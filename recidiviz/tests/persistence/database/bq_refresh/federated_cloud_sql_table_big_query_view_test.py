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
"""Tests for federated_cloud_sql_table_big_query_view.py."""

import importlib
import unittest
from unittest import mock

from more_itertools import one

from recidiviz.big_query.big_query_view import BigQueryAddress
from recidiviz.common.constants import states
from recidiviz.common.constants.states import StateCode
from recidiviz.persistence.database.base_schema import StateBase, JailsBase
from recidiviz.persistence.database.bq_refresh.federated_cloud_sql_table_big_query_view import (
    FederatedCloudSQLTableBigQueryViewBuilder,
    FederatedCloudSQLTableBigQueryView,
)
from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.sqlalchemy_database_key import (
    SQLAlchemyDatabaseKey,
    SQLAlchemyStateDatabaseVersion,
)
from recidiviz.tools.utils.dataset_overrides import dataset_overrides_for_view_builders


class FederatedCloudSQLTableBigQueryViewTest(unittest.TestCase):
    """Tests for federated_cloud_sql_table_big_query_view.py."""

    def setUp(self) -> None:
        # Ensures StateCode.US_XX is properly loaded
        importlib.reload(states)
        self.metadata_patcher = mock.patch("recidiviz.utils.metadata.project_id")
        self.mock_project_id_fn = self.metadata_patcher.start()
        self.mock_project_id_fn.return_value = "test-project"

    def tearDown(self) -> None:
        self.metadata_patcher.stop()

    def test_build_view_state_primary(self) -> None:
        table = one(
            t for t in StateBase.metadata.sorted_tables if t.name == "state_person"
        )
        view_builder = FederatedCloudSQLTableBigQueryViewBuilder(
            instance_region="us-east2",
            table=table,
            view_id=table.name,
            cloud_sql_query="SELECT * FROM state_person;",
            database_key=SQLAlchemyDatabaseKey.for_state_code(
                StateCode.US_XX, db_version=SQLAlchemyStateDatabaseVersion.PRIMARY
            ),
            materialized_address_override=BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
        )
        expected_description = """View providing a connection to the [state_person]
table in the [us_xx_primary] database in the [STATE] schema. This view is 
managed outside of regular view update operations and the results can be found in the 
schema-specific datasets (`state`, `jails`, `justice_counts`, etc)."""

        expected_view_query = f"""/*{expected_description}*/
SELECT
    *
FROM EXTERNAL_QUERY(
    "test-project.us-east2.state_us_xx_primary_cloudsql",
    "SELECT * FROM state_person;"
)"""

        # Build without dataset overrides
        view = view_builder.build()

        self.assertIsInstance(view, FederatedCloudSQLTableBigQueryView)
        self.assertEqual(expected_view_query, view.view_query)
        self.assertEqual(expected_description, view.description)
        self.assertEqual(
            BigQueryAddress(
                dataset_id="state_us_xx_primary_cloudsql_connection",
                table_id="state_person",
            ),
            view.address,
        )
        self.assertEqual(
            BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
            view.materialized_address,
        )

        # Build with dataset overrides
        dataset_overrides = dataset_overrides_for_view_builders(
            "test_prefix", [view_builder]
        )
        view_with_overrides = view_builder.build(dataset_overrides=dataset_overrides)

        self.assertIsInstance(view, FederatedCloudSQLTableBigQueryView)
        self.assertEqual(expected_view_query, view_with_overrides.view_query)
        self.assertEqual(expected_description, view_with_overrides.description)
        self.assertEqual(
            BigQueryAddress(
                dataset_id="test_prefix_state_us_xx_primary_cloudsql_connection",
                table_id="state_person",
            ),
            view_with_overrides.address,
        )
        self.assertEqual(
            BigQueryAddress(
                dataset_id="test_prefix_materialized_dataset",
                table_id="materialized_table",
            ),
            view_with_overrides.materialized_address,
        )

    def test_build_view_state_legacy(self) -> None:
        table = one(
            t for t in StateBase.metadata.sorted_tables if t.name == "state_person"
        )
        view_builder = FederatedCloudSQLTableBigQueryViewBuilder(
            instance_region="us-east2",
            table=table,
            view_id=table.name,
            cloud_sql_query="SELECT * FROM state_person;",
            database_key=SQLAlchemyDatabaseKey.for_state_code(
                StateCode.US_XX, db_version=SQLAlchemyStateDatabaseVersion.LEGACY
            ),
            materialized_address_override=BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
        )
        expected_description = """View providing a connection to the [state_person]
table in the [postgres] database in the [STATE] schema. This view is 
managed outside of regular view update operations and the results can be found in the 
schema-specific datasets (`state`, `jails`, `justice_counts`, etc)."""

        expected_view_query = f"""/*{expected_description}*/
SELECT
    *
FROM EXTERNAL_QUERY(
    "test-project.us-east2.state_cloudsql",
    "SELECT * FROM state_person;"
)"""

        # Build without dataset overrides
        view = view_builder.build()

        self.assertIsInstance(view, FederatedCloudSQLTableBigQueryView)
        self.assertEqual(expected_view_query, view.view_query)
        self.assertEqual(expected_description, view.description)
        self.assertEqual(
            BigQueryAddress(
                dataset_id="state_cloudsql_connection",
                table_id="state_person",
            ),
            view.address,
        )
        self.assertEqual(
            BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
            view.materialized_address,
        )

    def test_build_view_non_multi_db_schema(self) -> None:
        table = one(t for t in JailsBase.metadata.sorted_tables if t.name == "person")
        view_builder = FederatedCloudSQLTableBigQueryViewBuilder(
            instance_region="us-east2",
            table=table,
            view_id=table.name,
            cloud_sql_query="SELECT * FROM person;",
            database_key=SQLAlchemyDatabaseKey.for_schema(SchemaType.JAILS),
            materialized_address_override=BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
        )
        expected_description = """View providing a connection to the [person]
table in the [postgres] database in the [JAILS] schema. This view is 
managed outside of regular view update operations and the results can be found in the 
schema-specific datasets (`state`, `jails`, `justice_counts`, etc)."""

        expected_view_query = f"""/*{expected_description}*/
SELECT
    *
FROM EXTERNAL_QUERY(
    "test-project.us-east2.jails_cloudsql",
    "SELECT * FROM person;"
)"""

        # Build without dataset overrides
        view = view_builder.build()

        self.assertIsInstance(view, FederatedCloudSQLTableBigQueryView)
        self.assertEqual(expected_view_query, view.view_query)
        self.assertEqual(expected_description, view.description)
        self.assertEqual(
            BigQueryAddress(
                dataset_id="jails_cloudsql_connection",
                table_id="person",
            ),
            view.address,
        )
        self.assertEqual(
            BigQueryAddress(
                dataset_id="materialized_dataset", table_id="materialized_table"
            ),
            view.materialized_address,
        )