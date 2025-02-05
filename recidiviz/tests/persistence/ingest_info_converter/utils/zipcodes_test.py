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
"""Implements tests for the ZipcodeDatabaseManager."""
import unittest

from recidiviz.persistence.ingest_info_converter.utils.zipcodes import (
    ZipcodeDatabaseManager,
)


class TestZipcodeDatabaseManager(unittest.TestCase):
    def test_bogus_zipcode_county(self) -> None:
        self.assertIsNone(ZipcodeDatabaseManager.county_for_zipcode("aoiwejf"))

    def test_valid_zipcode_county(self) -> None:
        self.assertEqual(
            ZipcodeDatabaseManager.county_for_zipcode("20001"),
            "District of Columbia",
        )

    def test_bogus_zipcode_state(self) -> None:
        self.assertIsNone(ZipcodeDatabaseManager.state_for_zipcode("aoiwejf"))

    def test_valid_zipcode_state(self) -> None:
        self.assertEqual(
            ZipcodeDatabaseManager.state_for_zipcode("94110"),
            "CA",
        )
