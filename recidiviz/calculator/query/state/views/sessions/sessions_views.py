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
"""All views needed for sessions"""
from typing import List

from recidiviz.big_query.big_query_view import SimpleBigQueryViewBuilder
from recidiviz.calculator.query.state.views.sessions.admission_start_reason_dedup_priority import (
    ADMISSION_START_REASON_DEDUP_PRIORITY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.assessment_lsir_responses import (
    ASSESSMENT_LSIR_RESPONSES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.assessment_lsir_scoring_key import (
    ASSESSMENT_LSIR_SCORING_KEY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.assessment_score_sessions import (
    ASSESSMENT_SCORE_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.cohort_month_index import (
    COHORT_MONTH_INDEX_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_level_0_super_sessions import (
    COMPARTMENT_LEVEL_0_SUPER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_level_1_super_sessions import (
    COMPARTMENT_LEVEL_1_SUPER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_level_2_dedup_priority import (
    COMPARTMENT_LEVEL_2_DEDUP_PRIORITY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_level_2_super_sessions import (
    COMPARTMENT_LEVEL_2_SUPER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_sentences import (
    COMPARTMENT_SENTENCES_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_session_end_reasons import (
    COMPARTMENT_SESSION_END_REASONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_session_start_reasons import (
    COMPARTMENT_SESSION_START_REASONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_sessions import (
    COMPARTMENT_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.compartment_sessions_unnested import (
    COMPARTMENT_SESSIONS_UNNESTED_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.dataflow_sessions import (
    DATAFLOW_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.incarceration_super_sessions import (
    INCARCERATION_SUPER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.location_sessions import (
    LOCATION_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.person_demographics import (
    PERSON_DEMOGRAPHICS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.reincarceration_cohort_sessions import (
    REINCARCERATION_COHORT_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.reincarceration_sessions_from_dataflow import (
    REINCARCERATION_SESSIONS_FROM_DATAFLOW_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.reincarceration_sessions_from_sessions import (
    REINCARCERATION_SESSIONS_FROM_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.release_termination_reason_dedup_priority import (
    RELEASE_TERMINATION_REASON_DEDUP_PRIORITY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.revocation_cohort_sessions import (
    REVOCATION_COHORT_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.revocation_sessions import (
    REVOCATION_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.supervision_level_dedup_priority import (
    SUPERVISION_LEVEL_DEDUP_PRIORITY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.supervision_level_sessions import (
    SUPERVISION_LEVEL_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.supervision_officer_sessions import (
    SUPERVISION_OFFICER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.supervision_super_sessions import (
    SUPERVISION_SUPER_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.system_sessions import (
    SYSTEM_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_employment_sessions import (
    US_ID_EMPLOYMENT_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_incarceration_population_metrics_preprocessed import (
    US_ID_INCARCERATION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_positive_urine_analysis_sessions import (
    US_ID_POSITIVE_URINE_ANALYSIS_SESSIONS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_raw_lsir_assessments import (
    US_ID_RAW_LSIR_ASSESSMENTS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_supervision_out_of_state_population_metrics_preprocessed import (
    US_ID_SUPERVISION_OUT_OF_STATE_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_id.us_id_supervision_population_metrics_preprocessed import (
    US_ID_SUPERVISION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_mo.us_mo_supervision_population_metrics_preprocessed import (
    US_MO_SUPERVISION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.us_nd.us_nd_raw_lsir_assessments import (
    US_ND_RAW_LSIR_ASSESSMENTS_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.violation_type_dedup_priority import (
    VIOLATION_TYPE_DEDUP_PRIORITY_VIEW_BUILDER,
)
from recidiviz.calculator.query.state.views.sessions.violations_sessions import (
    VIOLATIONS_SESSIONS_VIEW_BUILDER,
)

SESSIONS_VIEW_BUILDERS: List[SimpleBigQueryViewBuilder] = [
    ASSESSMENT_SCORE_SESSIONS_VIEW_BUILDER,
    COMPARTMENT_LEVEL_2_DEDUP_PRIORITY_VIEW_BUILDER,
    ADMISSION_START_REASON_DEDUP_PRIORITY_VIEW_BUILDER,
    RELEASE_TERMINATION_REASON_DEDUP_PRIORITY_VIEW_BUILDER,
    COMPARTMENT_SESSION_START_REASONS_VIEW_BUILDER,
    COMPARTMENT_SESSION_END_REASONS_VIEW_BUILDER,
    COMPARTMENT_SESSIONS_VIEW_BUILDER,
    SUPERVISION_SUPER_SESSIONS_VIEW_BUILDER,
    REVOCATION_SESSIONS_VIEW_BUILDER,
    REINCARCERATION_SESSIONS_FROM_DATAFLOW_VIEW_BUILDER,
    REINCARCERATION_SESSIONS_FROM_SESSIONS_VIEW_BUILDER,
    SYSTEM_SESSIONS_VIEW_BUILDER,
    COMPARTMENT_SESSIONS_UNNESTED_VIEW_BUILDER,
    COMPARTMENT_SENTENCES_VIEW_BUILDER,
    VIOLATIONS_SESSIONS_VIEW_BUILDER,
    VIOLATION_TYPE_DEDUP_PRIORITY_VIEW_BUILDER,
    DATAFLOW_SESSIONS_VIEW_BUILDER,
    SUPERVISION_LEVEL_SESSIONS_VIEW_BUILDER,
    SUPERVISION_LEVEL_DEDUP_PRIORITY_VIEW_BUILDER,
    SUPERVISION_OFFICER_SESSIONS_VIEW_BUILDER,
    LOCATION_SESSIONS_VIEW_BUILDER,
    US_ID_EMPLOYMENT_SESSIONS_VIEW_BUILDER,
    US_ID_POSITIVE_URINE_ANALYSIS_SESSIONS_VIEW_BUILDER,
    US_ID_SUPERVISION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
    US_ID_SUPERVISION_OUT_OF_STATE_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
    US_ID_INCARCERATION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
    INCARCERATION_SUPER_SESSIONS_VIEW_BUILDER,
    US_MO_SUPERVISION_POPULATION_METRICS_PREPROCESSED_VIEW_BUILDER,
    REVOCATION_COHORT_SESSIONS_VIEW_BUILDER,
    REINCARCERATION_COHORT_SESSIONS_VIEW_BUILDER,
    COMPARTMENT_LEVEL_1_SUPER_SESSIONS_VIEW_BUILDER,
    COMPARTMENT_LEVEL_2_SUPER_SESSIONS_VIEW_BUILDER,
    COMPARTMENT_LEVEL_0_SUPER_SESSIONS_VIEW_BUILDER,
    COHORT_MONTH_INDEX_VIEW_BUILDER,
    PERSON_DEMOGRAPHICS_VIEW_BUILDER,
    US_ID_RAW_LSIR_ASSESSMENTS_VIEW_BUILDER,
    US_ND_RAW_LSIR_ASSESSMENTS_VIEW_BUILDER,
    ASSESSMENT_LSIR_RESPONSES_VIEW_BUILDER,
    ASSESSMENT_LSIR_SCORING_KEY_VIEW_BUILDER,
]