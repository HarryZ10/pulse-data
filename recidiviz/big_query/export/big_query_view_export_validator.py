# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2020 Recidiviz, Inc.
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

"""Interface which validates the results of BigQuery view exports in specific formats."""

import abc

from recidiviz.cloud_storage.gcs_file_system import GCSFileSystem
from recidiviz.cloud_storage.gcsfs_path import GcsfsFilePath


class BigQueryViewExportValidator:
    """Interface for implementations which validate BigQuery view export results in specific formats."""

    def __init__(self, fs: GCSFileSystem):
        self.fs = fs

    @abc.abstractmethod
    def validate(self, path: GcsfsFilePath, allow_empty: bool) -> bool:
        """Validates whether the exported results are valid for presentation.

        Allow empty specifies whether an empty file is still valid. Some exporters
        (e.g. `ExistsBigQueryViewExportValidator`) will still return true for empty
        files even if allow_empty is False, but all exporters respect it when True."""


class ExistsBigQueryViewExportValidator(BigQueryViewExportValidator):
    """View validator which purely validates that a path exists."""

    def validate(self, path: GcsfsFilePath, allow_empty: bool) -> bool:
        return self.fs.exists(path)
