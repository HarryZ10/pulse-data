#  Recidiviz - a data platform for criminal justice reform
#  Copyright (C) 2022 Recidiviz, Inc.
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
"""Supervision to liberty population snapshot by dimension.

To generate the BQ view, run:
python -m recidiviz.calculator.query.state.views.dashboard.pathways.supervision_to_liberty_population_snapshot_by_dimension
"""
from recidiviz.calculator.query.bq_utils import (
    get_binned_time_period_months,
    length_of_stay_month_groups,
)
from recidiviz.calculator.query.state import (
    dataset_config,
    state_specific_query_strings,
)
from recidiviz.calculator.query.state.state_specific_query_strings import (
    get_pathways_supervision_last_updated_date,
)
from recidiviz.calculator.query.state.views.dashboard.pathways.pathways_metric_big_query_view import (
    PathwaysMetricBigQueryViewBuilder,
)
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_VIEW_NAME = (
    "supervision_to_liberty_population_snapshot_by_dimension"
)

SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_DESCRIPTION = (
    """Supervision to liberty population snapshot by dimension"""
)

SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_QUERY_TEMPLATE = """
    /*{description}*/
    WITH transitions AS (
        SELECT
            state_code,
            person_id,
            gender,
            age_group,
            supervision_type,
            IFNULL(supervision_level, "EXTERNAL_UNKNOWN") AS supervision_level,
            # TODO(#13552): Change to supervision_district once the FE can support it
            supervision_district AS district,
            race,
            {binned_time_periods} AS time_period,
            {length_of_stay_binned} AS length_of_stay,
        FROM (
            SELECT
                *,
                DATE_DIFF(transition_date, supervision_start_date, MONTH) AS length_of_stay_months,
            FROM `{project_id}.{dashboards_dataset}.supervision_to_liberty_transitions`
        )
        WHERE transition_date >= DATE_SUB(CURRENT_DATE('US/Eastern'), INTERVAL 60 MONTH)
    ),
    get_last_updated AS ({get_pathways_supervision_last_updated_date}),
    all_rows AS (
        SELECT
            transitions.state_code,
            get_last_updated.last_updated,
            time_period,
            gender,
            age_group,
            race,
            supervision_type,
            supervision_level,
            # TODO(#13552): Change to supervision_district once the FE can support it
            district,
            length_of_stay,
        FROM transitions
        LEFT JOIN get_last_updated USING (state_code)
       
    ),
    filtered_rows AS (
        SELECT * FROM all_rows
        WHERE {state_specific_district_filter}
    )
    
    SELECT 
        {dimensions_clause},
        last_updated,
        COUNT(1) AS event_count,
    FROM filtered_rows,
        UNNEST([gender, 'ALL']) AS gender,
        UNNEST([race, 'ALL']) AS race,
        UNNEST([age_group, 'ALL']) AS age_group,
        UNNEST([supervision_type, 'ALL']) AS supervision_type,
        UNNEST([supervision_level, 'ALL']) AS supervision_level,
        UNNEST([district, 'ALL']) AS district,
        UNNEST([length_of_stay, 'ALL']) AS length_of_stay
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
"""

SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_VIEW_BUILDER = PathwaysMetricBigQueryViewBuilder(
    dataset_id=dataset_config.DASHBOARD_VIEWS_DATASET,
    view_id=SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_VIEW_NAME,
    view_query_template=SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_QUERY_TEMPLATE,
    description=SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_DESCRIPTION,
    dimensions=(
        "state_code",
        "time_period",
        "gender",
        "age_group",
        "race",
        "supervision_type",
        "supervision_level",
        # TODO(#13552): Change to supervision_district once the FE can support it
        "district",
        "length_of_stay",
    ),
    dashboards_dataset=dataset_config.DASHBOARD_VIEWS_DATASET,
    binned_time_periods=get_binned_time_period_months("transition_date"),
    get_pathways_supervision_last_updated_date=get_pathways_supervision_last_updated_date(),
    length_of_stay_binned=length_of_stay_month_groups(),
    state_specific_district_filter=state_specific_query_strings.pathways_state_specific_supervision_district_filter(),
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        SUPERVISION_TO_LIBERTY_POPULATION_SNAPSHOT_BY_DIMENSION_VIEW_BUILDER.build_and_print()
