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
"""A class for caching information about a set of incarceration periods that are ready
for use in the calculation pipelines."""

from collections import defaultdict
from datetime import date
from typing import List, Set, Tuple, Dict, Optional

import attr

from recidiviz.common.constants.state.shared_enums import StateCustodialAuthority
from recidiviz.common.constants.state.state_incarceration_period import (
    StateIncarcerationPeriodAdmissionReason,
    is_official_admission,
    is_official_release,
)
from recidiviz.common.date import DateRange, DateRangeDiff
from recidiviz.persistence.entity.state.entities import StateIncarcerationPeriod


@attr.s
class PreProcessedIncarcerationPeriodIndex:
    """A class for caching information about a set of pre-processed incarceration
    periods for use in the calculation pipelines.
    """

    incarceration_periods: List[StateIncarcerationPeriod] = attr.ib()

    # Incarceration periods during which a person cannot also be counted in the supervision population
    incarceration_periods_not_under_supervision_authority: List[
        StateIncarcerationPeriod
    ] = attr.ib()

    @incarceration_periods_not_under_supervision_authority.default
    def _incarceration_periods_not_under_supervision_authority(
        self,
    ) -> List[StateIncarcerationPeriod]:
        """The incarceration periods in the incarceration_periods list during which a person cannot also be counted in
        the supervision population. If a person is in a facility, but is under the custodial authority of a supervision
        department, then they can be counted in the supervision population"""
        if not self.incarceration_periods:
            return []

        return [
            ip
            for ip in self.incarceration_periods
            if ip.custodial_authority != StateCustodialAuthority.SUPERVISION_AUTHORITY
        ]

    # A set of tuples in the format (year, month) for each month of which this person has been incarcerated for any
    # portion of the month, where the incarceration prevents the person from being counted simultaneously in the
    # supervision population.
    month_to_overlapping_ips_not_under_supervision_authority: Dict[
        int, Dict[int, List[StateIncarcerationPeriod]]
    ] = attr.ib()

    @month_to_overlapping_ips_not_under_supervision_authority.default
    def _month_to_overlapping_ips_not_under_supervision_authority(
        self,
    ) -> Dict[int, Dict[int, List[StateIncarcerationPeriod]]]:
        month_to_overlapping_ips_not_under_supervision_authority: Dict[
            int, Dict[int, List[StateIncarcerationPeriod]]
        ] = defaultdict(lambda: defaultdict(list))

        for (
            incarceration_period
        ) in self.incarceration_periods_not_under_supervision_authority:
            for (
                year,
                month,
            ) in incarceration_period.duration.get_months_range_overlaps_at_all():
                month_to_overlapping_ips_not_under_supervision_authority[year][
                    month
                ].append(incarceration_period)

        return month_to_overlapping_ips_not_under_supervision_authority

    # A set of tuples in the format (year, month) for each month of which this person has been incarcerated for the full
    # month, where the incarceration prevents the person from being counted simultaneously in the supervision
    # population.
    months_excluded_from_supervision_population: Set[Tuple[int, int]] = attr.ib()

    @months_excluded_from_supervision_population.default
    def _months_excluded_from_supervision_population(self) -> Set[Tuple[int, int]]:
        """For each StateIncarcerationPeriod, identifies months where the person was incarcerated for every day during
        that month. Returns a set of months in the format (year, month) for which the person spent the entire month in a
        prison, where the incarceration prevents the person from being counted simultaneously in the supervision
        population.
        """
        months_excluded_from_supervision_population: Set[Tuple[int, int]] = set()

        for (
            incarceration_period
        ) in self.incarceration_periods_not_under_supervision_authority:
            months_overlaps_at_all = (
                incarceration_period.duration.get_months_range_overlaps_at_all()
            )

            for year, month in months_overlaps_at_all:
                overlapping_periods = (
                    self.month_to_overlapping_ips_not_under_supervision_authority[year][
                        month
                    ]
                )

                remaining_ranges_to_cover = (
                    self._get_portions_of_range_not_covered_by_periods_subset(
                        DateRange.for_month(year, month), overlapping_periods
                    )
                )
                if not remaining_ranges_to_cover:
                    months_excluded_from_supervision_population.add((year, month))

        return months_excluded_from_supervision_population

    # A dictionary mapping admission dates of admissions to prison to the StateIncarcerationPeriods that happened on
    # that day.
    incarceration_periods_by_admission_date: Dict[
        date, List[StateIncarcerationPeriod]
    ] = attr.ib()

    @incarceration_periods_by_admission_date.default
    def _incarceration_periods_by_admission_date(
        self,
    ) -> Dict[date, List[StateIncarcerationPeriod]]:
        """Organizes the list of StateIncarcerationPeriods by the admission_date on the period."""
        incarceration_periods_by_admission_date: Dict[
            date, List[StateIncarcerationPeriod]
        ] = defaultdict(list)

        for incarceration_period in self.incarceration_periods:
            if incarceration_period.admission_date:
                incarceration_periods_by_admission_date[
                    incarceration_period.admission_date
                ].append(incarceration_period)

        return incarceration_periods_by_admission_date

    def is_excluded_from_supervision_population_for_range(
        self, range_to_cover: DateRange
    ) -> bool:
        """Returns True if this person is incarcerated for the full duration of the date range."""

        months_range_overlaps = range_to_cover.get_months_range_overlaps_at_all()

        if not months_range_overlaps:
            return False

        months_without_exclusion_from_supervision = []
        for year, month in months_range_overlaps:
            was_incarcerated_all_month = (
                year,
                month,
            ) in self.months_excluded_from_supervision_population
            if not was_incarcerated_all_month:
                months_without_exclusion_from_supervision.append((year, month))

        for year, month in months_without_exclusion_from_supervision:
            overlapping_periods = (
                self.month_to_overlapping_ips_not_under_supervision_authority[year][
                    month
                ]
            )

            range_portion_overlapping_month = (
                range_to_cover.portion_overlapping_with_month(year, month)
            )
            if not range_portion_overlapping_month:
                raise ValueError(
                    f"Expecting only months that overlap with the range, month ({year}, {month}) does not."
                )

            remaining_ranges_to_cover = (
                self._get_portions_of_range_not_covered_by_periods_subset(
                    range_portion_overlapping_month, overlapping_periods
                )
            )
            if remaining_ranges_to_cover:
                return False

        return True

    def incarceration_admissions_between_dates(
        self, start_date: date, end_date: date
    ) -> bool:
        """Returns whether there were incarceration admissions between the start_date and end_date, not inclusive of
        the end date."""
        return any(
            ip.admission_date and start_date <= ip.admission_date < end_date
            for ip in self.incarceration_periods
        )

    def incarceration_periods_with_admissions_between_dates(
        self, start_date_inclusive: date, end_date_exclusive: date
    ) -> List[StateIncarcerationPeriod]:
        """Returns any incarceration periods with admissions between the start_date and end_date, not inclusive of
        the end date."""
        return [
            ip
            for ip in self.incarceration_periods
            if ip.admission_date
            and start_date_inclusive <= ip.admission_date < end_date_exclusive
        ]

    @staticmethod
    def _get_portions_of_range_not_covered_by_periods_subset(
        time_range_to_cover: DateRange,
        incarceration_periods_subset: List[StateIncarcerationPeriod],
    ) -> List[DateRange]:
        """Returns a list of date ranges within the provided |time_range_to_cover| which the provided set of
        incarceration periods does not fully overlap.
        """

        remaining_ranges_to_cover = [time_range_to_cover]

        for incarceration_period in incarceration_periods_subset:
            new_remaining_ranges_to_cover = []
            for time_range in remaining_ranges_to_cover:
                new_remaining_ranges_to_cover.extend(
                    DateRangeDiff(
                        range_1=incarceration_period.duration, range_2=time_range
                    ).range_2_non_overlapping_parts
                )

            remaining_ranges_to_cover = new_remaining_ranges_to_cover
            if not remaining_ranges_to_cover:
                break

        return remaining_ranges_to_cover

    # A dictionary mapping incarceration_period_id values to the original
    # admission_reason and corresponding admission_reason_raw_text that started the
    # period of being incarcerated.
    original_admission_reasons_by_period_id: Dict[
        int, Tuple[StateIncarcerationPeriodAdmissionReason, Optional[str]]
    ] = attr.ib()

    @original_admission_reasons_by_period_id.default
    def _original_admission_reasons_by_period_id(
        self,
    ) -> Dict[int, Tuple[StateIncarcerationPeriodAdmissionReason, Optional[str]]]:
        """Determines the original admission reason of each period of incarceration. Returns a dictionary mapping
        incarceration_period_id values to the original admission_reason and corresponding admission_reason_raw_text that
        started the period of being incarcerated. People are often transferred between facilities during their time
        incarcerated, so this in practice is the most recent non-transfer admission reason for the given incarceration
        period."""
        original_admission_reasons_by_period_id: Dict[
            int, Tuple[StateIncarcerationPeriodAdmissionReason, Optional[str]]
        ] = {}

        most_recent_official_admission_reason: Optional[
            StateIncarcerationPeriodAdmissionReason
        ] = None
        most_recent_official_admission_reason_raw_text: Optional[str] = None

        for index, incarceration_period in enumerate(self.incarceration_periods):
            incarceration_period_id = incarceration_period.incarceration_period_id

            if not incarceration_period_id:
                raise ValueError(
                    "Unexpected incarceration period without a incarceration_period_id."
                )

            if not incarceration_period.admission_reason:
                raise ValueError(
                    "Incarceration period pre-processing is not setting missing admission_reasons correctly."
                )

            if index == 0 or is_official_admission(
                incarceration_period.admission_reason
            ):
                # These indicate that incarceration is "officially" starting
                most_recent_official_admission_reason = (
                    incarceration_period.admission_reason
                )
                most_recent_official_admission_reason_raw_text = (
                    incarceration_period.admission_reason_raw_text
                )

            if not most_recent_official_admission_reason:
                original_admission_reasons_by_period_id[incarceration_period_id] = (
                    incarceration_period.admission_reason,
                    incarceration_period.admission_reason_raw_text,
                )
            else:
                original_admission_reasons_by_period_id[incarceration_period_id] = (
                    most_recent_official_admission_reason,
                    most_recent_official_admission_reason_raw_text,
                )

            if is_official_release(incarceration_period.release_reason):
                # If the release from this period of incarceration indicates an official end to the period of
                # incarceration, then subsequent periods should not share the most recent admission reason.
                most_recent_official_admission_reason = None
                most_recent_official_admission_reason_raw_text = None

        return original_admission_reasons_by_period_id

    def preceding_incarceration_period(
        self, incarceration_period: StateIncarcerationPeriod
    ) -> Optional[StateIncarcerationPeriod]:
        """Returns the incarceration period which occurred immediately before the given
        period in this index.

        Returns None if the given period is the first period in this index.
        Raises a ValueError if the given period is not in this index."""
        preceding_incarceration_period: Optional[StateIncarcerationPeriod] = None

        if incarceration_period not in self.incarceration_periods:
            raise ValueError(
                f"Given incarceration period [{incarceration_period.incarceration_period_id}] "
                "not found in this incarceration period index"
            )

        ip_index: int = self.incarceration_periods.index(incarceration_period)
        if ip_index > 0:
            preceding_incarceration_period = self.incarceration_periods[ip_index - 1]

        return preceding_incarceration_period