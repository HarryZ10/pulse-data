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
"""This class implements tests for the Justice Counts UserInterface."""


from recidiviz.justice_counts.agency import AgencyInterface
from recidiviz.justice_counts.user_account import UserAccountInterface
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.tests.justice_counts.utils import JusticeCountsDatabaseTestCase


class TestUserInterface(JusticeCountsDatabaseTestCase):
    """Implements tests for the UserAccountInterface."""

    def test_create_and_get_user(self) -> None:
        with SessionFactory.using_database(self.database_key) as session:
            AgencyInterface.create_agency(session=session, name="Agency Alpha")
            UserAccountInterface.create_user(session=session, auth0_user_id="id0")
            UserAccountInterface.add_agency_to_user(
                session=session, auth0_user_id="id0", agency_name="Agency Alpha"
            )

        with SessionFactory.using_database(self.database_key) as session:
            user = UserAccountInterface.get_user_by_auth0_user_id(
                session=session, auth0_user_id="id0"
            )
            self.assertEqual(user.auth0_user_id, "id0")
            self.assertEqual({a.name for a in user.agencies}, {"Agency Alpha"})