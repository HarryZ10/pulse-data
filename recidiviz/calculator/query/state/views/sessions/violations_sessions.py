# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2020 Recidiviz, Inc.
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
"""Sessionized view of violations data - joins violations reports to sessions view
to allow analysis of violations that are associated with a given compartment"""
# pylint: disable=line-too-long
from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state import dataset_config
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override

VIOLATIONS_SESSIONS_VIEW_NAME = "violations_sessions"

us_nd_raw_data_up_to_date_views = "us_nd_raw_data_up_to_date_views"

VIOLATIONS_SESSIONS_VIEW_DESCRIPTION = """

## Overview

The table `violations_sessions_materialized` joins to sessions based on `person_id` and `session_id` and is used to associate a supervision violation with a given stay within a compartment. 

Each row in `violations_sessions_materialized` is a single violation on a given day. In the raw data, a single `violation_id` can have multiple violation types. A `violation_id` may also have multiple `violation_response_ids`, and each `response_id` may have multiple decisions made by the PO. We de-duplicate this by selecting the most serious violation type given a state-specific logic, and within the most serious violation type we prioritize keeping the most restrictive response_decision (such as REVOCATION over WARNING). We do keep a count of distinct `violation_id` per day in the `distinct_violations_per_day` field.

Each violation is associated with a `session_id` based on the `response_date` of the violation. Each violation is also associated with a supervision super-session - these group together continuous stays on supervision, in cases where an individual may go on `PAROLE_BOARD_HOLD`, `SHOCK_INCARCERATION`, or other temporary stays and back to supervision before being revoked. 

Finally, `revocation_sessions` are associated with violations by associating a revocation_session with the most severe violation type in a look-back window of 12 months. 

**Note: several revocation_sessions are not mapped onto violation_sessions and therefore `violation_sessions_materialized` should NOT be used to calculate total revocations**. Rather, revocation_session_id in the `violation_sessions_materialized` table can be useful for answering questions such as “What percentage of felony violations resulted in a revocation?”

## Field Definitions

|	Field	|	Description	|
|	--------------------	|	--------------------	|
|	person_id	|	Unique person identifier	|
|	state_code	|	State	|
|	supervision_violation_id	|	Unique identifier for a given violation	|
|	most_serious_violation_type	|	The most serious violation type for a given person on a given day. Determined using state specific logic	|
|	most_serious_violation_sub_type	|	The most serious violation sub type for a given person on a given day. Determined using state specific logic	|
|	most_severe_response_decision	|	The most severe recommendation from a PO for the most severe violation type for a given person/day	|
|	session_id	|	Session id	|
|	response_date	|	Date the violation was recorded	|
|	distinct_violations_per_day	|	A given person-day can have multiple distinct violation IDs. While we keep the most severe violation type on a given day, we keep track of the distinct violation IDs on a person-day.	|
|	is_violent	|	A flag for whether a violation involved a violent action - only available in some states	|
|	is_sex_offense	|	A flag for whether a violation involved a sex offense - only available in some states	|
|	supervision_super_session_id	|	An ID that groups together continuous stays on supervision, in cases where an individual may go on PAROLE_BOARD_HOLD and back to Parole several times before being revoked.	|
|	revocation_session_id	|	The session ID when an individual returns to incarceration. Can be used to join back onto `revocation_sessions_materialized` but cannot be used to count total revocations	|
|	revocation_date	|	Date of revocation if there is a revocation associated with that violation	|

## Methodology

Takes the output of the dataflow violations pipeline and integrates it with other sessions views including `compartment_sessions`, `revocation_sessions`, and `supervision_super_sessions`. This view also deduplicates to one violation per person per day by doing the following:

1. keeping the most severe violation type for a given `person_id`, `violation_id`
2. keeping the most severe violation type across all `violation_id`s for a given `person_id` and `response_date`
3. keeping the most severe response decision across all `violation_id`s for a given `person_id` and `response_date` if they have the same `most_severe_violation_type` and `most_severe_violation_type_subtype`
"""

VIOLATIONS_SESSIONS_QUERY_TEMPLATE = """
    /*{description}*/
    WITH violations_cte AS (
        SELECT 
        violations.state_code,
        violations.person_id,
        violations.supervision_violation_id,
        violations.violation_type as most_serious_violation_type,
        violations.violation_type_subtype as most_serious_violation_sub_type,
        violations.response_date,
        violations.most_severe_response_decision,
        violations.is_violent,
        violations.is_sex_offense,
        priority,  
        COUNT(DISTINCT  supervision_violation_id) OVER(PARTITION BY person_id, state_code, response_date) AS distinct_violations_per_day,
        ROW_NUMBER() OVER(PARTITION BY person_id, state_code, response_date ORDER BY 
        CASE WHEN is_most_severe_violation_type_of_all_violations = TRUE THEN 0 ELSE 1 END,
        CASE WHEN is_most_severe_response_decision_of_all_violations = TRUE THEN 0 ELSE 1 END) AS rn
        FROM `{project_id}.{dataflow_dataset}.most_recent_violation_with_response_metrics_materialized` violations
        LEFT JOIN `{project_id}.{sessions_dataset}.violation_type_dedup_priority`
                USING(state_code, violation_type, violation_type_subtype)
        /* This keeps most severe violation type associated with a given supervision_violation_id. There may still be 
        multiple supervision_violation_id's on the same response_date, so there are duplicates on person_id, 
        response_date after this step which are dealt with above in the ordering logic */ 
        WHERE is_most_severe_violation_type
        QUALIFY rn = 1
    ),
    us_nd_contacts_violations as (
        SELECT
            person_id,
            'US_ND' AS state_code,
            EXTRACT(date FROM PARSE_TIMESTAMP('%m/%d/%Y %I:%M:%S%p',CONTACT_DATE) ) AS response_date_ND
        FROM
            `{project_id}.us_nd_raw_data_up_to_date_views.docstars_contacts_latest`
        LEFT JOIN
            `{project_id}.{state_dataset}.state_person_external_id`
            ON
            SID = external_id
            AND state_code = "US_ND"
            AND id_type = 'US_ND_SID'
        WHERE
            CONTACT_CODE = 'VI'
            OR C2 = 'VI'
            OR C3 = 'VI'
            OR C4 = 'VI'
            OR C5 = 'VI'
            OR C6 = 'VI'
    ), 
    violations_combine AS (
        SELECT * EXCEPT(response_date, response_date_ND), 
        COALESCE(response_date_ND,response_date) AS response_date
        FROM violations_cte 
        FULL OUTER JOIN us_nd_contacts_violations USING(person_id,state_code)
    ),
    violations_sessions_info AS (
        SELECT violations.*,
        COALESCE(sessions.session_id,1) as session_id,
        /* Where the same violation is associated with multiple revocations, choose the earliest revocation date */
        ROW_NUMBER() OVER(PARTITION BY violations.person_id, violations.response_date 
            ORDER BY revocations.revocation_date ASC) as same_violation_multiple_revocations_rn,
        super_sessions.supervision_super_session_id,
        /* Where the same revocation is associated with multiple violations, choose the most severe of the violations
        and then choose the most recent violation if the severity is the same */
        CASE WHEN ROW_NUMBER() OVER(PARTITION BY violations.person_id, revocations.revocation_session_id 
            ORDER BY CASE WHEN priority IS null THEN 1 ELSE 0 END, priority ASC, response_date DESC) = 1 THEN revocation_session_id END AS revocation_session_id,
        CASE WHEN ROW_NUMBER() OVER(PARTITION BY violations.person_id, revocations.revocation_session_id 
            ORDER BY CASE WHEN priority IS null THEN 1 ELSE 0 END, priority ASC, response_date DESC) = 1 THEN revocation_date END AS revocation_date
        FROM violations_combine violations
        /* left join because there is a very small number of observations that dont get a session_id - if the violation
        is recorded before they show up in population metrics and therefore in sessions */
        LEFT JOIN `{project_id}.{sessions_dataset}.compartment_sessions_materialized` sessions
            ON sessions.person_id = violations.person_id
            AND violations.response_date BETWEEN sessions.start_date AND COALESCE(sessions.end_date, '9999-01-01')
        LEFT JOIN `{project_id}.{sessions_dataset}.supervision_super_sessions_materialized` super_sessions
            ON sessions.person_id = super_sessions.person_id
            AND sessions.session_id BETWEEN super_sessions.session_id_start AND super_sessions.session_id_end
        LEFT JOIN `{project_id}.{sessions_dataset}.revocation_sessions_materialized` revocations
            ON revocations.person_id = violations.person_id
            AND revocations.revocation_date BETWEEN violations.response_date AND DATE_ADD(violations.response_date, INTERVAL 365 DAY)        
    )   
    SELECT * EXCEPT(same_violation_multiple_revocations_rn, priority)
    FROM violations_sessions_info 
    WHERE same_violation_multiple_revocations_rn = 1
    """

VIOLATIONS_SESSIONS_VIEW_BUILDER = SimpleBigQueryViewBuilder(
    dataset_id=dataset_config.SESSIONS_DATASET,
    view_id=VIOLATIONS_SESSIONS_VIEW_NAME,
    view_query_template=VIOLATIONS_SESSIONS_QUERY_TEMPLATE,
    description=VIOLATIONS_SESSIONS_VIEW_DESCRIPTION,
    sessions_dataset=dataset_config.SESSIONS_DATASET,
    dataflow_dataset=dataset_config.DATAFLOW_METRICS_MATERIALIZED_DATASET,
    state_dataset=dataset_config.STATE_BASE_DATASET,
    should_materialize=True,
)

if __name__ == "__main__":
    with local_project_id_override(GCP_PROJECT_STAGING):
        VIOLATIONS_SESSIONS_VIEW_BUILDER.build_and_print()