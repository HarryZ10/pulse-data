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
"""Utils for calculations regarding incarceration admissions that are commitments from
supervision."""
import datetime
from typing import Optional, List, Dict, Any, NamedTuple, Tuple

from dateutil.relativedelta import relativedelta

from recidiviz.calculator.pipeline.utils.state_utils.state_calculation_config_manager import (
    get_supervising_officer_and_location_info_from_supervision_period,
    state_specific_purpose_for_incarceration_and_subtype,
)
from recidiviz.calculator.pipeline.utils.supervision_period_utils import (
    identify_most_severe_case_type,
)
from recidiviz.calculator.pipeline.utils.violation_response_utils import (
    violation_responses_in_window,
)
from recidiviz.calculator.pipeline.utils.violation_utils import (
    VIOLATION_HISTORY_WINDOW_MONTHS,
)
from recidiviz.common.constants.state.state_case_type import StateSupervisionCaseType
from recidiviz.common.constants.state.state_incarceration_period import (
    StateSpecializedPurposeForIncarceration,
)
from recidiviz.common.constants.state.state_supervision_period import (
    StateSupervisionLevel,
)
from recidiviz.common.date import DateRange
from recidiviz.persistence.entity.state.entities import (
    StateIncarcerationPeriod,
    StateSupervisionPeriod,
    StateSupervisionViolationResponse,
)

CommitmentDetails = NamedTuple(
    "CommitmentDetails",
    [
        (
            "purpose_for_incarceration",
            Optional[StateSpecializedPurposeForIncarceration],
        ),
        ("purpose_for_incarceration_subtype", Optional[str]),
        ("supervising_officer_external_id", Optional[str]),
        ("level_1_supervision_location_external_id", Optional[str]),
        ("level_2_supervision_location_external_id", Optional[str]),
        ("case_type", Optional[StateSupervisionCaseType]),
        ("supervision_level", Optional[StateSupervisionLevel]),
        ("supervision_level_raw_text", Optional[str]),
    ],
)


def get_commitment_from_supervision_details(
    incarceration_period: StateIncarcerationPeriod,
    pre_commitment_supervision_period: Optional[StateSupervisionPeriod],
    violation_responses: List[StateSupervisionViolationResponse],
    supervision_period_to_agent_associations: Optional[Dict[int, Dict[Any, Any]]],
) -> CommitmentDetails:
    """Identifies various attributes of the commitment to incarceration from
    supervision.
    """
    supervising_officer_external_id = None
    level_1_supervision_location_external_id = None
    level_2_supervision_location_external_id = None

    if pre_commitment_supervision_period and supervision_period_to_agent_associations:
        (
            supervising_officer_external_id,
            level_1_supervision_location_external_id,
            level_2_supervision_location_external_id,
        ) = get_supervising_officer_and_location_info_from_supervision_period(
            pre_commitment_supervision_period, supervision_period_to_agent_associations
        )

    (
        purpose_for_incarceration,
        purpose_for_incarceration_subtype,
    ) = state_specific_purpose_for_incarceration_and_subtype(
        incarceration_period.state_code,
        incarceration_period,
        violation_responses,
        _identify_specialized_purpose_for_incarceration_and_subtype,
    )

    case_type = (
        identify_most_severe_case_type(pre_commitment_supervision_period)
        if pre_commitment_supervision_period
        else StateSupervisionCaseType.GENERAL
    )

    supervision_level = (
        pre_commitment_supervision_period.supervision_level
        if pre_commitment_supervision_period
        else None
    )

    supervision_level_raw_text = (
        pre_commitment_supervision_period.supervision_level_raw_text
        if pre_commitment_supervision_period
        else None
    )

    commitment_details_result = CommitmentDetails(
        purpose_for_incarceration=purpose_for_incarceration,
        purpose_for_incarceration_subtype=purpose_for_incarceration_subtype,
        supervising_officer_external_id=supervising_officer_external_id,
        level_1_supervision_location_external_id=level_1_supervision_location_external_id,
        level_2_supervision_location_external_id=level_2_supervision_location_external_id,
        case_type=case_type,
        supervision_level=supervision_level,
        supervision_level_raw_text=supervision_level_raw_text,
    )

    return commitment_details_result


def _identify_specialized_purpose_for_incarceration_and_subtype(
    incarceration_period: StateIncarcerationPeriod,
) -> Tuple[Optional[StateSpecializedPurposeForIncarceration], Optional[str]]:
    """Determines the specialized_purpose_for_incarceration and, if applicable, the
    specialized_purpose_for_incarceration_subtype of the commitment from supervision
    admission to the given incarceration_period."""
    specialized_purpose_for_incarceration = (
        incarceration_period.specialized_purpose_for_incarceration
        # Default to GENERAL if no specialized_purpose_for_incarceration is set
        or StateSpecializedPurposeForIncarceration.GENERAL
    )

    # For now, all non-state-specific specialized_purpose_for_incarceration_subtypes are
    # None
    return specialized_purpose_for_incarceration, None


def default_violation_history_window_pre_commitment_from_supervision(
    admission_date: datetime.date,
    sorted_and_filtered_violation_responses: List[StateSupervisionViolationResponse],
) -> DateRange:
    """Returns the window of time before a commitment from supervision in which we
    should consider violations for the violation history prior to the admission."""
    # We will use the date of the last response prior to the admission as the
    # window cutoff.
    responses_in_window = violation_responses_in_window(
        violation_responses=sorted_and_filtered_violation_responses,
        upper_bound_exclusive=admission_date + relativedelta(days=1),
        lower_bound_inclusive=None,
    )

    violation_history_end_date = admission_date

    if responses_in_window:
        # If there were violation responses leading up to the incarceration
        # admission, then we want the violation history leading up to the last
        # response_date instead of the admission_date on the
        # incarceration_period
        last_response = responses_in_window[-1]

        if not last_response.response_date:
            # This should never happen, but is here to silence mypy warnings
            # about empty response_dates.
            raise ValueError(
                "Not effectively filtering out responses without valid"
                " response_dates."
            )
        violation_history_end_date = last_response.response_date

    violation_window_lower_bound_inclusive = violation_history_end_date - relativedelta(
        months=VIOLATION_HISTORY_WINDOW_MONTHS
    )
    violation_window_upper_bound_exclusive = violation_history_end_date + relativedelta(
        days=1
    )

    return DateRange(
        lower_bound_inclusive_date=violation_window_lower_bound_inclusive,
        upper_bound_exclusive_date=violation_window_upper_bound_exclusive,
    )