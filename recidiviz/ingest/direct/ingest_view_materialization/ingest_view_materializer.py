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
"""Class that manages logic related to materializing ingest views for a region so
the results can be processed and merged into our Postgres database.
"""
import datetime
import logging
from typing import Dict, Generic, List, Optional, Tuple

from google.cloud import bigquery

from recidiviz.big_query.big_query_client import BigQueryClient
from recidiviz.big_query.big_query_view_collector import BigQueryViewCollector
from recidiviz.big_query.view_update_manager import (
    TEMP_DATASET_DEFAULT_TABLE_EXPIRATION_MS,
)
from recidiviz.ingest.direct.ingest_view_materialization.ingest_view_materialization_args_generator_delegate import (
    IngestViewMaterializationArgsT,
)
from recidiviz.ingest.direct.ingest_view_materialization.ingest_view_materializer_delegate import (
    IngestViewMaterializerDelegate,
    ingest_view_materialization_temp_dataset,
)
from recidiviz.ingest.direct.types.cloud_task_args import (
    GcsfsIngestViewExportArgs,
    IngestViewMaterializationArgs,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.ingest.direct.views.direct_ingest_big_query_view_types import (
    DestinationTableType,
    DirectIngestPreProcessedIngestView,
    DirectIngestPreProcessedIngestViewBuilder,
    RawTableViewType,
)
from recidiviz.ingest.direct.views.direct_ingest_view_collector import (
    DirectIngestPreProcessedIngestViewCollector,
)
from recidiviz.utils import regions
from recidiviz.utils.environment import GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override
from recidiviz.utils.regions import Region
from recidiviz.utils.string import StrictStringFormatter

UPDATE_TIMESTAMP_PARAM_NAME = "update_timestamp"
UPPER_BOUND_TIMESTAMP_PARAM_NAME = "update_timestamp_upper_bound_inclusive"
LOWER_BOUND_TIMESTAMP_PARAM_NAME = "update_timestamp_lower_bound_exclusive"
SELECT_SUBQUERY = "SELECT * FROM `{project_id}.{dataset_id}.{table_name}`;"
TABLE_NAME_DATE_FORMAT = "%Y_%m_%d_%H_%M_%S"


class IngestViewMaterializer(Generic[IngestViewMaterializationArgsT]):
    """Class that manages logic related to materializing ingest views for a region so
    the results can be processed and merged into our Postgres database.
    """

    def __init__(
        self,
        *,
        region: Region,
        ingest_instance: DirectIngestInstance,
        delegate: IngestViewMaterializerDelegate[IngestViewMaterializationArgsT],
        big_query_client: BigQueryClient,
        view_collector: BigQueryViewCollector[
            DirectIngestPreProcessedIngestViewBuilder
        ],
        launched_ingest_views: List[str],
    ):

        self.region = region
        self.delegate = delegate
        self.ingest_instance = ingest_instance
        self.big_query_client = big_query_client
        self.ingest_views_by_name = {
            builder.ingest_view_name: builder.build()
            for builder in view_collector.collect_view_builders()
            if builder.ingest_view_name in launched_ingest_views
        }

    def _generate_export_job_for_date(
        self,
        table_name: str,
        ingest_view: DirectIngestPreProcessedIngestView,
        date_bound: datetime.datetime,
    ) -> bigquery.QueryJob:
        """Generates a query for the provided |ingest view| on the given |date bound| and starts a job to load the
        results of that query into the provided |table_name|. Returns the potentially in progress QueryJob to the
        caller.
        """
        query, query_params = self._generate_export_query_and_params_for_date(
            ingest_view=ingest_view,
            ingest_instance=self.ingest_instance,
            destination_table_type=DestinationTableType.PERMANENT_EXPIRING,
            destination_table_id=table_name,
            update_timestamp=date_bound,
        )

        logging.info(
            "Generated bound query with params \nquery: [%s]\nparams: [%s]",
            query,
            query_params,
        )

        self.big_query_client.create_dataset_if_necessary(
            dataset_ref=self.big_query_client.dataset_ref_for_id(
                ingest_view_materialization_temp_dataset(
                    ingest_view, self.ingest_instance
                )
            ),
            default_table_expiration_ms=TEMP_DATASET_DEFAULT_TABLE_EXPIRATION_MS,
        )
        query_job = self.big_query_client.run_query_async(
            query_str=query, query_parameters=query_params
        )
        return query_job

    @staticmethod
    def _create_date_diff_query(
        upper_bound_query: str, upper_bound_prev_query: str, do_reverse_date_diff: bool
    ) -> str:
        """Provided the given |upper_bound_query| and |upper_bound_prev_query| returns a query which will return the
        delta between those two queries. The ordering of the comparison depends on the provided |do_reverse_date_diff|.
        """
        main_query, filter_query = (
            (upper_bound_prev_query, upper_bound_query)
            if do_reverse_date_diff
            else (upper_bound_query, upper_bound_prev_query)
        )
        filter_query = filter_query.rstrip().rstrip(";")
        main_query = main_query.rstrip().rstrip(";")
        query = f"(\n{main_query}\n) EXCEPT DISTINCT (\n{filter_query}\n);"
        return query

    @staticmethod
    def _get_upper_bound_intermediate_table_name(
        ingest_view_export_args: IngestViewMaterializationArgs,
    ) -> str:
        """Returns name of the intermediate table that will store data for the view query with a date bound equal to the
        upper_bound_datetime_to_export in the args.
        """
        return (
            f"{ingest_view_export_args.ingest_view_name}_"
            f"{ingest_view_export_args.upper_bound_datetime_to_export.strftime(TABLE_NAME_DATE_FORMAT)}_"
            f"upper_bound"
        )

    @staticmethod
    def _get_lower_bound_intermediate_table_name(
        ingest_view_export_args: IngestViewMaterializationArgs,
    ) -> str:
        """Returns name of the intermediate table that will store data for the view query with a date bound equal to the
        upper_bound_datetime_prev in the args.

        Throws if the args have a null upper_bound_datetime_prev.
        """
        if not ingest_view_export_args.upper_bound_datetime_prev:
            raise ValueError(
                f"Expected nonnull upper_bound_datetime_prev for args: {ingest_view_export_args}"
            )
        return (
            f"{ingest_view_export_args.ingest_view_name}_"
            f"{ingest_view_export_args.upper_bound_datetime_prev.strftime(TABLE_NAME_DATE_FORMAT)}_"
            f"lower_bound"
        )

    def _get_export_query_for_args(
        self, ingest_view_export_args: IngestViewMaterializationArgs
    ) -> str:
        """Returns a query to export the ingest view with date bounds specified in the provided args. This query will
        only work if the intermediate tables have been exported via the
        _load_individual_date_queries_into_intermediate_tables function.
        """
        ingest_view = self.ingest_views_by_name[
            ingest_view_export_args.ingest_view_name
        ]
        export_query = StrictStringFormatter().format(
            SELECT_SUBQUERY,
            project_id=self.big_query_client.project_id,
            dataset_id=ingest_view_materialization_temp_dataset(
                ingest_view, self.ingest_instance
            ),
            table_name=self._get_upper_bound_intermediate_table_name(
                ingest_view_export_args
            ),
        )

        if ingest_view_export_args.upper_bound_datetime_prev:

            upper_bound_prev_query = StrictStringFormatter().format(
                SELECT_SUBQUERY,
                project_id=self.big_query_client.project_id,
                dataset_id=ingest_view_materialization_temp_dataset(
                    ingest_view, self.ingest_instance
                ),
                table_name=self._get_lower_bound_intermediate_table_name(
                    ingest_view_export_args
                ),
            )
            export_query = IngestViewMaterializer._create_date_diff_query(
                upper_bound_query=export_query,
                upper_bound_prev_query=upper_bound_prev_query,
                do_reverse_date_diff=ingest_view.do_reverse_date_diff,
            )

        if not isinstance(ingest_view_export_args, GcsfsIngestViewExportArgs):
            # TODO(#9717): Augment query logic here to add appropriate metadata columns
            #  (should probably do that inside a new delegate method?)
            raise ValueError(f"Unexpected args type [{type(ingest_view_export_args)}]")

        return DirectIngestPreProcessedIngestView.add_order_by_suffix(
            query=export_query, order_by_cols=ingest_view.order_by_cols
        )

    def _load_individual_date_queries_into_intermediate_tables(
        self, ingest_view_export_args: IngestViewMaterializationArgs
    ) -> None:
        """Loads query results from the upper and lower bound queries for this export job into intermediate tables."""

        ingest_view = self.ingest_views_by_name[
            ingest_view_export_args.ingest_view_name
        ]

        single_date_table_export_jobs = []

        upper_bound_table_job = self._generate_export_job_for_date(
            table_name=self._get_upper_bound_intermediate_table_name(
                ingest_view_export_args
            ),
            ingest_view=ingest_view,
            date_bound=ingest_view_export_args.upper_bound_datetime_to_export,
        )
        single_date_table_export_jobs.append(upper_bound_table_job)

        if ingest_view_export_args.upper_bound_datetime_prev:
            lower_bound_table_job = self._generate_export_job_for_date(
                table_name=self._get_lower_bound_intermediate_table_name(
                    ingest_view_export_args
                ),
                ingest_view=ingest_view,
                date_bound=ingest_view_export_args.upper_bound_datetime_prev,
            )
            single_date_table_export_jobs.append(lower_bound_table_job)

        # Wait for completion of all async date queries
        for export_job in single_date_table_export_jobs:
            export_job.result()

    def _delete_intermediate_tables(
        self, ingest_view_export_args: IngestViewMaterializationArgs
    ) -> None:
        ingest_view = self.ingest_views_by_name[
            ingest_view_export_args.ingest_view_name
        ]

        single_date_table_ids = [
            self._get_upper_bound_intermediate_table_name(ingest_view_export_args)
        ]
        if ingest_view_export_args.upper_bound_datetime_prev:
            single_date_table_ids.append(
                self._get_lower_bound_intermediate_table_name(ingest_view_export_args)
            )

        for table_id in single_date_table_ids:
            self.big_query_client.delete_table(
                dataset_id=ingest_view_materialization_temp_dataset(
                    ingest_view, self.ingest_instance
                ),
                table_id=table_id,
            )
            logging.info("Deleted intermediate table [%s]", table_id)

    def export_view_for_args(
        self, ingest_view_export_args: IngestViewMaterializationArgsT
    ) -> bool:
        """Performs an Cloud Storage export of a single ingest view with date bounds specified in the provided args. If
        the provided args contain an upper and lower bound date, the exported view contains only the delta between the
        two dates. If only the upper bound is provided, then the exported view contains historical results up until the
        bound date.

        Note: In order to prevent resource exhaustion in BigQuery, the ultimate query in this method is broken down
        into distinct parts. This method first persists the results of historical queries for each given bound date
        (upper and lower) into temporary tables. The delta between those tables is then queried separately using
        SQL's `EXCEPT DISTINCT` and those final results are exported to Cloud Storage.
        """
        if not self.region.is_ingest_launched_in_env():
            raise ValueError(
                f"Ingest not enabled for region [{self.region.region_code}]"
            )

        job_completion_time = self.delegate.get_job_completion_time_for_args(
            ingest_view_export_args
        )
        if job_completion_time:
            logging.warning(
                "Already materialized view for args [%s] - returning.",
                ingest_view_export_args,
            )
            return False

        self.delegate.prepare_for_job(ingest_view_export_args)

        ingest_view = self.ingest_views_by_name[
            ingest_view_export_args.ingest_view_name
        ]

        if (
            ingest_view.do_reverse_date_diff
            and not ingest_view_export_args.upper_bound_datetime_prev
        ):
            raise ValueError(
                f"Attempting to process reverse date diff view "
                f"[{ingest_view.ingest_view_name}] with no lower bound date."
            )

        logging.info(
            "Start loading results of individual date queries into intermediate tables."
        )
        self._load_individual_date_queries_into_intermediate_tables(
            ingest_view_export_args
        )
        logging.info(
            "Completed loading results of individual date queries into intermediate tables."
        )

        export_query = self._get_export_query_for_args(ingest_view_export_args)

        logging.info("Generated final export query [%s]", str(export_query))

        self.delegate.materialize_query_results(
            ingest_view_export_args, ingest_view, export_query
        )

        logging.info("Deleting intermediate tables.")
        self._delete_intermediate_tables(ingest_view_export_args)
        logging.info("Done deleting intermediate tables.")

        self.delegate.mark_job_complete(ingest_view_export_args)

        return True

    @classmethod
    def debug_query_for_args(
        cls,
        ingest_views_by_name: Dict[str, DirectIngestPreProcessedIngestView],
        ingest_view_export_args: IngestViewMaterializationArgs,
    ) -> str:
        """Returns a version of the export query for the provided args that can be run in the BigQuery UI."""
        query, query_params = cls._debug_generate_unified_query(
            ingest_views_by_name[ingest_view_export_args.ingest_view_name],
            ingest_view_export_args,
        )

        for param in query_params:
            dt = param.value
            query = query.replace(
                f"@{param.name}",
                f"DATETIME({dt.year}, {dt.month}, {dt.day}, {dt.hour}, {dt.minute}, {dt.second})",
            )

        return query

    @classmethod
    def _debug_generate_unified_query(
        cls,
        ingest_view: DirectIngestPreProcessedIngestView,
        ingest_view_export_args: IngestViewMaterializationArgs,
    ) -> Tuple[str, List[bigquery.ScalarQueryParameter]]:
        """Generates a single query that is date bounded such that it represents the data that has changed for this view
        between the specified date bounds in the provided export args.

        If there is no lower bound, this produces a query for a historical query up to the upper bound date. Otherwise,
        it diffs two historical queries to produce a delta query, using the SQL 'EXCEPT DISTINCT' function.

        Important Note: This query is meant for debug use only. In the actual DirectIngest flow, query results for
        individual dates are persisted into temporary tables, and those temporary tables are then diff'd using SQL's
        `EXCEPT DISTINCT` function.
        """

        upper_bound_table_id = cls._get_upper_bound_intermediate_table_name(
            ingest_view_export_args
        )
        query, query_params = cls._generate_export_query_and_params_for_date(
            ingest_view=ingest_view,
            ingest_instance=DirectIngestInstance.PRIMARY,
            destination_table_type=DestinationTableType.TEMPORARY,
            destination_table_id=upper_bound_table_id,
            update_timestamp=ingest_view_export_args.upper_bound_datetime_to_export,
            param_name=UPPER_BOUND_TIMESTAMP_PARAM_NAME,
            raw_table_subquery_name_prefix="upper_"
            if ingest_view.materialize_raw_data_table_views
            else "",
        )

        if ingest_view_export_args.upper_bound_datetime_prev:
            lower_bound_table_id = cls._get_lower_bound_intermediate_table_name(
                ingest_view_export_args
            )
            (
                lower_bound_query,
                lower_bound_query_params,
            ) = cls._generate_export_query_and_params_for_date(
                ingest_view=ingest_view,
                ingest_instance=DirectIngestInstance.PRIMARY,
                destination_table_type=DestinationTableType.TEMPORARY,
                destination_table_id=lower_bound_table_id,
                update_timestamp=ingest_view_export_args.upper_bound_datetime_prev,
                param_name=LOWER_BOUND_TIMESTAMP_PARAM_NAME,
                raw_table_subquery_name_prefix="lower_"
                if ingest_view.materialize_raw_data_table_views
                else "",
            )

            query_params.extend(lower_bound_query_params)

            diff_query = IngestViewMaterializer._create_date_diff_query(
                upper_bound_query=f"SELECT * FROM {upper_bound_table_id}",
                upper_bound_prev_query=f"SELECT * FROM {lower_bound_table_id}",
                do_reverse_date_diff=ingest_view.do_reverse_date_diff,
            )
            diff_query = DirectIngestPreProcessedIngestView.add_order_by_suffix(
                query=diff_query, order_by_cols=ingest_view.order_by_cols
            )

            query = f"{query}\n{lower_bound_query}\n{diff_query}"
        return query, query_params

    @staticmethod
    def _generate_export_query_and_params_for_date(
        *,
        ingest_view: DirectIngestPreProcessedIngestView,
        ingest_instance: DirectIngestInstance,
        update_timestamp: datetime.datetime,
        destination_table_type: DestinationTableType,
        destination_table_id: str,
        param_name: str = UPDATE_TIMESTAMP_PARAM_NAME,
        raw_table_subquery_name_prefix: Optional[str] = None,
    ) -> Tuple[str, List[bigquery.ScalarQueryParameter]]:
        """Generates a single query for the provided |ingest view| that is date bounded by |update_timestamp|."""
        query_params = [
            bigquery.ScalarQueryParameter(
                param_name, bigquery.enums.SqlTypeNames.DATETIME.value, update_timestamp
            )
        ]

        if destination_table_type == DestinationTableType.TEMPORARY:
            destination_dataset_id = None
        elif destination_table_type == DestinationTableType.PERMANENT_EXPIRING:
            destination_dataset_id = ingest_view_materialization_temp_dataset(
                ingest_view, ingest_instance
            )
        else:
            raise ValueError(
                f"Unexpected destination_table_type [{destination_table_type.name}]"
            )

        query = ingest_view.expanded_view_query(
            config=DirectIngestPreProcessedIngestView.QueryStructureConfig(
                raw_table_view_type=RawTableViewType.PARAMETERIZED,
                param_name_override=param_name,
                destination_table_type=destination_table_type,
                destination_dataset_id=destination_dataset_id,
                destination_table_id=destination_table_id,
                raw_table_subquery_name_prefix=raw_table_subquery_name_prefix,
            )
        )
        return query, query_params


if __name__ == "__main__":

    # Update these variables and run to print an export query you can run in the BigQuery UI
    region_code_: str = "us_mo"
    ingest_view_name_: str = "tak001_offender_identification"
    upper_bound_datetime_prev_: datetime.datetime = datetime.datetime(2020, 10, 15)
    upper_bound_datetime_to_export_: datetime.datetime = datetime.datetime(2020, 12, 18)

    with local_project_id_override(GCP_PROJECT_STAGING):
        region_ = regions.get_region(region_code_, is_direct_ingest=True)
        view_collector_ = DirectIngestPreProcessedIngestViewCollector(region_, [])
        views_by_name_ = {
            builder.ingest_view_name: builder.build()
            for builder in view_collector_.collect_view_builders()
        }

        debug_query = IngestViewMaterializer.debug_query_for_args(
            views_by_name_,
            # TODO(#9717): Migrate to new BQ-based implementation of
            #  IngestViewMaterializationArgs.
            GcsfsIngestViewExportArgs(
                ingest_view_name=ingest_view_name_,
                upper_bound_datetime_prev=upper_bound_datetime_prev_,
                upper_bound_datetime_to_export=upper_bound_datetime_to_export_,
                output_bucket_name="any_bucket",
            ),
        )
        print(debug_query)