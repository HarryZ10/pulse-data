# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2021 Recidiviz, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =============================================================================

"""Endpoints related to auth operations.
"""
import logging
import os
from http import HTTPStatus
from typing import Any, Dict, List, Mapping, Tuple, Union

import sqlalchemy.orm.exc
from flask import Blueprint, request
from sqlalchemy import func

from recidiviz.auth.auth0_client import CaseTriageAuth0AppMetadata
from recidiviz.calculator.query.state.views.reference.dashboard_user_restrictions import (
    DASHBOARD_USER_RESTRICTIONS_VIEW_BUILDER,
)
from recidiviz.case_triage.ops_routes import CASE_TRIAGE_DB_OPERATIONS_QUEUE
from recidiviz.cloud_sql.gcs_import_to_cloud_sql import import_gcs_csv_to_cloud_sql
from recidiviz.cloud_storage.gcsfs_path import GcsfsFilePath
from recidiviz.common.constants.states import StateCode
from recidiviz.common.google_cloud.cloud_task_queue_manager import (
    CloudTaskQueueInfo,
    CloudTaskQueueManager,
    get_cloud_task_json_body,
)
from recidiviz.metrics.export.export_config import (
    DASHBOARD_USER_RESTRICTIONS_OUTPUT_DIRECTORY_URI,
)
from recidiviz.persistence.database.schema.case_triage.schema import (
    DashboardUserRestrictions,
)
from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.persistence.database.sqlalchemy_database_key import SQLAlchemyDatabaseKey
from recidiviz.reporting.email_reporting_utils import validate_email_address
from recidiviz.utils import metadata
from recidiviz.utils.auth.gae import requires_gae_auth
from recidiviz.utils.params import get_only_str_param_value
from recidiviz.utils.pubsub_helper import OBJECT_ID, extract_pubsub_message_from_json
from recidiviz.utils.string import StrictStringFormatter

auth_endpoint_blueprint = Blueprint("auth_endpoint_blueprint", __name__)


@auth_endpoint_blueprint.route(
    "/handle_import_user_restrictions_csv_to_sql", methods=["POST"]
)
@requires_gae_auth
def handle_import_user_restrictions_csv_to_sql() -> Tuple[str, HTTPStatus]:
    """Called from a Cloud Storage Notification when a new file is created in the user restrictions
    bucket. It enqueues a task to import the file into Cloud SQL."""
    try:
        message = extract_pubsub_message_from_json(request.get_json())
    except Exception as e:
        return str(e), HTTPStatus.BAD_REQUEST

    if not message.attributes:
        return "Invalid Pub/Sub message", HTTPStatus.BAD_REQUEST

    attributes = message.attributes
    region_code, filename = os.path.split(attributes[OBJECT_ID])

    if not region_code:
        logging.info("Missing region, ignoring")
        return "", HTTPStatus.OK

    # It would be nice if we could do this as a filter in the GCS notification instead of as logic
    # here, but as of June 2022, the available filters are not expressive enough for our needs:
    # https://cloud.google.com/pubsub/docs/filtering#filtering_syntax
    if filename != "dashboard_user_restrictions.csv":
        logging.info("Unknown filename %s, ignoring", filename)
        return "", HTTPStatus.OK

    cloud_task_manager = CloudTaskQueueManager(
        queue_info_cls=CloudTaskQueueInfo, queue_name=CASE_TRIAGE_DB_OPERATIONS_QUEUE
    )
    cloud_task_manager.create_task(
        relative_uri="/auth/import_user_restrictions_csv_to_sql",
        body={"region_code": region_code},
    )
    logging.info(
        "Enqueued import_user_restrictions_csv_to_sql task to %s",
        CASE_TRIAGE_DB_OPERATIONS_QUEUE,
    )
    return "", HTTPStatus.OK


@auth_endpoint_blueprint.route(
    "/import_user_restrictions_csv_to_sql", methods=["GET", "POST"]
)
@requires_gae_auth
def import_user_restrictions_csv_to_sql() -> Tuple[str, HTTPStatus]:
    """This endpoint triggers the import of the user restrictions CSV file to Cloud SQL. It is requested by a Cloud
    Function that is triggered when a new file is created in the user restrictions bucket."""
    try:
        body = get_cloud_task_json_body()
        region_code = body.get("region_code")
        if not region_code:
            return "Missing region_code param", HTTPStatus.BAD_REQUEST

        try:
            _validate_region_code(region_code)
        except ValueError as error:
            logging.error(error)
            return str(error), HTTPStatus.BAD_REQUEST

        view_builder = DASHBOARD_USER_RESTRICTIONS_VIEW_BUILDER
        csv_path = GcsfsFilePath.from_absolute_path(
            os.path.join(
                StrictStringFormatter().format(
                    DASHBOARD_USER_RESTRICTIONS_OUTPUT_DIRECTORY_URI,
                    project_id=metadata.project_id(),
                ),
                region_code,
                f"{view_builder.view_id}.csv",
            )
        )

        import_gcs_csv_to_cloud_sql(
            database_key=SQLAlchemyDatabaseKey.for_schema(SchemaType.CASE_TRIAGE),
            model=DashboardUserRestrictions,
            gcs_uri=csv_path,
            columns=view_builder.columns,
            region_code=region_code.upper(),
        )
        logging.info(
            "CSV (%s) successfully imported to Cloud SQL schema %s for region code %s",
            csv_path.blob_name,
            SchemaType.CASE_TRIAGE,
            region_code,
        )

        return (
            f"CSV {csv_path.blob_name} successfully "
            f"imported to Cloud SQL schema {SchemaType.CASE_TRIAGE} for region code {region_code}",
            HTTPStatus.OK,
        )
    except Exception as error:
        logging.error(error)
        return (str(error), HTTPStatus.INTERNAL_SERVER_ERROR)


@auth_endpoint_blueprint.route("/dashboard_user_restrictions_by_email", methods=["GET"])
@requires_gae_auth
def dashboard_user_restrictions_by_email() -> Tuple[
    Union[CaseTriageAuth0AppMetadata, str], HTTPStatus
]:
    """This endpoint is accessed by a service account used by an Auth0 hook that is called at the pre-registration when
    a user first signs up for an account. Given a user email address in the request, it responds with
    the app_metadata that the hook will save on the user so that the UP dashboards can apply the appropriate
    restrictions.

    Query parameters:
        email_address: (required) The email address that requires a user restrictions lookup
        region_code: (required) The region code to use to lookup the user restrictions

    Returns:
         JSON response of the app_metadata associated with the given email address and an HTTP status

    Raises:
        Nothing. Catch everything so that we can always return a response to the request
    """
    email_address = get_only_str_param_value("email_address", request.args)
    region_code = get_only_str_param_value(
        "region_code", request.args, preserve_case=True
    )

    try:
        if not email_address:
            return "Missing email_address param", HTTPStatus.BAD_REQUEST
        if not region_code:
            return "Missing region_code param", HTTPStatus.BAD_REQUEST
        _validate_region_code(region_code)
        validate_email_address(email_address)
    except ValueError as error:
        logging.error(error)
        return str(error), HTTPStatus.BAD_REQUEST

    database_key = SQLAlchemyDatabaseKey.for_schema(schema_type=SchemaType.CASE_TRIAGE)
    # TODO(#8046): Don't use the deprecated session fetcher
    session = SessionFactory.deprecated__for_database(database_key=database_key)
    try:
        user_restrictions = (
            session.query(
                DashboardUserRestrictions.allowed_supervision_location_ids,
                DashboardUserRestrictions.allowed_supervision_location_level,
                DashboardUserRestrictions.can_access_leadership_dashboard,
                DashboardUserRestrictions.can_access_case_triage,
                DashboardUserRestrictions.should_see_beta_charts,
                DashboardUserRestrictions.routes,
                DashboardUserRestrictions.user_hash,
            )
            .filter(
                DashboardUserRestrictions.state_code == region_code.upper(),
                func.lower(DashboardUserRestrictions.restricted_user_email)
                == email_address.lower(),
            )
            .one()
        )

        restrictions = _format_db_results(user_restrictions)

        return (restrictions, HTTPStatus.OK)

    except sqlalchemy.orm.exc.NoResultFound:
        return (
            f"User not found for email address {email_address} and region code {region_code}.",
            HTTPStatus.NOT_FOUND,
        )

    except Exception as error:
        logging.error(error)
        return (
            f"An error occurred while fetching dashboard user restrictions with the email {email_address} for "
            f"region_code {region_code}: {error}",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    finally:
        session.close()


def _format_db_results(
    user_restrictions: Dict[str, Any],
) -> CaseTriageAuth0AppMetadata:
    return {
        "allowed_supervision_location_ids": _format_allowed_supervision_location_ids(
            user_restrictions["allowed_supervision_location_ids"]
        ),
        "allowed_supervision_location_level": user_restrictions[
            "allowed_supervision_location_level"
        ],
        "can_access_leadership_dashboard": user_restrictions[
            "can_access_leadership_dashboard"
        ],
        "can_access_case_triage": user_restrictions["can_access_case_triage"],
        "should_see_beta_charts": user_restrictions["should_see_beta_charts"],
        "routes": user_restrictions["routes"],
        "user_hash": user_restrictions["user_hash"],
    }


def _normalize_current_restrictions(
    current_app_metadata: Mapping[str, Any],
) -> Mapping[str, Any]:
    return {
        "allowed_supervision_location_ids": current_app_metadata.get(
            "allowed_supervision_location_ids", []
        ),
        "allowed_supervision_location_level": current_app_metadata.get(
            "allowed_supervision_location_level", None
        ),
        "can_access_leadership_dashboard": current_app_metadata.get(
            "can_access_leadership_dashboard", False
        ),
        "can_access_case_triage": current_app_metadata.get(
            "can_access_case_triage", False
        ),
        "should_see_beta_charts": current_app_metadata.get(
            "should_see_beta_charts", False
        ),
        "routes": current_app_metadata.get("routes", {}),
        "user_hash": current_app_metadata.get("user_hash"),
    }


def _format_allowed_supervision_location_ids(
    allowed_supervision_location_ids: str,
) -> List[str]:
    if not allowed_supervision_location_ids:
        return []
    return [
        restriction.strip()
        for restriction in allowed_supervision_location_ids.split(",")
        if restriction.strip()
    ]


def _validate_region_code(region_code: str) -> None:
    if not StateCode.is_state_code(region_code.upper()):
        raise ValueError(
            f"Unknown region_code [{region_code}] received, must be a valid state code."
        )
