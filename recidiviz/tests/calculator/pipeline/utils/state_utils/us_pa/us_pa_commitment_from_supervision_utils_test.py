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
"""Tests the functions in us_pa_commitment_from_supervision_utils.py"""

import unittest
from datetime import date

from recidiviz.calculator.pipeline.utils.state_utils.us_pa import (
    us_pa_commitment_from_supervision_utils,
)
from recidiviz.calculator.pipeline.utils.state_utils.us_pa.us_pa_commitment_from_supervision_utils import (
    PURPOSE_FOR_INCARCERATION_PVC,
    SHOCK_INCARCERATION_UNDER_6_MONTHS,
    SHOCK_INCARCERATION_12_MONTHS,
    SHOCK_INCARCERATION_9_MONTHS,
    SHOCK_INCARCERATION_6_MONTHS,
    SHOCK_INCARCERATION_PVC,
)
from recidiviz.common.constants.state.state_incarceration import StateIncarcerationType
from recidiviz.common.constants.state.state_incarceration_period import (
    StateIncarcerationPeriodAdmissionReason,
    StateIncarcerationPeriodStatus,
    StateSpecializedPurposeForIncarceration,
    StateIncarcerationPeriodReleaseReason,
)
from recidiviz.common.constants.state.state_supervision_period import (
    StateSupervisionPeriodSupervisionType,
    StateSupervisionPeriodStatus,
)
from recidiviz.common.constants.state.state_supervision_violation_response import (
    StateSupervisionViolationResponseRevocationType,
    StateSupervisionViolationResponseDecision,
    StateSupervisionViolationResponseType,
    StateSupervisionViolationResponseDecidingBodyType,
)
from recidiviz.persistence.entity.state.entities import (
    StateIncarcerationPeriod,
    StateSupervisionPeriod,
    StateSupervisionViolationResponseDecisionEntry,
    StateSupervisionViolationResponse,
)

STATE_CODE = "US_PA"

# pylint: disable=protected-access
class TestIsCommitmentFromSupervision(unittest.TestCase):
    """Tests the us_pa_admission_is_commitment_from_supervision function."""

    def test_us_pa_admission_is_commitment_from_supervision_parole(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            state_code=STATE_CODE,
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            status=StateIncarcerationPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        self.assertTrue(
            us_pa_commitment_from_supervision_utils._us_pa_admission_is_commitment_from_supervision(
                incarceration_period
            )
        )

    def test_us_pa_admission_is_commitment_from_supervision_probation(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            state_code=STATE_CODE,
            admission_reason=StateIncarcerationPeriodAdmissionReason.PROBATION_REVOCATION,
            status=StateIncarcerationPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        self.assertTrue(
            us_pa_commitment_from_supervision_utils._us_pa_admission_is_commitment_from_supervision(
                incarceration_period
            )
        )

    def test_us_pa_admission_is_commitment_from_supervision_not_revocation(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            state_code=STATE_CODE,
            admission_reason=StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION,
            status=StateIncarcerationPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        self.assertFalse(
            us_pa_commitment_from_supervision_utils._us_pa_admission_is_commitment_from_supervision(
                incarceration_period
            )
        )


class TestPreCommitmentSupervisionPeriodsIfCommitment(unittest.TestCase):
    """Tests the us_pa_pre_commitment_supervision_periods_if_commitment function."""

    def test_us_pa_pre_commitment_supervision_periods_if_commitment(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            state_code=STATE_CODE,
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            admission_date=date(2020, 1, 1),
            status=StateIncarcerationPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        revoked_supervision_period = StateSupervisionPeriod.new_with_defaults(
            state_code=STATE_CODE,
            supervision_period_supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            start_date=date(2019, 12, 1),
            status=StateSupervisionPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        (
            admission_is_revocation,
            revoked_supervision_periods,
        ) = us_pa_commitment_from_supervision_utils.us_pa_pre_commitment_supervision_periods_if_commitment(
            incarceration_period, [revoked_supervision_period]
        )

        self.assertTrue(admission_is_revocation)
        self.assertEqual([revoked_supervision_period], revoked_supervision_periods)

    def test_us_pa_pre_commitment_supervision_periods_if_commitment_no_revocation(
        self,
    ):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            state_code=STATE_CODE,
            admission_reason=StateIncarcerationPeriodAdmissionReason.ADMITTED_FROM_SUPERVISION,
            admission_date=date(2020, 1, 1),
            status=StateIncarcerationPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        revoked_supervision_period = StateSupervisionPeriod.new_with_defaults(
            state_code=STATE_CODE,
            supervision_period_supervision_type=StateSupervisionPeriodSupervisionType.PAROLE,
            start_date=date(2019, 12, 1),
            status=StateSupervisionPeriodStatus.PRESENT_WITHOUT_INFO,
        )

        (
            admission_is_revocation,
            revoked_supervision_periods,
        ) = us_pa_commitment_from_supervision_utils.us_pa_pre_commitment_supervision_periods_if_commitment(
            incarceration_period, [revoked_supervision_period]
        )

        self.assertFalse(admission_is_revocation)
        self.assertEqual([], revoked_supervision_periods)


class TestPurposeForIncarcerationAndSubtype(unittest.TestCase):
    """Tests the us_pa_purpose_for_incarceration_and_subtype function."""

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_RESCR(self):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a commitment to a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual(
            SHOCK_INCARCERATION_UNDER_6_MONTHS,
            purpose_for_incarceration_subtype,
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_RESCR6(self):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_6_MONTHS,
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a commitment to a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual(
            SHOCK_INCARCERATION_6_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_RESCR9(self):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_9_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_9_MONTHS,
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a commitment to a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual(
            SHOCK_INCARCERATION_9_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_RESCR12(self):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_12_MONTHS,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_12_MONTHS,
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a commitment to a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual(
            SHOCK_INCARCERATION_12_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_no_set_subtype(
        self,
    ):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            # Program 46 indicates a commitment to a 6, 9 or 12 month stay
            specialized_purpose_for_incarceration_raw_text="CCIS-46",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        # Default subtype for SHOCK_INCARCERATION is RESCR
        self.assertEqual(
            SHOCK_INCARCERATION_UNDER_6_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_sci_no_set_subtype(
        self,
    ):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        # Default subtype for SHOCK_INCARCERATION is RESCR
        self.assertEqual(
            SHOCK_INCARCERATION_UNDER_6_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_shock_incarceration_sci_with_board_actions(
        self,
    ):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_12_MONTHS,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_12_MONTHS,
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual(
            SHOCK_INCARCERATION_12_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_and_subtype_reincarceration(self):
        parole_board_decision_entry = (
            StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                state_code=STATE_CODE,
                decision_raw_text="XXX",
            )
        )

        parole_board_permanent_decision = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, [parole_board_permanent_decision]
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.GENERAL,
            purpose_for_incarceration,
        )
        self.assertIsNone(purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_and_subtype_reincarceration_no_board_actions(
        self,
    ):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.STATE_PRISON,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.GENERAL,
            purpose_for_incarceration,
        )
        self.assertIsNone(purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_and_subtype_PVC(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.GENERAL,
            # Program 26 indicates a stay in a PVC
            specialized_purpose_for_incarceration_raw_text=PURPOSE_FOR_INCARCERATION_PVC,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.SHOCK_INCARCERATION,
            purpose_for_incarceration,
        )
        self.assertEqual("PVC", purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_and_subtype_treatment(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            purpose_for_incarceration,
        )
        self.assertIsNone(purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_and_subtype_treatment_51(self):
        incarceration_period = StateIncarcerationPeriod.new_with_defaults(
            incarceration_period_id=222,
            external_id="ip2",
            state_code=STATE_CODE,
            incarceration_type=StateIncarcerationType.COUNTY_JAIL,
            status=StateIncarcerationPeriodStatus.NOT_IN_CUSTODY,
            admission_date=date(2018, 5, 19),
            admission_reason=StateIncarcerationPeriodAdmissionReason.PAROLE_REVOCATION,
            specialized_purpose_for_incarceration=StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            specialized_purpose_for_incarceration_raw_text="CCIS-51",
            release_date=date(2019, 3, 3),
            release_reason=StateIncarcerationPeriodReleaseReason.SENTENCE_SERVED,
        )

        (
            purpose_for_incarceration,
            purpose_for_incarceration_subtype,
        ) = us_pa_commitment_from_supervision_utils.us_pa_purpose_for_incarceration_and_subtype(
            incarceration_period, []
        )

        self.assertEqual(
            StateSpecializedPurposeForIncarceration.TREATMENT_IN_PRISON,
            purpose_for_incarceration,
        )
        self.assertIsNone(purpose_for_incarceration_subtype)


# pylint: disable=protected-access
class TestRevocationTypeSubtypeFromParoleDecisions(unittest.TestCase):
    """Tests the _purpose_for_incarceration_subtype function."""

    def test_purpose_for_incarceration_subtype(self):
        parole_board_decision_entry_old = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
        )

        parole_board_permanent_decision_outside_window = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_old],
        )

        parole_board_decision_entry_new = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_12_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_12_MONTHS,
        )

        parole_board_permanent_decision_in_window = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_new],
        )

        commitment_admission_date = date(2020, 1, 1)
        specialized_purpose_for_incarceration_raw_text = "CCIS-46"

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date,
                specialized_purpose_for_incarceration_raw_text,
                [
                    parole_board_permanent_decision_outside_window,
                    parole_board_permanent_decision_in_window,
                ],
            )
        )

        self.assertEqual(
            SHOCK_INCARCERATION_12_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_subtype_pvc(self):
        commitment_admission_date = date(2020, 1, 1)
        specialized_purpose_for_incarceration_raw_text = PURPOSE_FOR_INCARCERATION_PVC

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date,
                specialized_purpose_for_incarceration_raw_text,
                [],
            )
        )

        self.assertEqual(SHOCK_INCARCERATION_PVC, purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_subtype_no_parole_decisions(self):
        violation_response = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2018, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.VIOLATION_REPORT,
        )

        commitment_admission_date = date(2020, 1, 1)

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date, None, [violation_response]
            )
        )

        self.assertIsNone(purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_subtype_after_revocations(self):
        parole_board_decision_entry = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_UNDER_6_MONTHS,
        )

        parole_board_permanent_decision_outside_window = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2020, month=5, day=16),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry],
        )

        commitment_admission_date = date(2020, 1, 1)

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date,
                None,
                [parole_board_permanent_decision_outside_window],
            )
        )

        self.assertIsNone(purpose_for_incarceration_subtype)

    def test_purpose_for_incarceration_subtype_two_same_day(self):
        """Tests that the longer shock incarceration length is taken from two parole board actions that happened on
        the same day."""
        parole_board_decision_entry_1 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_9_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_9_MONTHS,
        )

        parole_board_permanent_decision_1 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_1],
        )

        parole_board_decision_entry_2 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_6_MONTHS,
        )

        parole_board_permanent_decision_2 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_2],
        )

        commitment_admission_date = date(2020, 1, 1)

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date,
                None,
                [parole_board_permanent_decision_1, parole_board_permanent_decision_2],
            )
        )

        self.assertEqual(
            SHOCK_INCARCERATION_9_MONTHS, purpose_for_incarceration_subtype
        )

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date,
                None,
                [parole_board_permanent_decision_2, parole_board_permanent_decision_1],
            )
        )

        self.assertEqual(
            SHOCK_INCARCERATION_9_MONTHS, purpose_for_incarceration_subtype
        )

    def test_purpose_for_incarceration_subtype_no_responses(self):
        commitment_admission_date = date(2020, 1, 1)

        purpose_for_incarceration_subtype = (
            us_pa_commitment_from_supervision_utils._purpose_for_incarceration_subtype(
                commitment_admission_date, None, []
            )
        )

        self.assertIsNone(purpose_for_incarceration_subtype)


# pylint: disable=protected-access
class TestMostSevereRevocationTypeSubtype(unittest.TestCase):
    """Tests the _most_severe_purpose_for_incarceration_subtype function."""

    def test_most_severe_purpose_for_incarceration_subtype(self):
        parole_board_decision_entry_1 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_9_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_9_MONTHS,
        )

        parole_board_permanent_decision_1 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_1],
        )

        parole_board_decision_entry_2 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_6_MONTHS,
        )

        parole_board_permanent_decision_2 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_2],
        )

        (
            purpose_for_incarceration_subtype
        ) = us_pa_commitment_from_supervision_utils._most_severe_purpose_for_incarceration_subtype(
            [parole_board_permanent_decision_1, parole_board_permanent_decision_2]
        )

        self.assertEqual(
            SHOCK_INCARCERATION_9_MONTHS, purpose_for_incarceration_subtype
        )

    def test_most_severe_purpose_for_incarceration_subtype_invalid_type(self):
        parole_board_decision_entry_1 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text="XXX",
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text="XXX",
        )

        parole_board_permanent_decision_1 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_1],
        )

        parole_board_decision_entry_2 = StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
            state_code=STATE_CODE,
            decision_raw_text=SHOCK_INCARCERATION_6_MONTHS,
            revocation_type=StateSupervisionViolationResponseRevocationType.SHOCK_INCARCERATION,
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            revocation_type_raw_text=SHOCK_INCARCERATION_6_MONTHS,
        )

        parole_board_permanent_decision_2 = StateSupervisionViolationResponse.new_with_defaults(
            state_code=STATE_CODE,
            response_date=date(year=2019, month=12, day=30),
            response_type=StateSupervisionViolationResponseType.PERMANENT_DECISION,
            response_type_raw_text="PERMANENT_DECISION",
            deciding_body_type=StateSupervisionViolationResponseDecidingBodyType.PAROLE_BOARD,
            deciding_body_type_raw_text="PAROLE_BOARD",
            supervision_violation_response_decisions=[parole_board_decision_entry_2],
        )

        purpose_for_incarceration_subtype = us_pa_commitment_from_supervision_utils._most_severe_purpose_for_incarceration_subtype(
            [parole_board_permanent_decision_1, parole_board_permanent_decision_2]
        )

        self.assertEqual(
            SHOCK_INCARCERATION_6_MONTHS, purpose_for_incarceration_subtype
        )

    def test_most_severe_purpose_for_incarceration_subtype_no_responses(self):
        purpose_for_incarceration_subtype = us_pa_commitment_from_supervision_utils._most_severe_purpose_for_incarceration_subtype(
            []
        )

        self.assertIsNone(purpose_for_incarceration_subtype)