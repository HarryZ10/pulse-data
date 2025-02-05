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
"""Tests for base_upload_state_files_to_ingest_bucket_controller.py"""
import datetime
import unittest
from unittest.mock import Mock, patch

from recidiviz.cloud_storage.gcsfs_path import GcsfsDirectoryPath, GcsfsFilePath
from recidiviz.common.results import MultiRequestResultWithSkipped
from recidiviz.ingest.direct.metadata.direct_ingest_instance_pause_status_manager import (
    DirectIngestInstancePauseStatusManager,
)
from recidiviz.ingest.direct.metadata.postgres_direct_ingest_file_metadata_manager import (
    PostgresDirectIngestRawFileMetadataManager,
)
from recidiviz.ingest.direct.sftp.base_upload_state_files_to_ingest_bucket_controller import (
    UploadStateFilesToIngestBucketController,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.sqlalchemy_database_key import SQLAlchemyDatabaseKey
from recidiviz.tests.cloud_storage.fake_gcs_file_system import FakeGCSFileSystem
from recidiviz.tests.utils import fakes

TODAY = datetime.datetime.today()


@patch("recidiviz.ingest.direct.direct_ingest_control.GcsfsFactory.build")
@patch.object(
    PostgresDirectIngestRawFileMetadataManager,
    "has_raw_file_been_processed",
    lambda _, path: "skipped" in path.abs_path(),
)
@patch.object(
    PostgresDirectIngestRawFileMetadataManager,
    "has_raw_file_been_discovered",
    lambda _, path: "discovered" in path.abs_path(),
)
class TestUploadStateFilesToIngestBucketController(unittest.TestCase):
    """Tests for UploadStateFilesToIngestBucketController."""

    def setUp(self) -> None:
        self.project_id = "recidiviz-456"
        self.region = "us_xx"

        self.project_id_patcher = patch("recidiviz.utils.metadata.project_id")
        self.project_id_patcher.start().return_value = self.project_id

        self.operations_database_key = SQLAlchemyDatabaseKey.for_schema(
            SchemaType.OPERATIONS
        )
        fakes.use_in_memory_sqlite_database(self.operations_database_key)
        self.us_xx_primary_manager = (
            DirectIngestInstancePauseStatusManager.add_instance(
                self.region, DirectIngestInstance.PRIMARY, is_paused=False
            )
        )
        self.us_xx_secondary_manager = (
            DirectIngestInstancePauseStatusManager.add_instance(
                self.region, DirectIngestInstance.SECONDARY, is_paused=False
            )
        )

    def tearDown(self) -> None:
        fakes.teardown_in_memory_sqlite_databases()
        self.project_id_patcher.stop()

    def test_do_upload_succeeds(self, mock_fs_factory: Mock) -> None:
        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                )
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        expected_result = [
            "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt"
        ]
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertEqual(result.successes, expected_result)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(controller.skipped_files), 0)
        self.assertFalse(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())

    def test_do_upload_graceful_failures(
        self,
        mock_fs_factory: Mock,
    ) -> None:
        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                ),
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/non_existent_file.txt",
                    TODAY,
                ),
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertEqual(
            result.successes,
            ["recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt"],
        )
        self.assertEqual(
            result.failures,
            ["recidiviz-456-direct-ingest-state-us-xx/raw_data/non_existent_file.txt"],
        )
        self.assertEqual(len(controller.skipped_files), 0)
        self.assertFalse(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())

    def test_do_upload_sets_correct_content_type(
        self,
        mock_fs_factory: Mock,
    ) -> None:
        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.csv"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                ),
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.csv",
                    TODAY,
                ),
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertListEqual(
            sorted(result.successes),
            [
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.csv",
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
            ],
        )
        resulting_content_types = [file.content_type for file in mock_fs.files.values()]
        self.assertListEqual(
            sorted(resulting_content_types), ["text/csv", "text/plain"]
        )
        self.assertFalse(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())

    def test_get_paths_to_upload_is_correct(
        self,
        mock_fs_factory: Mock,
    ) -> None:
        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx",
                "raw_data/subdir1/test_file.txt",
            ),
            local_path=None,
        )
        mock_fs.test_add_path(
            path=GcsfsDirectoryPath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/subdir2/"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                ("recidiviz-456-direct-ingest-state-us-xx/raw_data/", TODAY),
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        result = [
            ("recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt", TODAY),
            (
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/subdir1/test_file.txt",
                TODAY,
            ),
        ]
        self.assertListEqual(result, controller.get_paths_to_upload())
        self.assertFalse(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())

    def test_skip_already_processed_or_discovered_files(
        self,
        mock_fs_factory: Mock,
    ) -> None:
        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.csv"
            ),
            local_path=None,
        )

        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx",
                "raw_data/skipped.csv",
            ),
            local_path=None,
        )
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx",
                "raw_data/discovered.csv",
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                ),
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.csv",
                    TODAY,
                ),
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/skipped.csv",
                    TODAY,
                ),
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/discovered.csv",
                    TODAY,
                ),
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertListEqual(
            result.successes,
            [
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.csv",
            ],
        )
        self.assertListEqual(
            result.skipped,
            [
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/skipped.csv",
                "recidiviz-456-direct-ingest-state-us-xx/raw_data/discovered.csv",
            ],
        )
        self.assertFalse(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())

    def test_do_upload_succeeds_ingest_was_paused(self, mock_fs_factory: Mock) -> None:
        self.us_xx_primary_manager.pause_instance()
        self.us_xx_secondary_manager.pause_instance()

        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                )
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        expected_result = [
            "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt"
        ]
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertEqual(result.successes, expected_result)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(controller.skipped_files), 0)
        self.assertTrue(self.us_xx_primary_manager.is_instance_paused())
        self.assertTrue(self.us_xx_secondary_manager.is_instance_paused())

    def test_do_upload_succeeds_ingest_was_paused_only_in_one_instance(
        self, mock_fs_factory: Mock
    ) -> None:
        self.us_xx_primary_manager.pause_instance()

        mock_fs = FakeGCSFileSystem()
        mock_fs.test_add_path(
            path=GcsfsFilePath.from_bucket_and_blob_name(
                "recidiviz-456-direct-ingest-state-us-xx", "raw_data/test_file.txt"
            ),
            local_path=None,
        )
        mock_fs_factory.return_value = mock_fs
        controller = UploadStateFilesToIngestBucketController(
            paths_with_timestamps=[
                (
                    "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt",
                    TODAY,
                )
            ],
            project_id="recidiviz-456",
            region_code="us_xx",
        )
        expected_result = [
            "recidiviz-456-direct-ingest-state-us-xx/raw_data/test_file.txt"
        ]
        result: MultiRequestResultWithSkipped[str, str, str] = controller.do_upload()
        self.assertEqual(result.successes, expected_result)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(controller.skipped_files), 0)
        self.assertTrue(self.us_xx_primary_manager.is_instance_paused())
        self.assertFalse(self.us_xx_secondary_manager.is_instance_paused())
