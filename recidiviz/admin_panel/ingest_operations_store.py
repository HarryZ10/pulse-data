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
"""Store used to keep information related to direct ingest operations"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from google.cloud import tasks_v2

from recidiviz.admin_panel.admin_panel_store import AdminPanelStore
from recidiviz.big_query.big_query_client import BigQueryClientImpl
from recidiviz.cloud_storage.gcsfs_factory import GcsfsFactory
from recidiviz.cloud_storage.gcsfs_path import GcsfsFilePath
from recidiviz.common.constants.operations.direct_ingest_instance_status import (
    DirectIngestStatus,
)
from recidiviz.common.constants.states import StateCode
from recidiviz.ingest.direct.direct_ingest_cloud_task_manager import (
    DirectIngestCloudTaskManagerImpl,
    get_direct_ingest_queues_for_state,
)
from recidiviz.ingest.direct.gcs.direct_ingest_gcs_file_system import (
    DirectIngestGCSFileSystem,
)
from recidiviz.ingest.direct.gcs.directory_path_utils import (
    gcsfs_direct_ingest_bucket_for_state,
    gcsfs_direct_ingest_storage_directory_path_for_state,
)
from recidiviz.ingest.direct.ingest_view_materialization.instance_ingest_view_contents import (
    InstanceIngestViewContentsImpl,
)
from recidiviz.ingest.direct.metadata.direct_ingest_instance_pause_status_manager import (
    DirectIngestInstancePauseStatusManager,
)
from recidiviz.ingest.direct.metadata.direct_ingest_instance_status_manager import (
    DirectIngestInstanceStatusManager,
)
from recidiviz.ingest.direct.metadata.direct_ingest_view_materialization_metadata_manager import (
    DirectIngestViewMaterializationMetadataManager,
)
from recidiviz.ingest.direct.metadata.postgres_direct_ingest_file_metadata_manager import (
    PostgresDirectIngestRawFileMetadataManager,
)
from recidiviz.ingest.direct.regions.direct_ingest_region_utils import (
    get_direct_ingest_states_launched_in_env,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.utils import metadata
from recidiviz.utils.regions import get_region

_TASK_LOCATION = "us-east1"

QUEUE_STATE_ENUM = tasks_v2.enums.Queue.State

BucketSummaryType = Dict[str, Union[str, int]]


class IngestOperationsStore(AdminPanelStore):
    """
    A store for tracking the current state of direct ingest.
    """

    def __init__(self) -> None:
        self.fs = DirectIngestGCSFileSystem(GcsfsFactory.build())
        self.cloud_task_manager = DirectIngestCloudTaskManagerImpl()
        self.cloud_tasks_client = tasks_v2.CloudTasksClient()

    def recalculate_store(self) -> None:
        # This store currently does not store any internal state that can be refreshed.
        # Data must be fetched manually from other public methods.
        pass

    @property
    def state_codes_launched_in_env(self) -> List[StateCode]:
        return get_direct_ingest_states_launched_in_env()

    @staticmethod
    def get_queues_for_region(state_code: StateCode) -> List[str]:
        """Returns the list of formatted direct ingest queues for given state"""
        return sorted(get_direct_ingest_queues_for_state(state_code))

    def trigger_task_scheduler(self, state_code: StateCode, instance_str: str) -> None:
        """This function creates a cloud task to schedule the next job for a given state code and instance.
        Requires:
        - state_code: (required) State code to start ingest for (i.e. "US_ID")
        - instance: (required) Which instance to start ingest for (either PRIMARY or SECONDARY)
        """
        try:
            instance = DirectIngestInstance[instance_str]
        except KeyError as e:
            logging.error("Received an invalid instance: %s.", instance_str)
            raise ValueError(
                f"Invalid instance [{instance_str}] received",
            ) from e

        can_start_ingest = state_code in self.state_codes_launched_in_env

        formatted_state_code = state_code.value.lower()
        region = get_region(formatted_state_code, is_direct_ingest=True)

        logging.info(
            "Creating cloud task to schedule next job and kick ingest for %s instance in %s.",
            instance,
            formatted_state_code,
        )
        self.cloud_task_manager.create_direct_ingest_handle_new_files_task(
            region=region,
            ingest_instance=instance,
            can_start_ingest=can_start_ingest,
        )

    def update_ingest_queues_state(
        self, state_code: StateCode, new_queue_state: str
    ) -> None:
        """This function is called through the Ingest Operations UI in the admin panel.
        It updates the state of the following queues by either pausing or resuming the
        queues:
         - direct-ingest-state-<region_code>-extract-and-merge
         - direct-ingest-state-<region_code>-extract-and-merge-queue-secondary
         - direct-ingest-state-<region_code>-scheduler
         - direct-ingest-state-<region_code>-scheduler-secondary
         - direct-ingest-state-<region_code>-raw-data-import
         - direct-ingest-state-<region_code>-raw-data-import-secondary
         - direct-ingest-state-<region_code>-materialize-ingest-view
         - direct-ingest-state-<region_code>-materialize-ingest-view-secondary
         - direct-ingest-state-<region_code>-sftp-queue    (for select regions)

        Requires:
        - state_code: (required) State code to pause queues for
        - new_state: (required) Either 'PAUSED' or 'RUNNING'
        """
        queues_to_update = self.get_queues_for_region(state_code)

        if new_queue_state not in [
            QUEUE_STATE_ENUM.RUNNING.name,
            QUEUE_STATE_ENUM.PAUSED.name,
        ]:
            logging.error(
                "Received an invalid queue state: %s. This method should only be used "
                "to update queue states to PAUSED or RUNNING",
                new_queue_state,
            )
            raise ValueError(
                f"Invalid queue state [{new_queue_state}] received",
            )

        for queue in queues_to_update:
            queue_path = self.cloud_tasks_client.queue_path(
                metadata.project_id(), _TASK_LOCATION, queue
            )

            if new_queue_state == QUEUE_STATE_ENUM.PAUSED.name:
                logging.info("Pausing queue: %s", new_queue_state)
                self.cloud_tasks_client.pause_queue(name=queue_path)
            else:
                logging.info("Resuming queue: %s", new_queue_state)
                self.cloud_tasks_client.resume_queue(name=queue_path)

    def get_ingest_queue_states(self, state_code: StateCode) -> List[Dict[str, str]]:
        """Returns a list of dictionaries that contain the name and states of direct ingest queues for a given region"""
        ingest_queue_states: List[Dict[str, str]] = []
        queues_to_update = self.get_queues_for_region(state_code)

        for queue_name in queues_to_update:
            queue_path = self.cloud_tasks_client.queue_path(
                metadata.project_id(), _TASK_LOCATION, queue_name
            )
            queue = self.cloud_tasks_client.get_queue(name=queue_path)
            queue_state = {
                "name": queue_name,
                "state": QUEUE_STATE_ENUM(queue.state).name,
            }
            ingest_queue_states.append(queue_state)

        return ingest_queue_states

    def get_ingest_instance_summary(
        self, state_code: StateCode, ingest_instance: DirectIngestInstance
    ) -> Dict[str, Any]:
        """Returns a dictionary containing the following info for the provided instance:
        i.e. {
            instance: the direct ingest instance,
            dbName: database name for this instance,
            storageDirectoryPath: storage directory absolute path,
            ingestBucketPath: ingest bucket path,
            ingestBucketNumFiles: number of files of any kind in the ingest bucket,
            operations: dictionary with metadata from the operations DB
        }
        """
        formatted_state_code = state_code.value.lower()

        # Get the ingest bucket path
        ingest_bucket_path = gcsfs_direct_ingest_bucket_for_state(
            region_code=formatted_state_code,
            ingest_instance=ingest_instance,
            project_id=metadata.project_id(),
        )

        files_in_bucket = [
            p
            for p in self.fs.ls_with_blob_prefix(
                bucket_name=ingest_bucket_path.bucket_name, blob_prefix=""
            )
            if isinstance(p, GcsfsFilePath)
        ]
        num_files_in_bucket = len(files_in_bucket)

        # Get the storage bucket for this instance
        storage_bucket_path = gcsfs_direct_ingest_storage_directory_path_for_state(
            region_code=formatted_state_code,
            ingest_instance=ingest_instance,
            project_id=metadata.project_id(),
        )

        # Get the database name corresponding to this instance
        ingest_db_name = ingest_instance.database_key_for_state(state_code).db_name

        # Get the operations metadata for this ingest instance
        operations_db_metadata = self._get_operations_db_metadata(
            state_code, ingest_instance
        )

        logging.info("Done getting instance summary for [%s]", ingest_instance.value)
        return {
            "instance": ingest_instance.value,
            "storageDirectoryPath": storage_bucket_path.abs_path(),
            "ingestBucketPath": ingest_bucket_path.abs_path(),
            "ingestBucketNumFiles": num_files_in_bucket,
            "dbName": ingest_db_name,
            "operations": operations_db_metadata,
        }

    @staticmethod
    def _get_operations_db_metadata(
        state_code: StateCode, ingest_instance: DirectIngestInstance
    ) -> Dict[
        str,
        Union[
            int,
            Optional[datetime],
            List[Dict[str, Union[Optional[str], int]]],
        ],
    ]:
        """Returns the following dictionary with information about the operations
        database for the state:
        {
            isPaused: <bool>
            unprocessedFilesRaw: <int>
            processedFilesRaw: <int>
            dateOfEarliestUnprocessedIngestView: <datetime>
            ingestViewMaterializationSummaries: [
                {
                    ingestViewName: <str>
                    numPendingJobs: <int>
                    numCompletedJobs: <int>
                    completedJobsMaxDatetime: <datetime>
                    pendingJobsMinDatetime: <datetime>
                }
            ]
        }
        """
        logging.info(
            "Getting operations DB metadata for instance [%s]", ingest_instance.value
        )
        raw_file_metadata_manager = PostgresDirectIngestRawFileMetadataManager(
            region_code=state_code.value,
            # TODO(#12794): Change to be based on the instance the raw file is processed in once we can ingest in
            # multiple instances.
            raw_data_instance=DirectIngestInstance.PRIMARY,
        )

        if ingest_instance == DirectIngestInstance.PRIMARY:
            logging.info(
                "Getting unprocessed raw files for instance [%s]", ingest_instance.value
            )
            num_unprocessed_raw_files = (
                raw_file_metadata_manager.get_num_unprocessed_raw_files()
            )
            logging.info(
                "Getting processed raw files for instance [%s]", ingest_instance.value
            )
            num_processed_raw_files = (
                raw_file_metadata_manager.get_num_processed_raw_files()
            )
        elif ingest_instance == DirectIngestInstance.SECONDARY:
            # TODO(##12387): Raw files are currently processed in the primary instance
            #  only, not secondary. This logic will need to change once we enable
            #  raw data imports in secondary.
            num_unprocessed_raw_files = 0
            num_processed_raw_files = 0
        else:
            raise ValueError(f"Unexpected ingest instance: [{ingest_instance}]")

        ingest_instance_status_manager = DirectIngestInstancePauseStatusManager(
            state_code.value, ingest_instance
        )
        logging.info("Checking is instance [%s] paused", ingest_instance.value)
        is_paused = ingest_instance_status_manager.is_instance_paused()

        logging.info(
            "Getting instance [%s] ingest view materialization summaries",
            ingest_instance.value,
        )
        materialization_job_summaries = DirectIngestViewMaterializationMetadataManager(
            state_code.value, ingest_instance
        ).get_instance_summaries()

        ingest_view_contents = InstanceIngestViewContentsImpl(
            big_query_client=BigQueryClientImpl(),
            region_code=state_code.value,
            ingest_instance=ingest_instance,
            dataset_prefix=None,
        )
        logging.info(
            "Getting instance [%s] ingest view contents summaries",
            ingest_instance.value,
        )
        contents_summaries = [
            ingest_view_contents.get_ingest_view_contents_summary(ingest_view_name)
            for ingest_view_name, summary in materialization_job_summaries.items()
        ]

        logging.info(
            "Done getting operations DB metadata for instance [%s]",
            ingest_instance.value,
        )
        return {
            "isPaused": is_paused,
            "unprocessedFilesRaw": num_unprocessed_raw_files,
            "processedFilesRaw": num_processed_raw_files,
            "ingestViewMaterializationSummaries": [
                summary.as_api_dict()
                for summary in materialization_job_summaries.values()
            ],
            "ingestViewContentsSummaries": [
                summary.as_api_dict()
                for summary in contents_summaries
                if summary is not None
            ],
        }

    def get_all_current_ingest_instance_statuses(
        self,
    ) -> Dict[StateCode, Dict[DirectIngestInstance, Optional[DirectIngestStatus]]]:
        """Returns the current status of each ingest instance for states in the given project."""

        ingest_statuses = {}
        for state_code in get_direct_ingest_states_launched_in_env():
            instance_to_status_dict = {}
            for i_instance in DirectIngestInstance:  # new direct ingest instance
                status_manager = DirectIngestInstanceStatusManager(
                    region_code=state_code.value, ingest_instance=i_instance
                )
                curr_status = status_manager.get_current_status()

                instance_to_status_dict[i_instance] = curr_status

            ingest_statuses[state_code] = instance_to_status_dict

        return ingest_statuses
