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
"""
Important note: This script should be run from `prod-data-client`. It will not work
when run anywhere else.

This script runs a single downgrade migration against the specified database. Note that
the downgrade alembic migration must exist for it to be run properly, so this script
should be run on a rev where the to-be-rolled-back upgrade migration exists.

Example usage (run from `pipenv shell`):

python -m recidiviz.tools.migrations.run_downgrade_migration \
    --database STATE \
    --project-id recidiviz-staging \
    --target-revision [revision_id] \
    --ssl-cert-path ~/dev_state_data_certs
"""
import argparse
import logging
import sys

import alembic.config

from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.sqlalchemy_engine_manager import (
    SQLAlchemyEngineManager,
)
from recidiviz.server_config import database_keys_for_schema_type
from recidiviz.tools.migrations.migration_helpers import (
    confirm_correct_db_instance,
    confirm_correct_git_branch,
)
from recidiviz.tools.postgres import local_postgres_helpers
from recidiviz.tools.utils.script_helpers import prompt_for_confirmation
from recidiviz.utils import metadata
from recidiviz.utils.environment import GCP_PROJECT_PRODUCTION, GCP_PROJECT_STAGING
from recidiviz.utils.metadata import local_project_id_override


def create_parser() -> argparse.ArgumentParser:
    """Returns an argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Run a single downgrade migration against the specified PostgresQL database."
    )
    parser.add_argument(
        "--database",
        type=SchemaType,
        choices=list(SchemaType),
        help="Specifies which database to run against.",
        required=True,
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default="./",
        help="The path to the root pulse-data/ folder. "
        "This is needed to check the current git branch.",
    )
    parser.add_argument(
        "--project-id",
        choices=[GCP_PROJECT_STAGING, GCP_PROJECT_PRODUCTION],
        help="Used to select which GCP project in which to run this script.",
        required=True,
    )
    parser.add_argument(
        "--target-revision",
        type=str,
        help="The revision id to downgrade to.",
        required=True,
    )
    parser.add_argument(
        "--ssl-cert-path",
        type=str,
        help="The path to the folder where the certs live.",
        required=True,
    )
    return parser


def main(
    schema_type: SchemaType, repo_root: str, target_revision: str, ssl_cert_path: str
) -> None:
    """
    Invokes the main code path for running a downgrade.

    This checks for user validations that the database and branches are correct and then runs the downgrade
    migration.
    """

    is_prod = metadata.project_id() == GCP_PROJECT_PRODUCTION
    if is_prod:
        logging.info("RUNNING AGAINST PRODUCTION\n")

    prompt_for_confirmation("This script will run a DOWNGRADE migration.", "DOWNGRADE")
    confirm_correct_db_instance(schema_type)
    confirm_correct_git_branch(repo_root)

    db_keys = database_keys_for_schema_type(schema_type)

    for key in db_keys:
        # Run downgrade
        overridden_env_vars = SQLAlchemyEngineManager.update_sqlalchemy_env_vars(
            database_key=key,
            ssl_cert_path=ssl_cert_path,
            migration_user=True,
        )
        try:
            config = alembic.config.Config(key.alembic_file)
            alembic.command.downgrade(config, target_revision)
        except Exception as e:
            logging.error("Downgrade failed to run: %s", e)
            sys.exit(1)
        finally:
            local_postgres_helpers.restore_local_env_vars(overridden_env_vars)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    args = create_parser().parse_args()
    with local_project_id_override(args.project_id):
        main(args.database, args.repo_root, args.target_revision, args.ssl_cert_path)
