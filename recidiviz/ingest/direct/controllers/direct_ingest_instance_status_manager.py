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
"""A class that manages reading and updating DirectIngestInstanceStatuses."""
from recidiviz.ingest.direct.controllers.direct_ingest_instance import (
    DirectIngestInstance,
)
from recidiviz.persistence.database.schema.operations.schema import (
    DirectIngestInstanceStatus,
)
from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.session import Session
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.persistence.database.sqlalchemy_database_key import SQLAlchemyDatabaseKey
from recidiviz.utils import environment


class DirectIngestInstanceStatusManager:
    """An interface for reading and updating DirectIngestInstanceStatuses."""

    def __init__(self, region_code: str, ingest_instance: DirectIngestInstance):
        self.region_code = region_code.upper()
        self.ingest_instance = ingest_instance

        self.db_key = SQLAlchemyDatabaseKey.for_schema(SchemaType.OPERATIONS)

    def _get_status_using_session(self, session: Session) -> DirectIngestInstanceStatus:
        return (
            session.query(DirectIngestInstanceStatus)
            .filter(
                DirectIngestInstanceStatus.region_code == self.region_code,
                DirectIngestInstanceStatus.instance == self.ingest_instance.value,
            )
            .one()
        )

    def is_instance_paused(self) -> bool:
        session = SessionFactory.for_database(self.db_key)
        try:
            return self._get_status_using_session(session).is_paused
        finally:
            session.close()

    def pause_instance(self) -> None:
        session = SessionFactory.for_database(self.db_key)
        try:
            status = self._get_status_using_session(session)
            status.is_paused = True
            session.commit()
        finally:
            session.close()

    def unpause_instance(self) -> None:
        session = SessionFactory.for_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.OPERATIONS)
        )
        try:
            status = self._get_status_using_session(session)
            status.is_paused = False
            session.commit()
        finally:
            session.close()

    # This one specifically for test setup!
    @staticmethod
    @environment.test_only
    def add_instance(
        region_code: str, ingest_instance: DirectIngestInstance, is_paused: bool
    ) -> "DirectIngestInstanceStatusManager":
        session = SessionFactory.for_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.OPERATIONS)
        )
        try:
            session.add(
                DirectIngestInstanceStatus(
                    region_code=region_code.upper(),
                    instance=ingest_instance.value,
                    is_paused=is_paused,
                )
            )
            session.commit()
        finally:
            session.close()

        return DirectIngestInstanceStatusManager(region_code, ingest_instance)