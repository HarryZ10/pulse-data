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
"""Tests for violation/pipeline.py"""
import unittest
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from unittest import mock

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import BeamAssertException, assert_that, equal_to

from recidiviz.calculator.pipeline.metrics.base_metric_pipeline import (
    ClassifyEvents,
    MetricPipelineJobArgs,
    ProduceMetrics,
)
from recidiviz.calculator.pipeline.metrics.violation.events import (
    ViolationWithResponseEvent,
)
from recidiviz.calculator.pipeline.metrics.violation.identifier import (
    ViolationIdentifier,
)
from recidiviz.calculator.pipeline.metrics.violation.metric_producer import (
    ViolationMetricProducer,
)
from recidiviz.calculator.pipeline.metrics.violation.metrics import (
    ViolationMetric,
    ViolationMetricType,
)
from recidiviz.calculator.pipeline.metrics.violation.pipeline import (
    ViolationPipelineRunDelegate,
)
from recidiviz.calculator.pipeline.pipeline_type import PipelineType
from recidiviz.calculator.pipeline.utils.beam_utils.person_utils import (
    PERSON_EVENTS_KEY,
    PERSON_METADATA_KEY,
    ExtractPersonEventsMetadata,
)
from recidiviz.calculator.pipeline.utils.beam_utils.pipeline_args_utils import (
    derive_apache_beam_pipeline_args,
)
from recidiviz.calculator.pipeline.utils.metric_utils import PersonMetadata
from recidiviz.common.constants.person_characteristics import Ethnicity, Gender, Race
from recidiviz.common.constants.state.state_supervision_violation import (
    StateSupervisionViolationType,
)
from recidiviz.common.constants.state.state_supervision_violation_response import (
    StateSupervisionViolationResponseDecision,
)
from recidiviz.persistence.database.schema.state import schema
from recidiviz.persistence.entity.state import entities
from recidiviz.tests.calculator.calculator_test_utils import (
    normalized_database_base_dict,
    normalized_database_base_dict_list,
)
from recidiviz.tests.calculator.pipeline.fake_bigquery import (
    DataTablesDict,
    FakeReadFromBigQueryFactory,
    FakeWriteToBigQuery,
    FakeWriteToBigQueryFactory,
)
from recidiviz.tests.calculator.pipeline.utils.run_pipeline_test_utils import (
    default_data_dict_for_root_schema_classes,
    run_test_pipeline,
)
from recidiviz.tests.calculator.pipeline.utils.state_utils.state_calculation_config_manager_test import (
    STATE_DELEGATES_FOR_TESTS,
)

ALL_METRIC_INCLUSIONS_DICT = {metric_type: True for metric_type in ViolationMetricType}

ROOT_SCHEMA_CLASSES_FOR_PIPELINE = [
    schema.StatePerson,
    schema.StateSupervisionViolation,
    schema.StateSupervisionViolationResponse,
]


class TestViolationPipeline(unittest.TestCase):
    """Tests the entire violation pipeline."""

    def setUp(self) -> None:
        self.fake_bq_source_factory = FakeReadFromBigQueryFactory()
        self.fake_bq_sink_factory = FakeWriteToBigQueryFactory(FakeWriteToBigQuery)
        self.state_specific_delegate_patcher = mock.patch(
            "recidiviz.calculator.pipeline.utils.state_utils"
            ".state_calculation_config_manager.get_all_state_specific_delegates"
        )
        self.mock_get_state_delegate_container = (
            self.state_specific_delegate_patcher.start()
        )
        self.mock_get_state_delegate_container.return_value = STATE_DELEGATES_FOR_TESTS

    def tearDown(self) -> None:
        self._stop_state_specific_delegate_patchers()

    def _stop_state_specific_delegate_patchers(self) -> None:
        self.state_specific_delegate_patcher.stop()

    @staticmethod
    def build_data_dict(
        fake_person_id: int, fake_supervision_violation_id: int
    ) -> Dict[str, List[Any]]:
        """Builds a data_dict for a basic run of the pipeline."""
        fake_person = schema.StatePerson(
            state_code="US_XX",
            person_id=fake_person_id,
            gender=Gender.FEMALE,
            birthdate=date(1985, 2, 1),
        )
        persons_data = [normalized_database_base_dict(fake_person)]

        race_1 = schema.StatePersonRace(
            person_race_id=111,
            state_code="US_XX",
            race=Race.ASIAN,
            person_id=fake_person_id,
        )
        race_2 = schema.StatePersonRace(
            person_race_id=111,
            state_code="US_XX",
            race=Race.AMERICAN_INDIAN_ALASKAN_NATIVE,
            person_id=fake_person_id,
        )

        races_data = normalized_database_base_dict_list([race_1, race_2])

        ethnicity = schema.StatePersonEthnicity(
            person_ethnicity_id=111,
            state_code="US_XX",
            ethnicity=Ethnicity.NOT_HISPANIC,
            person_id=fake_person_id,
        )

        ethnicity_data = normalized_database_base_dict_list([ethnicity])

        violation_decision = schema.StateSupervisionViolationResponseDecisionEntry(
            state_code="US_XX",
            decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            person_id=fake_person_id,
            supervision_violation_response_decision_entry_id=234,
            supervision_violation_response_id=1234,
        )
        violation_response = schema.StateSupervisionViolationResponse(
            state_code="US_XX",
            supervision_violation_response_id=1234,
            response_type=entities.StateSupervisionViolationResponseType.VIOLATION_REPORT,
            response_date=date(2021, 1, 4),
            is_draft=False,
            supervision_violation_response_decisions=[violation_decision],
            person_id=fake_person_id,
        )

        violation_type = schema.StateSupervisionViolationTypeEntry(
            supervision_violation_type_entry_id=123,
            state_code="US_XX",
            violation_type=StateSupervisionViolationType.FELONY,
            person_id=fake_person_id,
        )
        violation = schema.StateSupervisionViolation(
            state_code="US_XX",
            supervision_violation_id=fake_supervision_violation_id,
            violation_date=date(2021, 1, 1),
            is_violent=False,
            is_sex_offense=False,
            supervision_violation_types=[violation_type],
            supervision_violation_responses=[violation_response],
            person_id=fake_person_id,
        )
        violation_type.supervision_violation_id = fake_supervision_violation_id
        violation_response.supervision_violation_id = fake_supervision_violation_id

        violations_data = [normalized_database_base_dict(violation)]
        violation_responses_data = [normalized_database_base_dict(violation_response)]
        violation_types_data = [normalized_database_base_dict(violation_type)]
        violation_decisions_data = [normalized_database_base_dict(violation_decision)]

        state_race_ethnicity_population_count_data = [
            {
                "state_code": "US_XX",
                "race_or_ethnicity": "ASIAN",
                "population_count": 1,
                "representation_priority": 1,
            }
        ]

        data_dict = default_data_dict_for_root_schema_classes(
            ROOT_SCHEMA_CLASSES_FOR_PIPELINE
        )

        data_dict_overrides: Dict[str, List[Any]] = {
            schema.StatePerson.__tablename__: persons_data,
            schema.StatePersonRace.__tablename__: races_data,
            schema.StatePersonEthnicity.__tablename__: ethnicity_data,
            schema.StateSupervisionViolation.__tablename__: violations_data,
            schema.StateSupervisionViolationResponse.__tablename__: violation_responses_data,
            schema.StateSupervisionViolationTypeEntry.__tablename__: violation_types_data,
            schema.StateSupervisionViolationResponseDecisionEntry.__tablename__: violation_decisions_data,
            "state_race_ethnicity_population_counts": state_race_ethnicity_population_count_data,
        }
        data_dict.update(data_dict_overrides)

        return data_dict

    def run_test_pipeline(
        self,
        data_dict: DataTablesDict,
        expected_metric_types: Set[ViolationMetricType],
        unifying_id_field_filter_set: Optional[Set[int]] = None,
        metric_types_filter: Optional[Set[str]] = None,
    ) -> None:
        """Runs a test version of the violation pipeline."""
        project = "project"
        dataset = "dataset"

        read_from_bq_constructor = (
            self.fake_bq_source_factory.create_fake_bq_source_constructor(
                dataset, data_dict
            )
        )
        write_to_bq_constructor = (
            self.fake_bq_sink_factory.create_fake_bq_sink_constructor(
                dataset, expected_output_metric_types=expected_metric_types
            )
        )
        run_test_pipeline(
            run_delegate=ViolationPipelineRunDelegate,
            state_code="US_XX",
            project_id=project,
            dataset_id=dataset,
            read_from_bq_constructor=read_from_bq_constructor,
            write_to_bq_constructor=write_to_bq_constructor,
            unifying_id_field_filter_set=unifying_id_field_filter_set,
            metric_types_filter=metric_types_filter,
        )

    def testViolationPipeline(self) -> None:
        """Tests the violation pipeline."""
        data_dict = self.build_data_dict(
            fake_person_id=12345, fake_supervision_violation_id=23456
        )

        self.run_test_pipeline(
            data_dict, expected_metric_types={ViolationMetricType.VIOLATION}
        )

    def testViolationPipelineWithFilterSet(self) -> None:
        """Tests the violation pipeline with a proper filter set."""
        data_dict = self.build_data_dict(
            fake_person_id=12345, fake_supervision_violation_id=23456
        )

        self.run_test_pipeline(
            data_dict,
            expected_metric_types={ViolationMetricType.VIOLATION},
            unifying_id_field_filter_set={12345},
        )

    def testViolationPipelineWithNoViolations(self) -> None:
        """Tests the violation pipeline when a person does not have any violations."""
        data_dict = self.build_data_dict(
            fake_person_id=12345, fake_supervision_violation_id=23456
        )
        data_dict[schema.StateSupervisionViolation.__tablename__] = []
        data_dict[schema.StateSupervisionViolationResponse.__tablename__] = []
        data_dict[schema.StateSupervisionViolationTypeEntry.__tablename__] = []
        data_dict[
            schema.StateSupervisionViolationResponseDecisionEntry.__tablename__
        ] = []

        self.run_test_pipeline(data_dict, expected_metric_types=set())


class TestClassifyViolationEvents(unittest.TestCase):
    """Tests the ClassifyViolationEvents DoFn."""

    def setUp(self) -> None:
        self.state_code = "US_XX"
        self.fake_person_id = 12345
        self.fake_supervision_violation_id = 23456

        self.fake_person = entities.StatePerson.new_with_defaults(
            state_code="US_XX",
            person_id=self.fake_person_id,
            gender=Gender.FEMALE,
            birthdate=date(1985, 2, 1),
        )
        self.identifier = ViolationIdentifier()
        self.state_specific_delegate_patcher = mock.patch(
            "recidiviz.calculator.pipeline.utils.state_utils"
            ".state_calculation_config_manager.get_all_state_specific_delegates"
        )
        self.mock_get_state_delegate_container = (
            self.state_specific_delegate_patcher.start()
        )
        self.mock_get_state_delegate_container.return_value = STATE_DELEGATES_FOR_TESTS

    def tearDown(self) -> None:
        self._stop_state_specific_delegate_patchers()

    def _stop_state_specific_delegate_patchers(self) -> None:
        self.state_specific_delegate_patcher.stop()

    def testClassifyViolationEvents(self) -> None:
        """Tests the ClassifyViolationEvents DoFn."""
        violation_type = entities.StateSupervisionViolationTypeEntry.new_with_defaults(
            state_code="US_XX",
            violation_type=StateSupervisionViolationType.FELONY,
        )
        violation_decision = (
            entities.StateSupervisionViolationResponseDecisionEntry.new_with_defaults(
                state_code="US_XX",
                decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
            )
        )
        violation_response = entities.StateSupervisionViolationResponse.new_with_defaults(
            state_code="US_XX",
            response_type=entities.StateSupervisionViolationResponseType.VIOLATION_REPORT,
            response_date=date(2021, 1, 4),
            is_draft=False,
            supervision_violation_response_decisions=[violation_decision],
        )
        violation = entities.StateSupervisionViolation.new_with_defaults(
            state_code="US_XX",
            supervision_violation_id=self.fake_supervision_violation_id,
            violation_date=date(2021, 1, 1),
            is_violent=False,
            is_sex_offense=False,
            supervision_violation_types=[violation_type],
            supervision_violation_responses=[violation_response],
        )
        violation_decision.supervision_violation_response = violation_response
        violation_response.supervision_violation = violation
        violation_type.supervision_violation = violation

        violation_events = [
            ViolationWithResponseEvent(
                state_code="US_XX",
                supervision_violation_id=self.fake_supervision_violation_id,
                event_date=date(2021, 1, 4),
                violation_date=date(2021, 1, 1),
                violation_type=StateSupervisionViolationType.FELONY,
                violation_type_subtype="FELONY",
                is_most_severe_violation_type=True,
                is_violent=False,
                is_sex_offense=False,
                most_severe_response_decision=StateSupervisionViolationResponseDecision.SHOCK_INCARCERATION,
                is_most_severe_response_decision_of_all_violations=True,
                is_most_severe_violation_type_of_all_violations=True,
            )
        ]

        correct_output: List[
            Tuple[int, Tuple[entities.StatePerson, List[ViolationWithResponseEvent]]]
        ] = [(self.fake_person_id, (self.fake_person, violation_events))]

        person_violations = {
            entities.StatePerson.__name__: [self.fake_person],
            entities.StateSupervisionViolation.__name__: [violation],
        }
        test_pipeline = TestPipeline()
        output = (
            test_pipeline
            | beam.Create([(self.fake_person_id, person_violations)])
            | "Identify Violation Events"
            >> beam.ParDo(
                ClassifyEvents(), state_code=self.state_code, identifier=self.identifier
            )
        )

        assert_that(output, equal_to(correct_output))
        test_pipeline.run()

    def testClassifyViolationEventsNoViolations(self) -> None:
        """Tests the ClassifyViolationEvents DoFn with no violations for a person."""

        correct_output: List[
            Tuple[int, Tuple[entities.StatePerson, List[ViolationWithResponseEvent]]]
        ] = []

        person_violations = {
            entities.StatePerson.__name__: [self.fake_person],
            entities.StateSupervisionViolation.__name__: [],
        }
        test_pipeline = TestPipeline()
        output = (
            test_pipeline
            | beam.Create([(self.fake_person_id, person_violations)])
            | "Identify Violation Events"
            >> beam.ParDo(
                ClassifyEvents(), state_code=self.state_code, identifier=self.identifier
            )
        )
        assert_that(output, equal_to(correct_output))
        test_pipeline.run()

    def testClassifyViolationEventsNoResponses(self) -> None:
        """Tests the ClassifyViolationEvents DoFn with a violation that has no responses for a person."""
        violation_type = entities.StateSupervisionViolationTypeEntry.new_with_defaults(
            state_code="US_XX",
            violation_type=StateSupervisionViolationType.FELONY,
        )
        violation = entities.StateSupervisionViolation.new_with_defaults(
            state_code="US_XX",
            supervision_violation_id=self.fake_supervision_violation_id,
            violation_date=date(2021, 1, 1),
            is_violent=False,
            is_sex_offense=False,
            supervision_violation_types=[violation_type],
        )
        violation_type.supervision_violation = violation

        correct_output: List[
            Tuple[int, Tuple[entities.StatePerson, List[ViolationWithResponseEvent]]]
        ] = []

        person_violations = {
            entities.StatePerson.__name__: [self.fake_person],
            entities.StateSupervisionViolation.__name__: [violation],
        }
        test_pipeline = TestPipeline()
        output = (
            test_pipeline
            | beam.Create([(self.fake_person_id, person_violations)])
            | "Identify Violation Events"
            >> beam.ParDo(
                ClassifyEvents(), state_code=self.state_code, identifier=self.identifier
            )
        )
        assert_that(output, equal_to(correct_output))
        test_pipeline.run()


class TestProduceViolationMetrics(unittest.TestCase):
    """Tests the Produce ViolationMetrics DoFn in the pipeline."""

    def setUp(self) -> None:
        self.fake_person_id = 12345
        self.fake_supervision_violation_id = 23456

        self.person_metadata = PersonMetadata(prioritized_race_or_ethnicity="ASIAN")

        self.job_id_patcher = mock.patch(
            "recidiviz.calculator.pipeline.metrics.base_metric_pipeline.job_id"
        )
        self.mock_job_id = self.job_id_patcher.start()
        self.mock_job_id.return_value = "job_id"

        self.metric_producer = ViolationMetricProducer()
        self.pipeline_type = PipelineType.VIOLATION

        default_beam_args: List[str] = [
            "--project",
            "project",
            "--job_name",
            "test",
        ]

        beam_pipeline_options = PipelineOptions(
            derive_apache_beam_pipeline_args(default_beam_args)
        )

        self.pipeline_job_args = MetricPipelineJobArgs(
            state_code="US_XX",
            project_id="project",
            input_dataset="dataset_id",
            reference_dataset="dataset_id",
            static_reference_dataset="dataset_id",
            output_dataset="dataset_id",
            metric_inclusions=ALL_METRIC_INCLUSIONS_DICT,
            region="region",
            job_name="job",
            person_id_filter_set=None,
            calculation_end_month=None,
            calculation_month_count=-1,
            apache_beam_pipeline_options=beam_pipeline_options,
        )

    def testProduceViolationMetrics(self) -> None:
        """Tests the ProduceViolationMetrics DoFn."""

        fake_person = entities.StatePerson.new_with_defaults(
            state_code="US_XX",
            person_id=self.fake_person_id,
            gender=Gender.FEMALE,
            birthdate=date(1985, 2, 1),
        )

        violation_events = [
            ViolationWithResponseEvent(
                state_code="US_XX",
                event_date=date(2011, 4, 3),
                supervision_violation_id=self.fake_supervision_violation_id,
                violation_type=StateSupervisionViolationType.ABSCONDED,
                is_most_severe_violation_type=True,
                is_violent=False,
                is_sex_offense=False,
                most_severe_response_decision=StateSupervisionViolationResponseDecision.REVOCATION,
            )
        ]

        expected_metric_counts = {ViolationMetricType.VIOLATION.value: 1}

        test_pipeline = TestPipeline()

        inputs = [
            (
                self.fake_person_id,
                {
                    PERSON_EVENTS_KEY: [(fake_person, violation_events)],
                    PERSON_METADATA_KEY: [self.person_metadata],
                },
            )
        ]

        output = (
            test_pipeline
            | beam.Create(inputs)
            | beam.ParDo(ExtractPersonEventsMetadata())
            | "Produce Violation Metrics"
            >> beam.ParDo(
                ProduceMetrics(),
                self.pipeline_job_args,
                self.metric_producer,
                self.pipeline_type,
            )
        )

        assert_that(
            output,
            AssertMatchers.count_metrics(expected_metric_counts),
            "Assert number of metrics is expected value",
        )

        test_pipeline.run()

    def testProduceViolationMetricsNoInput(self) -> None:
        """Tests the ProduceViolationMetrics when there is no input to the function."""

        test_pipeline = TestPipeline()

        output = (
            test_pipeline
            | beam.Create([])
            | beam.ParDo(ExtractPersonEventsMetadata())
            | "Produce ViolationMetrics"
            >> beam.ParDo(
                ProduceMetrics(),
                self.pipeline_job_args,
                self.metric_producer,
                self.pipeline_type,
            )
        )

        assert_that(output, equal_to([]))

        test_pipeline.run()


class AssertMatchers:
    """Functions to be used by Apache Beam testing `assert_that` functions to validate
    pipeline outputs."""

    @staticmethod
    def validate_pipeline_test() -> Callable[[Dict[str, int], bool], None]:
        def _validate_pipeline_test(
            output: Dict[str, int], allow_empty: bool = False
        ) -> None:
            if not allow_empty and not output:
                raise BeamAssertException("Output metrics unexpectedly empty.")

            for metric in output:
                if not isinstance(metric, ViolationMetric):
                    raise BeamAssertException(
                        "Failed assert. Output is not of type ViolationMetric."
                    )

        return _validate_pipeline_test

    @staticmethod
    def count_metrics(
        expected_metric_counts: Dict[str, int]
    ) -> Callable[[Dict[str, int]], None]:
        """Asserts that the number of metric combinations matches the expected
        counts."""

        def _count_metrics(output: Dict[str, int]) -> None:
            actual_combination_counts = {}

            for key in expected_metric_counts.keys():
                actual_combination_counts[key] = 0

            for metric in output:
                assert isinstance(metric, ViolationMetric)

                metric_type = metric.metric_type

                actual_combination_counts[metric_type.value] = (
                    actual_combination_counts[metric_type.value] + 1
                )

            for key in expected_metric_counts:
                if expected_metric_counts[key] != actual_combination_counts[key]:
                    raise BeamAssertException(
                        "Failed assert. Count does not match expected value:"
                        f"{expected_metric_counts[key]} != {actual_combination_counts[key]}"
                    )

        return _count_metrics