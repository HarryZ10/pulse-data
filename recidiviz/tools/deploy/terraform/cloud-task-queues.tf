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

resource "google_cloud_tasks_queue" "scraper_phase_queue" {
  name     = "scraper-phase-v2"
  location = var.app_engine_region

  rate_limits {
    max_dispatches_per_second = 1
    max_concurrent_dispatches = 100
  }

  retry_config {
    max_attempts = 5
    min_backoff  = "5s"
    max_backoff  = "300s"
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}

# Queue used to run tasks that monitor whether we can start a cloud SQL refresh job and
# schedule the tasks when appropriate.
resource "google_cloud_tasks_queue" "cloud-sql-to-bq-refresh-scheduler-queue" {
  name     = "cloud-sql-to-bq-refresh-scheduler"
  location = var.app_engine_region

  rate_limits {
    max_dispatches_per_second = 25
    max_concurrent_dispatches = 25
  }

  retry_config {
    max_attempts = 5
    max_backoff  = "120s"
    min_backoff  = "5s"
  }

  stackdriver_logging_config {
    sampling_ratio = 1.0
  }
}

# Queue used to process tasks that mirror the data in our CloudSQL databases to BQ.
module "cloud-sql-to-bq-refresh-queue" {
  source = "./modules/base-task-queue"

  queue_name         = "cloud-sql-to-bq-refresh"
  region             = var.app_engine_region
  max_retry_attempts = 1
}

# Queue used to process tasks that update views in BQ.
module "bq-view-update-queue" {
  source = "./modules/base-task-queue"

  queue_name         = "bq-view-update"
  region             = var.app_engine_region
  max_retry_attempts = 1
}

# Queue used to process tasks that export the results of metric view queries to GCS.
# TODO(#4593): We might be able to get rid of this queue entirely once we run the metric
#  export endpoints directly in Airflow, rather than just triggering the tasks with
#  Pub/Sub topics.
module "metric-view-export-queue" {
  source = "./modules/base-task-queue"

  queue_name         = "metric-view-export"
  region             = var.app_engine_region
  max_retry_attempts = 1
  max_concurrent_dispatches = 50
}

# Queue used for tasks to update raw data `*_latest` views for all states.
module "state-raw-data-latest-view-update-queue" {
  source = "./modules/base-task-queue"

  queue_name         = "state-raw-data-latest-view-update"
  region             = var.app_engine_region
  max_retry_attempts = 1
}

module "case-triage-db-operations-queue" {
  source = "./modules/base-task-queue"

  queue_name                = "case-triage-db-operations-queue"
  region                    = var.app_engine_region
  max_dispatches_per_second = 100
}
