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
"""Contains the factory class for creating PoMonthlyReportMetricsDelegate objects"""

from recidiviz.reporting.context.po_monthly_report.state_utils.po_monthly_report_metrics_delegate import (
    PoMonthlyReportMetricsDelegate,
)
from recidiviz.reporting.context.po_monthly_report.state_utils.us_id.us_id_metrics_delegate import (
    UsIdMetricsDelegate,
)
from recidiviz.reporting.context.po_monthly_report.state_utils.us_pa.us_pa_metrics_delegate import (
    UsPaMetricsDelegate,
)


class PoMonthlyReportMetricsDelegateFactory:
    @classmethod
    def build(cls, *, region_code: str) -> PoMonthlyReportMetricsDelegate:
        if region_code.upper() == "US_ID":
            return UsIdMetricsDelegate()
        if region_code.upper() == "US_PA":
            return UsPaMetricsDelegate()
        raise ValueError(f"Unexpected region_code provided: {region_code}")