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
"""Implements data models for opportunities that are not part of a database schema."""
from typing import Dict

import attr

from recidiviz.case_triage.client_utils.compliance import (
    get_assessment_due_status,
    get_contact_due_status,
)
from recidiviz.case_triage.opportunities.types import Opportunity, OpportunityType
from recidiviz.persistence.database.schema.case_triage.schema import ETLClient


@attr.s(auto_attribs=True)
class ComputedOpportunity(Opportunity):
    """An opportunity not backed by an underlying database entity."""

    state_code: str
    supervising_officer_external_id: str
    person_external_id: str
    opportunity_type: str
    opportunity_metadata: dict

    @staticmethod
    def build_all_for_client(
        client: ETLClient,
    ) -> Dict[OpportunityType, "ComputedOpportunity"]:
        """Outputs all ComputedOpportunities applicable to the given client."""
        opps = {}

        client_args = {
            "state_code": client.state_code,
            "supervising_officer_external_id": client.supervising_officer_external_id,
            "person_external_id": client.person_external_id,
        }

        # employment opportunities
        if client.employer is None and not client.receiving_ssi_or_disability_income:
            opps[OpportunityType.EMPLOYMENT] = ComputedOpportunity(
                opportunity_type=OpportunityType.EMPLOYMENT.value,
                opportunity_metadata={},
                **client_args
            )

        # compliance opportunities
        assessment_status = get_assessment_due_status(client)
        if assessment_status:
            opps[OpportunityType.ASSESSMENT] = ComputedOpportunity(
                opportunity_type=OpportunityType.ASSESSMENT.value,
                opportunity_metadata={"status": assessment_status},
                **client_args
            )

        contact_status = get_contact_due_status(client)
        if contact_status:
            opps[OpportunityType.CONTACT] = ComputedOpportunity(
                opportunity_type=OpportunityType.CONTACT.value,
                opportunity_metadata={"status": contact_status},
                **client_args
            )

        return opps