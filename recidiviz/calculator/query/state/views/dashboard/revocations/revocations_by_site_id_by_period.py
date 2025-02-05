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
"""Revocations by site_id by metric period months."""

from recidiviz.calculator.query import bq_utils
from recidiviz.calculator.query.state import dataset_config
from recidiviz.metrics.metric_big_query_view import MetricBigQueryViewBuilder
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

REVOCATIONS_BY_SITE_ID_BY_PERIOD_VIEW_NAME = "revocations_by_site_id_by_period"

REVOCATIONS_BY_SITE_ID_BY_PERIOD_DESCRIPTION = """
 Revocations by site_id by metric period months.
 This counts all individuals admitted to prison for a revocation of supervision, broken
 down by the site_id of the district in which the person was supervised prior to the
 revocation admission, and by the violation type of the supervision violation.
 """

REVOCATIONS_BY_SITE_ID_BY_PERIOD_QUERY_TEMPLATE = """
    /*{description}*/
    SELECT
      state_code,
      IFNULL(felony_count, 0) AS felony_count,
      IFNULL(absconsion_count, 0) AS absconsion_count,
      IFNULL(technical_count, 0) AS technical_count,
      IFNULL(SAFE_SUBTRACT(all_violation_types_count, (felony_count + technical_count + absconsion_count)), 0) as unknown_count,
      total_supervision_count,
      supervision_type,
      district,
      metric_period_months
    FROM (
      SELECT
        state_code,
        COUNT(DISTINCT person_id) AS total_supervision_count,
        supervision_type,
        district,
        metric_period_months
      FROM `{project_id}.{shared_metric_views_dataset}.event_based_supervision_populations_with_commitments_for_rate_denominators`,
      {metric_period_dimension}
      WHERE {metric_period_condition}
      GROUP BY state_code, supervision_type, district, metric_period_months
    ) pop
    LEFT JOIN (
      SELECT
        state_code,
        supervision_type,
        COUNT(DISTINCT IF(most_severe_violation_type IN ('FELONY', 'MISDEMEANOR', 'LAW'), person_id, NULL)) AS felony_count,
        COUNT(DISTINCT IF(most_severe_violation_type = 'TECHNICAL', person_id, NULL)) AS technical_count,
        COUNT(DISTINCT IF(most_severe_violation_type IN ('ESCAPED', 'ABSCONDED'), person_id, NULL)) AS absconsion_count,
        COUNT(DISTINCT person_id) AS all_violation_types_count,
        district,
        metric_period_months
      FROM (
        SELECT
          state_code, metric_period_months,
          person_id, most_severe_violation_type,
          supervision_type, district,
          -- Only use most recent revocation per person/supervision_type/metric_period_months
          ROW_NUMBER() OVER (PARTITION BY state_code, person_id, supervision_type, metric_period_months, district
                             ORDER BY admission_date DESC) AS revocation_rank
        FROM `{project_id}.{shared_metric_views_dataset}.event_based_commitments_from_supervision_materialized`,
        {metric_period_dimension}
        WHERE {metric_period_condition}
      )
      WHERE revocation_rank = 1
      GROUP BY state_code, supervision_type, district, metric_period_months
    ) rev
    USING (state_code, supervision_type, district, metric_period_months)
    WHERE supervision_type in ('ALL', 'PAROLE', 'PROBATION')
    ORDER BY state_code, district, supervision_type, metric_period_months
    """

REVOCATIONS_BY_SITE_ID_BY_PERIOD_VIEW_BUILDER = MetricBigQueryViewBuilder(
    dataset_id=dataset_config.DASHBOARD_VIEWS_DATASET,
    view_id=REVOCATIONS_BY_SITE_ID_BY_PERIOD_VIEW_NAME,
    view_query_template=REVOCATIONS_BY_SITE_ID_BY_PERIOD_QUERY_TEMPLATE,
    dimensions=("state_code", "metric_period_months", "supervision_type", "district"),
    description=REVOCATIONS_BY_SITE_ID_BY_PERIOD_DESCRIPTION,
    shared_metric_views_dataset=dataset_config.SHARED_METRIC_VIEWS_DATASET,
    metric_period_dimension=bq_utils.unnest_metric_period_months(),
    metric_period_condition=bq_utils.metric_period_condition(),
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        REVOCATIONS_BY_SITE_ID_BY_PERIOD_VIEW_BUILDER.build_and_print()
