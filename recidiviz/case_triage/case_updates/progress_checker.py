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
"""Provides framework for evaluating whether a CaseUpdateActionType is still in-progress for a client."""
from typing import Callable, Dict

import attr

from recidiviz.case_triage.case_updates.types import (
    CaseActionVersionData,
    CaseUpdateActionType,
)
from recidiviz.case_triage.opportunities.models import NEW_TO_CASELOAD_THRESHOLD_DAYS


def _in_progress_until_changed(
    current_version: CaseActionVersionData, last_version: CaseActionVersionData
) -> bool:
    return attr.asdict(current_version) == attr.asdict(last_version)


def _always_in_progress(
    _current_version: CaseActionVersionData, _last_version: CaseActionVersionData
) -> bool:
    return True


def _in_progress_until_more_recent_date(
    current_version: CaseActionVersionData, last_version: CaseActionVersionData
) -> bool:
    # In progress if there is no current recorded date
    # or the last recorded date is as if not more recent than the current date
    return current_version.last_recorded_date is None or (
        last_version.last_recorded_date is not None
        and last_version.last_recorded_date >= current_version.last_recorded_date
    )


def _found_employment_progress_checker(
    current_version: CaseActionVersionData, _last_version: CaseActionVersionData
) -> bool:
    return (
        current_version.last_employer is None
        or "UNEMP" in current_version.last_employer.upper()
    )


def _new_to_caseload_progress_checker(
    current_version: CaseActionVersionData, _last_version: CaseActionVersionData
) -> bool:
    """Update remains in progress until the newness threshold expires.
    This allows for clients to become new again in the future, e.g. via transfers."""

    # if there is no longer a recorded number of days, clear the update
    # (this is not really expected but it's technically possible)
    if current_version.last_days_with_current_po is None:
        return False

    if current_version.last_days_with_current_po > NEW_TO_CASELOAD_THRESHOLD_DAYS:
        return False

    return True


_CASE_UPDATE_ACTION_TYPE_TO_PROGRESS_CHECKER: Dict[
    CaseUpdateActionType, Callable[[CaseActionVersionData, CaseActionVersionData], bool]
] = {
    # Assessment progress checkers
    CaseUpdateActionType.COMPLETED_ASSESSMENT: _in_progress_until_more_recent_date,
    CaseUpdateActionType.INCORRECT_ASSESSMENT_DATA: _in_progress_until_changed,
    # Employment progress checkers
    CaseUpdateActionType.FOUND_EMPLOYMENT: _found_employment_progress_checker,
    CaseUpdateActionType.INCORRECT_EMPLOYMENT_DATA: _in_progress_until_changed,
    # Face to face contact progress checkers
    CaseUpdateActionType.SCHEDULED_FACE_TO_FACE: _in_progress_until_more_recent_date,
    CaseUpdateActionType.INCORRECT_CONTACT_DATA: _in_progress_until_changed,
    # Home visit contact progress checkers
    CaseUpdateActionType.INCORRECT_HOME_VISIT_DATA: _in_progress_until_changed,
    # Supervision level progress checkers
    CaseUpdateActionType.DOWNGRADE_INITIATED: _in_progress_until_changed,
    # TODO(#5721): Need to better understand how to detect when DISCHARGE_INITIATED is no longer in-progress.
    CaseUpdateActionType.DISCHARGE_INITIATED: _always_in_progress,
    CaseUpdateActionType.INCORRECT_SUPERVISION_LEVEL_DATA: _in_progress_until_changed,
    CaseUpdateActionType.NOT_ON_CASELOAD: _always_in_progress,
    CaseUpdateActionType.CURRENTLY_IN_CUSTODY: _always_in_progress,
    CaseUpdateActionType.INCORRECT_NEW_TO_CASELOAD_DATA: _new_to_caseload_progress_checker,
}


def check_case_update_action_progress(
    action_type: CaseUpdateActionType,
    *,
    last_version: CaseActionVersionData,
    current_version: CaseActionVersionData,
) -> bool:
    progress_checker = _CASE_UPDATE_ACTION_TYPE_TO_PROGRESS_CHECKER[action_type]
    return progress_checker(current_version, last_version)
