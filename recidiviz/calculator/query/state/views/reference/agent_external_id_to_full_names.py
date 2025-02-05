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
"""Table for associating a unique agent external id to a full name for state agents with augmented information."""
from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state import dataset_config
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_NAME = "agent_external_id_to_full_name"

AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_DESCRIPTION = """Agent information table that adds links distinct external ids for state agents back to their full names"""

AGENT_EXTERNAL_ID_TO_FULL_NAMES_QUERY_TEMPLATE = """
    /*{description}*/
    WITH unique_agents AS (
        SELECT
            state_code,
            external_id,
            full_name,
            given_names,
            surname,
            ROW_NUMBER() OVER (PARTITION BY state_code, external_id ORDER BY surname NULLS LAST) as rn
        FROM `{project_id}.{reference_views_dataset}.augmented_agent_info`
    )
    
    SELECT
        * EXCEPT(rn),
        -- TODO(#8674): Remove the agent_external_id_with_full_name once the Lantern FE 
        -- is no longer relying on this value
        CONCAT(external_id, IFNULL(CONCAT(': ', NULLIF(TRIM(full_name), '')), '')) as agent_external_id_with_full_name
    FROM unique_agents
    WHERE rn=1
"""

AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_BUILDER = SimpleBigQueryViewBuilder(
    dataset_id=dataset_config.REFERENCE_VIEWS_DATASET,
    view_id=AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_NAME,
    view_query_template=AGENT_EXTERNAL_ID_TO_FULL_NAMES_QUERY_TEMPLATE,
    description=AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_DESCRIPTION,
    reference_views_dataset=dataset_config.REFERENCE_VIEWS_DATASET,
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        AGENT_EXTERNAL_ID_TO_FULL_NAMES_VIEW_BUILDER.build_and_print()
