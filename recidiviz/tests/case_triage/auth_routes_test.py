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
"""Implements tests for the authorization blueprint."""
import unittest

from flask import Flask, session

from recidiviz.case_triage.auth_routes import create_auth_blueprint
from recidiviz.tests.auth.utils import get_test_auth0_config


class TestAuthRoutes(unittest.TestCase):
    """Tests the auth blueprint"""

    def setUp(self) -> None:
        authorization_config = get_test_auth0_config()

        auth_blueprint = create_auth_blueprint(authorization_config)

        self.test_app = Flask(__name__)
        self.test_app.secret_key = "not a secret"
        self.test_app.register_blueprint(auth_blueprint, url_prefix="/auth")

    def test_log_out(self) -> None:
        """
        Cobalt ID: #PT7441_2
        OWASP ASVS: 3.3.1
        CWE 613
        NIST 7.1
        """
        with self.test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["session_data"] = {}

            response = client.post("/auth/log_out")

            self.assertEqual(
                "session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; HttpOnly; Path=/",
                response.headers["Set-Cookie"],
            )

            self.assertEqual(
                "https://auth0.localhost/v2/logout?client_id=test_client_id&returnTo=http%3A%2F%2Flocalhost%3A3000",
                response.headers["Location"],
            )

            with self.test_app.test_request_context():
                self.assertEqual(0, len(session.keys()))
