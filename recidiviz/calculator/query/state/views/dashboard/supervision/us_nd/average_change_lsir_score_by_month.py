# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2019 Recidiviz, Inc.
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
"""
The average change in LSIR score by month of scheduled supervision termination.
Per ND-specific request, compares the LSIR score at termination to the second
LSIR score of the person's supervision.
"""

from recidiviz.calculator.query import bq_utils
from recidiviz.calculator.query.state import dataset_config
from recidiviz.metrics.metric_big_query_view import MetricBigQueryViewBuilder
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

AVERAGE_CHANGE_LSIR_SCORE_MONTH_VIEW_NAME = "average_change_lsir_score_by_month"

AVERAGE_CHANGE_LSIR_SCORE_MONTH_DESCRIPTION = """
The average change in LSIR score by month of scheduled supervision 
termination. Per ND-request, compares the LSIR score at termination to the 
second LSIR score of the person's supervision.
"""

AVERAGE_CHANGE_LSIR_SCORE_MONTH_QUERY_TEMPLATE = """
    /*{description}*/
    SELECT
      state_code, termination_year, termination_month,
      ROUND(IFNULL(AVG(assessment_score_change), 0), 2) AS average_change,
      supervision_type,
      IFNULL(district, 'EXTERNAL_UNKNOWN') as district
    FROM (
      SELECT
        state_code, year as termination_year, month as termination_month,
        assessment_score_change,
        supervision_type,
        district,
        -- Use the most recent termination per person/year/month/supervision/district
        ROW_NUMBER() OVER (PARTITION BY state_code, year, month, supervision_type, district, person_id
                           ORDER BY termination_date DESC, assessment_score_change) AS supervision_rank
      FROM `{project_id}.{materialized_metrics_dataset}.most_recent_supervision_termination_metrics_materialized`,
      {district_dimension},
      {supervision_type_dimension}
      WHERE assessment_type = 'LSIR'
        AND assessment_score_change IS NOT NULL
        AND {thirty_six_month_filter}
    )
    WHERE supervision_type IN ('ALL', 'PAROLE', 'PROBATION')
      AND supervision_rank = 1
    GROUP BY state_code, termination_year, termination_month, supervision_type, district
    ORDER BY state_code, termination_year, termination_month, district, supervision_type
    """

AVERAGE_CHANGE_LSIR_SCORE_MONTH_VIEW_BUILDER = MetricBigQueryViewBuilder(
    dataset_id=dataset_config.DASHBOARD_VIEWS_DATASET,
    view_id=AVERAGE_CHANGE_LSIR_SCORE_MONTH_VIEW_NAME,
    view_query_template=AVERAGE_CHANGE_LSIR_SCORE_MONTH_QUERY_TEMPLATE,
    dimensions=(
        "state_code",
        "termination_year",
        "termination_month",
        "supervision_type",
        "district",
    ),
    description=AVERAGE_CHANGE_LSIR_SCORE_MONTH_DESCRIPTION,
    materialized_metrics_dataset=dataset_config.DATAFLOW_METRICS_MATERIALIZED_DATASET,
    district_dimension=bq_utils.unnest_district(),
    supervision_type_dimension=bq_utils.unnest_supervision_type(),
    thirty_six_month_filter=bq_utils.thirty_six_month_filter(),
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        AVERAGE_CHANGE_LSIR_SCORE_MONTH_VIEW_BUILDER.build_and_print()
