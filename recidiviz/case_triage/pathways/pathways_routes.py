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
"""Implements routes for the Pathways Flask blueprint. """
import re
from collections import defaultdict
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import werkzeug.wrappers
from flask import Blueprint, Response, jsonify, make_response, request
from werkzeug.http import parse_set_header

from recidiviz.case_triage.api_schemas import load_api_schema
from recidiviz.case_triage.pathways.metric_fetcher import PathwaysMetricFetcher
from recidiviz.case_triage.pathways.metrics import ENABLED_METRICS_BY_STATE_BY_NAME
from recidiviz.case_triage.pathways.pathways_api_schemas import (
    FETCH_METRIC_SCHEMAS_BY_NAME,
)
from recidiviz.case_triage.pathways.pathways_authorization import (
    build_authorization_handler,
)
from recidiviz.common.constants.states import StateCode
from recidiviz.common.str_field_utils import snake_to_camel
from recidiviz.utils.flask_exception import FlaskException

PATHWAYS_ALLOWED_ORIGINS = [
    r"http\://localhost:3000",
    r"https\://dashboard-staging\.recidiviz\.org$",
    r"https\://dashboard\.recidiviz\.org$",
    r"https\://recidiviz-dashboard-stag-e1108--[^.]+?\.web\.app$",
]
FILTER_STRING_PATTERN = r"filters\[(\w+)\]"


def match_filter_string(value: str) -> Optional[str]:
    match_result = re.match(FILTER_STRING_PATTERN, value)

    if match_result:
        return match_result.group(1)

    return None


def load_filters_from_query_string() -> Dict[str, List[str]]:
    filters: Dict[str, List[str]] = defaultdict(list)

    for key, values in request.args.to_dict(flat=False).items():
        filter_dimension = match_filter_string(key)

        if filter_dimension:
            filters[filter_dimension] = [*filters[filter_dimension], *values]

    return filters


def create_pathways_api_blueprint() -> Blueprint:
    """Creates the API blueprint for Pathways"""
    api = Blueprint("pathways", __name__)

    handle_authorization = build_authorization_handler()

    @api.before_request
    def validate_authentication() -> None:
        # OPTIONS requests do not require authentication
        if request.method != "OPTIONS":
            handle_authorization()

    @api.before_request
    def validate_cors() -> Optional[Response]:
        origin_is_allowed = any(
            re.match(allowed_origin, request.origin)
            for allowed_origin in PATHWAYS_ALLOWED_ORIGINS
        )

        if not origin_is_allowed:
            response = make_response()
            response.status_code = HTTPStatus.FORBIDDEN
            return response

        return None

    @api.after_request
    def add_cors_headers(
        response: werkzeug.wrappers.Response,
    ) -> werkzeug.wrappers.Response:
        # Don't cache access control headers across origins
        response.vary = "Origin"
        response.access_control_allow_origin = request.origin
        response.access_control_allow_headers = parse_set_header(
            "authorization, sentry-trace"
        )
        # Cache preflight responses for 2 hours
        response.access_control_max_age = 2 * 60 * 60
        return response

    @api.get("/<state>/<metric_name>")
    def metrics(state: str, metric_name: str) -> Response:
        state_code = StateCode(state)

        try:
            metric_mapper = ENABLED_METRICS_BY_STATE_BY_NAME[state_code][metric_name]
        except KeyError as e:
            raise FlaskException(
                code="metric_not_enabled",
                description=f"{metric_name} is not enabled for {state_code.value}",
                status_code=HTTPStatus.BAD_REQUEST,
            ) from e

        source_data: Dict[str, Any] = {
            "filters": load_filters_from_query_string(),
        }
        for arg in ["group", "since"]:
            arg_value = request.args.get(arg)
            if arg_value:
                source_data[arg] = arg_value

        fetch_metric_params_schema = load_api_schema(
            FETCH_METRIC_SCHEMAS_BY_NAME[metric_name],
            source_data=source_data,
        )
        fetch_metric_params = metric_mapper.build_params(fetch_metric_params_schema)

        return jsonify(
            [
                {snake_to_camel(k): v for (k, v) in val.items()}
                for val in PathwaysMetricFetcher(state_code).fetch(
                    metric_mapper, fetch_metric_params
                )
            ]
        )

    return api
