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
"""Legacy implementation of the ingest view file parser, which uses intermediate ingest
info objects and legacy ingest mappings files.
"""
# TODO(#8905): Delete everything in this file once we have fully migrated to the new
#  ingest mappings design.
import abc
import logging
from typing import Callable, Dict, List, Optional, Iterable

from recidiviz.common.constants.enum_overrides import EnumOverrides
from recidiviz.common.ingest_metadata import IngestMetadata
from recidiviz.common.io.contents_handle import ContentsHandle
from recidiviz.common.io.local_file_contents_handle import LocalFileContentsHandle
from recidiviz.ingest.direct.controllers.gcsfs_direct_ingest_utils import (
    ExtractAndMergeArgs,
)
from recidiviz.ingest.direct.controllers.ingest_view_processor import (
    IngestViewProcessor,
)
from recidiviz.ingest.direct.ingest_mappings.ingest_view_file_parser_delegate import (
    yaml_mappings_filepath,
)
from recidiviz.ingest.direct.legacy_ingest_mappings.state_shared_row_posthooks import (
    IngestGatingContext,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.ingest.direct.types.errors import (
    DirectIngestError,
    DirectIngestErrorType,
)
from recidiviz.ingest.extractor.csv_data_extractor import (
    CsvDataExtractor,
    IngestFieldCoordinates,
    RowType,
)
from recidiviz.ingest.models import ingest_info, serialization
from recidiviz.ingest.models.ingest_info import IngestInfo, IngestObject
from recidiviz.ingest.models.ingest_object_cache import IngestObjectCache
from recidiviz.persistence import persistence
from recidiviz.utils.regions import Region

IngestRowPrehookCallable = Callable[[IngestGatingContext, RowType], None]
IngestRowPosthookCallable = Callable[
    [IngestGatingContext, RowType, List[IngestObject], IngestObjectCache], None
]
IngestFilePostprocessorCallable = Callable[
    [IngestGatingContext, IngestInfo, Optional[IngestObjectCache]], None
]
IngestPrimaryKeyOverrideCallable = Callable[
    [IngestGatingContext, RowType], IngestFieldCoordinates
]
IngestAncestorChainOverridesCallable = Callable[
    [IngestGatingContext, RowType], Dict[str, str]
]


class LegacyIngestViewProcessorDelegate(metaclass=abc.ABCMeta):
    """Legacy implementation of the ingest view file parser, which uses intermediate ingest
    info objects and legacy ingest mappings files.
    """

    @abc.abstractmethod
    def get_enum_overrides(self) -> EnumOverrides:
        """Returns global enum overrides for legacy ingest mappings."""

    @abc.abstractmethod
    def get_row_pre_processors_for_file(
        self, _file_tag: str
    ) -> List[IngestRowPrehookCallable]:
        """Implementations should return row_pre_processors for a given
        file tag.
        """

    @abc.abstractmethod
    def get_row_post_processors_for_file(
        self, _file_tag: str
    ) -> List[IngestRowPosthookCallable]:
        """Implementations should return row_post_processors for a given
        file tag.
        """

    @abc.abstractmethod
    def get_file_post_processors_for_file(
        self, _file_tag: str
    ) -> List[IngestFilePostprocessorCallable]:
        """Implementations should return file_post_processors for a given
        file tag.
        """

    @abc.abstractmethod
    def get_ancestor_chain_overrides_callback_for_file(
        self, _file_tag: str
    ) -> Optional[IngestAncestorChainOverridesCallable]:
        """Implementations should return an
        ancestor_chain_overrides_callback for a given file tag.
        """

    @abc.abstractmethod
    def get_primary_key_override_for_file(
        self, _file_tag: str
    ) -> Optional[IngestPrimaryKeyOverrideCallable]:
        """Implementations should return a primary_key_override for a
        given file tag.
        """

    @abc.abstractmethod
    def get_files_to_set_with_empty_values(self) -> List[str]:
        """Implementations should return which files to set with empty
        values (see CsvDataExtractor).
        """


class LegacyIngestViewProcessor(IngestViewProcessor):
    """Legacy implementation of the ingest view file parser, which uses intermediate ingest
    info objects and legacy ingest mappings files.
    """

    def __init__(
        self,
        region: Region,
        ingest_instance: DirectIngestInstance,
        delegate: LegacyIngestViewProcessorDelegate,
    ):
        self.region = region
        self.ingest_instance = ingest_instance
        self.delegate = delegate

    def parse_and_persist_contents(
        self,
        args: ExtractAndMergeArgs,
        contents_handle: ContentsHandle,
        ingest_metadata: IngestMetadata,
    ) -> bool:
        ii = self._parse_ingest_info(args, contents_handle, ingest_metadata)
        if not ii:
            raise DirectIngestError(
                error_type=DirectIngestErrorType.PARSE_ERROR,
                msg="No IngestInfo after parse.",
            )

        logging.info("Successfully parsed data for ingest run [%s]", args.job_tag())

        ingest_info_proto = serialization.convert_ingest_info_to_proto(ii)

        logging.info(
            "Successfully converted ingest_info to proto for ingest run [%s]",
            args.job_tag(),
        )

        return persistence.write_ingest_info(ingest_info_proto, ingest_metadata)

    def _parse_ingest_info(
        self,
        args: ExtractAndMergeArgs,
        contents_handle: ContentsHandle,
        ingest_metadata: IngestMetadata,
    ) -> ingest_info.IngestInfo:
        """Parses ingest view file contents into an IngestInfo object."""
        file_tag = args.file_tag
        gating_context = IngestGatingContext(
            file_tag=file_tag, ingest_instance=self.ingest_instance
        )

        file_mapping = yaml_mappings_filepath(self.region, file_tag)

        row_pre_processors = self.delegate.get_row_pre_processors_for_file(file_tag)
        row_post_processors = self.delegate.get_row_post_processors_for_file(file_tag)
        file_post_processors = self.delegate.get_file_post_processors_for_file(file_tag)
        # pylint: disable=assignment-from-none
        primary_key_override_callback = self.delegate.get_primary_key_override_for_file(
            file_tag
        )
        # pylint: disable=assignment-from-none
        ancestor_chain_overrides_callback = (
            self.delegate.get_ancestor_chain_overrides_callback_for_file(file_tag)
        )
        should_set_with_empty_values = (
            gating_context.file_tag
            in self.delegate.get_files_to_set_with_empty_values()
        )

        data_extractor = CsvDataExtractor(
            file_mapping,
            gating_context,
            row_pre_processors,
            row_post_processors,
            file_post_processors,
            ancestor_chain_overrides_callback,
            primary_key_override_callback,
            ingest_metadata.system_level,
            should_set_with_empty_values,
        )

        contents_iterator: Iterable[str]
        if isinstance(contents_handle, LocalFileContentsHandle):
            contents_iterator = contents_handle.get_contents_iterator()
        else:
            # TODO(#9717): Add support for reading from a contents handle that pulls
            #  results from BigQuery.
            raise ValueError(
                f"Unsupported contents handle type: [{type(contents_handle)}]."
            )

        return data_extractor.extract_and_populate_data(contents_iterator)