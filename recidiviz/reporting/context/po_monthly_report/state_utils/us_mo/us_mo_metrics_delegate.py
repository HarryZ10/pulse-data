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
"""Metrics for US_MO that are to be displayed in the PO Monthly Report"""
from typing import Dict, List

from recidiviz.case_triage.state_utils.us_mo import US_MO_SUPERVISION_LEVEL_NAMES
from recidiviz.common.constants.state.state_supervision_period import (
    StateSupervisionLevel,
)
from recidiviz.reporting.context.po_monthly_report.constants import (
    ABSCONSIONS,
    CRIME_REVOCATIONS,
    POS_DISCHARGES,
    SUPERVISION_DOWNGRADES,
    TECHNICAL_REVOCATIONS,
)
from recidiviz.reporting.context.po_monthly_report.state_utils.po_monthly_report_metrics_delegate import (
    PoMonthlyReportMetricsDelegate,
)


class UsMoMetricsDelegate(PoMonthlyReportMetricsDelegate):
    """Metrics for US_MO that are to be displayed in the PO Monthly Report"""

    @property
    def decarceral_actions_metrics(self) -> List[str]:
        return [POS_DISCHARGES, SUPERVISION_DOWNGRADES]

    @property
    def client_outcome_metrics(self) -> List[str]:
        return [TECHNICAL_REVOCATIONS, CRIME_REVOCATIONS, ABSCONSIONS]

    @property
    def compliance_action_metrics(self) -> List[str]:
        return []

    @property
    def compliance_action_metric_goal_thresholds(self) -> Dict[str, float]:
        return {}

    # TODO(#10286): Get correct copy for US_MO reports
    @property
    def completion_date_label(self) -> str:
        return "FTRD"  # stands for "full-term release date" FYI

    @property
    def has_case_triage(self) -> bool:
        return False

    @property
    def supervision_level_labels(self) -> Dict[StateSupervisionLevel, str]:
        return US_MO_SUPERVISION_LEVEL_NAMES
