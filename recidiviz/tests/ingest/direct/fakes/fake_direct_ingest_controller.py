# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2022 Recidiviz, Inc.
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
"""Helpers for building a test-only version of the BaseDirectIngestController."""
from types import ModuleType
from typing import Dict, List, Type

import attr
from mock import Mock, patch

from recidiviz.big_query.big_query_client import BigQueryClient
from recidiviz.big_query.big_query_view_collector import BigQueryViewCollector
from recidiviz.cloud_storage.gcsfs_csv_reader import GcsfsCsvReader
from recidiviz.cloud_storage.gcsfs_factory import GcsfsFactory
from recidiviz.cloud_storage.gcsfs_path import (
    GcsfsBucketPath,
    GcsfsDirectoryPath,
    GcsfsFilePath,
)
from recidiviz.common.ingest_metadata import SystemLevel
from recidiviz.ingest.direct.controllers.base_direct_ingest_controller import (
    BaseDirectIngestController,
)
from recidiviz.ingest.direct.controllers.direct_ingest_gcs_file_system import (
    DirectIngestGCSFileSystem,
)
from recidiviz.ingest.direct.controllers.gcsfs_direct_ingest_utils import (
    gcsfs_direct_ingest_bucket_for_region,
)
from recidiviz.ingest.direct.raw_data import direct_ingest_raw_table_migration_collector
from recidiviz.ingest.direct.raw_data.direct_ingest_raw_file_import_manager import (
    DirectIngestRawFileConfig,
    DirectIngestRawFileImportManager,
    DirectIngestRegionRawFileConfig,
    RawTableColumnInfo,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.ingest.direct.views.direct_ingest_big_query_view_types import (
    DirectIngestPreProcessedIngestViewBuilder,
)
from recidiviz.ingest.direct.views.direct_ingest_view_collector import (
    DirectIngestPreProcessedIngestViewCollector,
)
from recidiviz.persistence.entity.operations.entities import DirectIngestRawFileMetadata
from recidiviz.tests.cloud_storage.fake_gcs_file_system import (
    FakeGCSFileSystem,
    FakeGCSFileSystemDelegate,
)
from recidiviz.tests.ingest.direct import fake_regions as fake_regions_module
from recidiviz.tests.ingest.direct.fakes.fake_async_direct_ingest_cloud_task_manager import (
    FakeAsyncDirectIngestCloudTaskManager,
)
from recidiviz.tests.ingest.direct.fakes.fake_direct_ingest_big_query_client import (
    FakeDirectIngestBigQueryClient,
)
from recidiviz.tests.ingest.direct.fakes.fake_synchronous_direct_ingest_cloud_task_manager import (
    FakeSynchronousDirectIngestCloudTaskManager,
)
from recidiviz.utils import metadata
from recidiviz.utils.regions import Region


class DirectIngestFakeGCSFileSystemDelegate(FakeGCSFileSystemDelegate):
    def __init__(self, controller: BaseDirectIngestController, can_start_ingest: bool):
        self.controller = controller
        self.can_start_ingest = can_start_ingest

    def on_file_added(self, path: GcsfsFilePath) -> None:
        if path.abs_path().startswith(self.controller.ingest_bucket_path.abs_path()):
            self.controller.handle_file(path, start_ingest=self.can_start_ingest)


@attr.s
class FakeDirectIngestRegionRawFileConfig(DirectIngestRegionRawFileConfig):
    def _get_raw_data_file_configs(self) -> Dict[str, DirectIngestRawFileConfig]:
        return {
            "tagA": DirectIngestRawFileConfig(
                file_tag="tagA",
                file_path="path/to/tagA.yaml",
                file_description="file description",
                primary_key_cols=["mockKey"],
                columns=[
                    RawTableColumnInfo(
                        name="mockKey",
                        description="mockKey description",
                        is_datetime=False,
                    )
                ],
                supplemental_order_by_clause="",
                encoding="UTF-8",
                separator=",",
                custom_line_terminator=None,
                ignore_quotes=False,
                always_historical_export=False,
            ),
            "tagB": DirectIngestRawFileConfig(
                file_tag="tagB",
                file_path="path/to/tagB.yaml",
                file_description="file description",
                primary_key_cols=["mockKey"],
                columns=[
                    RawTableColumnInfo(
                        name="mockKey",
                        description="mockKey description",
                        is_datetime=False,
                    )
                ],
                supplemental_order_by_clause="",
                encoding="UTF-8",
                separator=",",
                custom_line_terminator=None,
                ignore_quotes=False,
                always_historical_export=False,
            ),
            "tagC": DirectIngestRawFileConfig(
                file_tag="tagC",
                file_path="path/to/tagC.yaml",
                file_description="file description",
                primary_key_cols=["mockKey"],
                columns=[
                    RawTableColumnInfo(
                        name="mockKey",
                        description="mockKey description",
                        is_datetime=False,
                    )
                ],
                supplemental_order_by_clause="",
                encoding="UTF-8",
                separator=",",
                custom_line_terminator=None,
                ignore_quotes=False,
                always_historical_export=False,
            ),
            "tagWeDoNotIngest": DirectIngestRawFileConfig(
                file_tag="tagWeDoNotIngest",
                file_path="path/to/tagWeDoNotIngest.yaml",
                file_description="file description",
                primary_key_cols=[],
                columns=[],
                supplemental_order_by_clause="",
                encoding="UTF-8",
                separator=",",
                custom_line_terminator=None,
                ignore_quotes=False,
                always_historical_export=False,
            ),
        }


class FakeDirectIngestRawFileImportManager(DirectIngestRawFileImportManager):
    """Fake implementation of DirectIngestRawFileImportManager for tests."""

    def __init__(
        self,
        *,
        region: Region,
        fs: DirectIngestGCSFileSystem,
        ingest_bucket_path: GcsfsBucketPath,
        temp_output_directory_path: GcsfsDirectoryPath,
        big_query_client: BigQueryClient,
    ):
        super().__init__(
            region=region,
            fs=fs,
            ingest_bucket_path=ingest_bucket_path,
            temp_output_directory_path=temp_output_directory_path,
            big_query_client=big_query_client,
            region_raw_file_config=FakeDirectIngestRegionRawFileConfig(
                region.region_code
            ),
        )
        self.imported_paths: List[GcsfsFilePath] = []

    def import_raw_file_to_big_query(
        self, path: GcsfsFilePath, file_metadata: DirectIngestRawFileMetadata
    ) -> None:
        self.imported_paths.append(path)


class FakeDirectIngestPreProcessedIngestViewCollector(
    DirectIngestPreProcessedIngestViewCollector
):
    def __init__(self, region: Region, controller_tag_rank_list: List[str]):
        super().__init__(region, controller_tag_rank_list)

    def collect_view_builders(self) -> List[DirectIngestPreProcessedIngestViewBuilder]:
        builders = [
            DirectIngestPreProcessedIngestViewBuilder(
                region=self.region.region_code,
                ingest_view_name=tag,
                view_query_template=f"SELECT * FROM {{{tag}}}",
                order_by_cols="",
            )
            for tag in self.controller_tag_rank_list
        ]

        builders.append(
            DirectIngestPreProcessedIngestViewBuilder(
                ingest_view_name="gatedTagNotInTagsList",
                region=self.region.region_code,
                view_query_template="SELECT * FROM {tagA} LEFT OUTER JOIN {tagB} USING (col);",
                order_by_cols="",
            )
        )

        return builders


@patch("recidiviz.utils.metadata.project_id", Mock(return_value="recidiviz-staging"))
def build_fake_direct_ingest_controller(
    controller_cls: Type[BaseDirectIngestController],
    ingest_instance: DirectIngestInstance,
    run_async: bool,
    can_start_ingest: bool = True,
    regions_module: ModuleType = fake_regions_module,
) -> BaseDirectIngestController:
    """Builds an instance of |controller_cls| for use in tests with several internal
    classes mocked properly.
    """
    fake_fs = FakeGCSFileSystem()

    def mock_build_fs() -> FakeGCSFileSystem:
        return fake_fs

    if "TestDirectIngestController" in controller_cls.__name__:
        view_collector_cls: Type[
            BigQueryViewCollector
        ] = FakeDirectIngestPreProcessedIngestViewCollector
    else:
        view_collector_cls = DirectIngestPreProcessedIngestViewCollector

    with patch(
        f"{BaseDirectIngestController.__module__}.DirectIngestCloudTaskManagerImpl"
    ) as mock_task_factory_cls, patch(
        f"{BaseDirectIngestController.__module__}.BigQueryClientImpl"
    ) as mock_big_query_client_cls, patch(
        f"{BaseDirectIngestController.__module__}.DirectIngestRawFileImportManager",
        FakeDirectIngestRawFileImportManager,
    ), patch(
        f"{BaseDirectIngestController.__module__}.DirectIngestPreProcessedIngestViewCollector",
        view_collector_cls,
    ):
        task_manager = (
            FakeAsyncDirectIngestCloudTaskManager()
            if run_async
            else FakeSynchronousDirectIngestCloudTaskManager()
        )
        mock_task_factory_cls.return_value = task_manager
        mock_big_query_client_cls.return_value = FakeDirectIngestBigQueryClient(
            project_id=metadata.project_id(),
            fs=fake_fs,
            region_code=controller_cls.region_code(),
        )
        with patch.object(GcsfsFactory, "build", new=mock_build_fs):
            with patch.object(
                direct_ingest_raw_table_migration_collector,
                "regions",
                new=regions_module,
            ):
                controller = controller_cls(
                    ingest_bucket_path=gcsfs_direct_ingest_bucket_for_region(
                        region_code=controller_cls.region_code(),
                        system_level=SystemLevel.for_region_code(
                            controller_cls.region_code(),
                            is_direct_ingest=True,
                        ),
                        ingest_instance=ingest_instance,
                        project_id="recidiviz-xxx",
                    )
                )
                controller.csv_reader = GcsfsCsvReader(fake_fs)
                controller.raw_file_import_manager.csv_reader = controller.csv_reader

                task_manager.set_controller(controller)
                fake_fs.test_set_delegate(
                    DirectIngestFakeGCSFileSystemDelegate(
                        controller, can_start_ingest=can_start_ingest
                    )
                )
                return controller