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
"""A script for writing all regularly updated views in BigQuery to a set of temporary
datasets. Used during development to test updates to views.

This can be run on-demand whenever locally with the following command:
    python -m recidiviz.tools.load_views_to_sandbox \
        --project_id [PROJECT_ID] \
        --sandbox_dataset_prefix [SANDBOX_DATASET_PREFIX] \
        --dataflow_dataset_override [DATAFLOW_DATASET_OVERRIDE] \
        --refresh_materialized_tables_only [True,False]
        --view_ids_to_load [DATASET_ID_1.VIEW_ID_1,DATASET_ID_2.VIEW_ID_2,...]
        --dataset_ids_to_load [DATASET_ID_1,DATASET_ID_2,...]
        --update_ancestors [True,False]
        --update_descendants [True,False]
"""
import argparse
import logging
import sys
from typing import List, Optional, Tuple

from recidiviz.big_query.big_query_view import BigQueryViewBuilder
from recidiviz.big_query.view_update_manager import (
    create_managed_dataset_and_deploy_views_for_view_builders,
    rematerialize_views_for_view_builders,
    view_builder_sub_graph_for_view_builders_to_load,
)
from recidiviz.calculator.query.state.dataset_config import (
    DATAFLOW_METRICS_MATERIALIZED_DATASET,
)
from recidiviz.tools.utils.script_helpers import prompt_for_confirmation
from recidiviz.utils.environment import GCP_PROJECT_PRODUCTION, GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override, project_id
from recidiviz.utils.params import str_to_bool
from recidiviz.view_registry.address_overrides_factory import (
    address_overrides_for_view_builders,
)
from recidiviz.view_registry.datasets import VIEW_SOURCE_TABLE_DATASETS
from recidiviz.view_registry.deployed_views import deployed_view_builders


def load_views_to_sandbox(
    sandbox_dataset_prefix: str,
    dataflow_dataset_override: Optional[str] = None,
    refresh_materialized_tables_only: bool = False,
    view_ids_to_load: Optional[List[str]] = None,
    dataset_ids_to_load: Optional[List[str]] = None,
    update_ancestors: bool = False,
    update_descendants: bool = False,
) -> None:
    """Loads all views into sandbox datasets prefixed with the sandbox_dataset_prefix.

    Params
    ------
    sandbox_dataset_prefix : str
        Loads datasets that all take the form of
        "<sandbox_dataset_prefix>_<original dataset_id>

    dataflow_dataset_override : Optional[str]
        If True, updates views in the DATAFLOW_METRICS_MATERIALIZED_DATASET

    refresh_materialized_tables_only : bool, default False
        If True, re-materializes any materialized views and doesn't change underlying
        queries.

    view_ids_to_load : Optional[List[str]]
        If specified, only loads views whose view_id matches one of the listed view_ids.
        View_ids must take the form dataset_id.view_id

    dataset_ids_to_load : Optional[List[str]]
        If specified, only loads views whose dataset_id matches one of the listed
        dataset_ids.

    update_descendants : bool, default True
        Only applied if `view_ids_to_load` or `dataset_ids_to_load` is included.
        If True, loads descendant views of views found in the two aforementioned
        parameters.

    update_ancestors : bool, default False
        To be used with `view_ids_to_load` or `dataset_ids_to_load`. If True, loads
        ancestor/parent views of views found in the two aforementioned parameters.
    """
    # throw error if update_ancestors and not view_ids_to_load or dataset_ids_to_load
    if (update_ancestors or update_descendants) and not (
        view_ids_to_load or dataset_ids_to_load
    ):
        raise ValueError(
            "Cannot update_ancestors or update descendants without supplying "
            "view_ids_to_load or dataset_ids_to_load."
        )

    # throw error if both view_ids_to_load and dataset_ids_to_load supplied
    if view_ids_to_load and dataset_ids_to_load:
        raise ValueError(
            "Only supply view_ids_to_load OR dataset_ids_to_load, not both."
        )

    logging.info("Gathering all deployed views...")
    view_builders = deployed_view_builders(project_id())

    # if view_ids_to_load or dataset_ids_to_load, use dag walker to get ancestor views
    # and potentially descendant views, which will be updated, too.
    if view_ids_to_load or dataset_ids_to_load:

        # get views for all view_ids in view_ids_to_load or dataset_ids_to_load
        view_builders_to_load: List[BigQueryViewBuilder] = []
        if view_ids_to_load:
            view_builders_to_load.extend(
                view
                for view in view_builders
                if view.dataset_id + "." + view.view_id in view_ids_to_load
            )
        elif dataset_ids_to_load:  # mypy
            view_builders_to_load.extend(
                view for view in view_builders if view.dataset_id in dataset_ids_to_load
            )
        else:
            raise ValueError("view_ids_to_load and dataset_ids_to_load not defined.")

        logging.info("Gathering views to load to sandbox...")
        builders_to_update = view_builder_sub_graph_for_view_builders_to_load(
            view_builders_to_load=view_builders_to_load,
            all_view_builders_in_dag=view_builders,
            get_ancestors=update_ancestors,
            get_descendants=update_descendants,
            include_dataflow_views=(dataflow_dataset_override is not None),
        )

    # update all view builders if view_ids_to_load not specified
    else:
        prompt_for_confirmation("This will load all sandbox views, continue?")
        builders_to_update = [
            builder
            for builder in view_builders
            # Only update views in the DATAFLOW_METRICS_MATERIALIZED_DATASET if the
            # dataflow_dataset_override is set
            if dataflow_dataset_override is not None
            or builder.dataset_id != DATAFLOW_METRICS_MATERIALIZED_DATASET
        ]

    logging.info("Updating %s views.", len(builders_to_update))

    sandbox_address_overrides = address_overrides_for_view_builders(
        view_dataset_override_prefix=sandbox_dataset_prefix,
        view_builders=builders_to_update,
        dataflow_dataset_override=dataflow_dataset_override,
    )

    if refresh_materialized_tables_only:
        rematerialize_views_for_view_builders(
            view_source_table_datasets=VIEW_SOURCE_TABLE_DATASETS,
            views_to_update_builders=builders_to_update,
            all_view_builders=view_builders,
            address_overrides=sandbox_address_overrides,
            # If a given view hasn't been loaded to the sandbox, skip it
            skip_missing_views=True,
        )
    else:
        create_managed_dataset_and_deploy_views_for_view_builders(
            view_source_table_datasets=VIEW_SOURCE_TABLE_DATASETS,
            view_builders_to_update=builders_to_update,
            address_overrides=sandbox_address_overrides,
            # Don't clean up datasets when running a sandbox script
            historically_managed_datasets_to_clean=None,
        )


def parse_arguments(argv: List[str]) -> Tuple[argparse.Namespace, List[str]]:
    """Parses the required arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--project_id",
        dest="project_id",
        type=str,
        choices=[GCP_PROJECT_STAGING, GCP_PROJECT_PRODUCTION],
        required=True,
    )

    parser.add_argument(
        "--sandbox_dataset_prefix",
        dest="sandbox_dataset_prefix",
        help="A prefix to append to all names of the datasets where these views will "
        "be loaded.",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--dataflow_dataset_override",
        dest="dataflow_dataset_override",
        help="An override of the dataset containing Dataflow metric output that the "
        "updated views should reference.",
        type=str,
        required=False,
    )

    parser.add_argument(
        "--refresh_materialized_tables_only",
        dest="refresh_materialized_tables_only",
        help="If True, will only re-materialize views that have already been loaded to "
        "the sandbox.",
        type=str_to_bool,
        default=False,
        required=False,
    )

    # make view_ids_to_load and dataset_ids_to_load mutually exclusive
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--view_ids_to_load",
        dest="view_ids_to_load",
        help="A list of view_ids to load separated by commas. If provided, only loads "
        "views in this list plus dependencies. View_ids must take the form "
        "dataset_id.view_id",
        type=str_to_list,
        required=False,
    )

    group.add_argument(
        "--dataset_ids_to_load",
        dest="dataset_ids_to_load",
        help="A list of dataset_ids to load separated by commas. If provided, only "
        "loads datasets in this list plus dependencies.",
        type=str_to_list,
        required=False,
    )

    parser.add_argument(
        "--update_ancestors",
        dest="update_ancestors",
        help="If True, will load views that are ancestors of those provided in "
        "view_ids_to_load or dataset_ids_to_load.",
        type=str_to_bool,
        default=False,
        required=False,
    )

    parser.add_argument(
        "--update_descendants",
        dest="update_descendants",
        help="If True, will load views that are descendants of those provided in "
        "view_ids_to_load or dataset_ids_to_load.",
        type=str_to_bool,
        default=True,
        required=False,
    )

    return parser.parse_known_args(argv)


def str_to_list(list_str: str) -> List[str]:
    """
    Separates strings by commas and returns a list
    """
    return list_str.split(",")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    known_args, _ = parse_arguments(sys.argv)

    with local_project_id_override(known_args.project_id):
        logging.info(
            "Prefixing all view datasets with [%s_].", known_args.sandbox_dataset_prefix
        )

        load_views_to_sandbox(
            known_args.sandbox_dataset_prefix,
            known_args.dataflow_dataset_override,
            known_args.refresh_materialized_tables_only,
            known_args.view_ids_to_load,
            known_args.dataset_ids_to_load,
            known_args.update_ancestors,
            known_args.update_descendants,
        )
