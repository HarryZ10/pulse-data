#  Recidiviz - a data platform for criminal justice reform
#  Copyright (C) 2021 Recidiviz, Inc.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  =============================================================================
"""Count of supervisees with their contact needs met by PO by day"""
# pylint: disable=line-too-long

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state import (
    dataset_config,
    state_specific_query_strings,
)
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

TIMELY_CONTACT_BY_PO_BY_DAY_VIEW_NAME = "timely_contact_by_po_by_day"

TIMELY_CONTACT_BY_PO_BY_DAY_DESCRIPTION = """
    Number of supervisees who have their contact requirements filled by PO by day
 """

TIMELY_CONTACT_BY_PO_BY_DAY_QUERY_TEMPLATE = """
    /*{description}*/
WITH overdue_contacts AS (
    SELECT
        compliance.state_code,
        compliance.date_of_supervision,
        supervising_officer_external_id,
        IFNULL(level_1_supervision_location_external_id, 'UNKNOWN') as level_1_supervision_location_external_id,
        IFNULL(level_2_supervision_location_external_id, 'UNKNOWN') as level_2_supervision_location_external_id,
        COUNT (DISTINCT(
            # Only supervisees on MINIMUM, MEDIUM, or MAXIMUM supervision have a contact requirement.
            IF(supervision_level IN ('MINIMUM', 'MEDIUM', 'MAXIMUM') AND NOT face_to_face_frequency_sufficient,
                person_id,
                NULL))) as total_overdue,
    FROM `{project_id}.{materialized_metrics_dataset}.most_recent_supervision_case_compliance_metrics_materialized` compliance,
    UNNEST ([compliance.level_1_supervision_location_external_id, 'ALL']) AS level_1_supervision_location_external_id,
    UNNEST ([compliance.level_2_supervision_location_external_id, 'ALL']) AS level_2_supervision_location_external_id,
    UNNEST ([supervising_officer_external_id, 'ALL']) AS supervising_officer_external_id
    WHERE state_code = 'US_ND'
        AND level_2_supervision_location_external_id IS NOT NULL
        AND date_of_supervision > DATE_SUB(CURRENT_DATE('US/Pacific'), INTERVAL 211 DAY)
    GROUP BY state_code, date_of_supervision, supervising_officer_external_id, level_1_supervision_location_external_id, level_2_supervision_location_external_id
    )

    SELECT
        overdue_contacts.state_code,
        overdue_contacts.date_of_supervision,
        IFNULL(overdue_contacts.supervising_officer_external_id, 'UNKNOWN') as supervising_officer_external_id,
        {vitals_state_specific_district_id},
        {vitals_state_specific_district_name},
        total_overdue,
        sup_pop.supervisees_requiring_contact AS supervisees_requiring_contact,
        IFNULL(SAFE_DIVIDE((sup_pop.supervisees_requiring_contact - total_overdue), sup_pop.supervisees_requiring_contact), 1) * 100 AS timely_contact,
    FROM overdue_contacts
    LEFT JOIN `{project_id}.{reference_views_dataset}.supervision_location_ids_to_names` locations
        ON overdue_contacts.state_code = locations.state_code
        AND {vitals_state_specific_join_with_supervision_location_ids}
    LEFT JOIN `{project_id}.{vitals_views_dataset}.supervision_population_by_po_by_day_materialized` sup_pop
        ON sup_pop.state_code = overdue_contacts.state_code
        AND sup_pop.date_of_supervision = overdue_contacts.date_of_supervision
        AND sup_pop.supervising_officer_external_id = overdue_contacts.supervising_officer_external_id
        AND {vitals_state_specific_join_with_supervision_population}
    """

TIMELY_CONTACT_BY_PO_BY_DAY_VIEW_BUILDER = SimpleBigQueryViewBuilder(
    dataset_id=dataset_config.VITALS_REPORT_DATASET,
    view_id=TIMELY_CONTACT_BY_PO_BY_DAY_VIEW_NAME,
    view_query_template=TIMELY_CONTACT_BY_PO_BY_DAY_QUERY_TEMPLATE,
    description=TIMELY_CONTACT_BY_PO_BY_DAY_DESCRIPTION,
    materialized_metrics_dataset=dataset_config.DATAFLOW_METRICS_MATERIALIZED_DATASET,
    reference_views_dataset=dataset_config.REFERENCE_VIEWS_DATASET,
    vitals_views_dataset=dataset_config.VITALS_REPORT_DATASET,
    vitals_state_specific_district_id=state_specific_query_strings.vitals_state_specific_district_id(
        "overdue_contacts"
    ),
    vitals_state_specific_district_name=state_specific_query_strings.vitals_state_specific_district_name(
        "overdue_contacts"
    ),
    vitals_state_specific_join_with_supervision_location_ids=state_specific_query_strings.vitals_state_specific_join_with_supervision_location_ids(
        "overdue_contacts"
    ),
    vitals_state_specific_join_with_supervision_population=state_specific_query_strings.vitals_state_specific_join_with_supervision_population(
        "overdue_contacts"
    ),
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        TIMELY_CONTACT_BY_PO_BY_DAY_VIEW_BUILDER.build_and_print()