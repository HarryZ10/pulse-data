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
# ============================================================================
"""Define the ORM schema objects that map directly to the database, for Pathways related entities.
"""

from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import DeclarativeMeta, declarative_base

# Defines the base class for all table classes in the pathways schema.
# For actual schema definitions, see /pathways/schema.py.
from recidiviz.persistence.database.database_entity import DatabaseEntity

PathwaysBase: DeclarativeMeta = declarative_base(
    cls=DatabaseEntity, name="PathwaysBase"
)


class LibertyToPrisonTransitions(PathwaysBase):
    """ETL data imported from
    `recidiviz.calculator.query.state.views.dashboard.pathways.event_level.liberty_to_prison_transitions`
    """

    __tablename__ = "liberty_to_prison_transitions"

    # Date that the transition occurred
    transition_date = Column(Date, primary_key=True, nullable=False)
    # Denormalized transition year
    year = Column(Integer, nullable=False)
    # Denormalized transition month
    month = Column(Integer, nullable=False)
    # Bin of when the transition occurred (see recidiviz.calculator.query.bq_utils.get_binned_time_period_months)
    time_period = Column(String, nullable=True)
    # Person ID for the transition
    person_id = Column(String, primary_key=True, nullable=False)
    # Age group of the person when the transition occurred (see recidiviz.calculator.query.bq_utils.add_age_groups)
    age_group = Column(String, nullable=True)
    # Gender of the person
    gender = Column(String, nullable=True)
    # `prioritized_race_or_ethnicity` of the person
    race = Column(String, nullable=True)
    # District the transition occurred in
    judicial_district = Column(String, nullable=False)
    # Total number of months the person was previously incarcerated
    prior_length_of_incarceration = Column(String, nullable=False)
    # State code for the transition
    state_code = Column(String, nullable=False)


class PrisonToSupervisionTransitions(PathwaysBase):
    """ETL data imported from
    `recidiviz.calculator.query.state.views.dashboard.pathways.event_level.prison_to_supervision_transitions`
    """

    __tablename__ = "prison_to_supervision_transitions"

    # Date that the transition occurred
    transition_date = Column(Date, primary_key=True, nullable=False)
    # Denormalized transition year
    year = Column(Integer, nullable=False)
    # Denormalized transition month
    month = Column(Integer, nullable=False)
    # Person ID for the transition
    person_id = Column(String, primary_key=True, nullable=False)
    # Age group of the person when the transition occurred (see recidiviz.calculator.query.bq_utils.add_age_groups)
    age_group = Column(String, nullable=True)
    # Age of the person
    age = Column(Integer, nullable=True)
    # Gender of the person
    gender = Column(String, nullable=True)
    # `prioritized_race_or_ethnicity` of the person
    race = Column(String, nullable=True)
    # Facility the transition occurred from
    facility = Column(String, nullable=True)
    # Full name of the person
    full_name = Column(String, nullable=True)
    # Bin of when the transition occurred (see recidiviz.calculator.query.bq_utils.get_binned_time_period_months)
    time_period = Column(String, nullable=True)
    # External ID of the person
    state_id = Column(String, nullable=True)
    # State code for the transition
    state_code = Column(String, nullable=False)


class SupervisionToLibertyTransitions(PathwaysBase):
    """ETL data imported from
    `recidiviz.calculator.query.state.views.dashboard.pathways.event_level.supervision_to_liberty_transitions`
    """

    __tablename__ = "supervision_to_liberty_transitions"

    # Date that the transition occurred
    transition_date = Column(Date, primary_key=True, nullable=False)
    # Denormalized transition year
    year = Column(Integer, nullable=False)
    # Denormalized transition month
    month = Column(Integer, nullable=False)
    # Person ID for the transition
    person_id = Column(String, primary_key=True, nullable=False)
    # Age group of the person when the transition occurred (see recidiviz.calculator.query.bq_utils.add_age_groups)
    age_group = Column(String, nullable=True)
    # Age of the person
    age = Column(Integer, nullable=True)
    # Gender of the person
    gender = Column(String, nullable=True)
    # `prioritized_race_or_ethnicity` of the person
    race = Column(String, nullable=True)
    # Type of supervision the person was under
    supervision_type = Column(String, nullable=True)
    # Level of supervision the person was under
    supervision_level = Column(String, nullable=True)
    # District the person was supervised in
    supervision_district = Column(String, nullable=True)
    # ID of the person's supervising officer at time of release
    supervising_officer = Column(String, nullable=True)
    # When the ending supervision period started
    supervision_start_date = Column(Date, nullable=True)
    # Bin of when the transition occurred (see recidiviz.calculator.query.bq_utils.get_binned_time_period_months)
    time_period = Column(String, nullable=True)
    # Binned length of supervision in months
    length_of_stay = Column(String, nullable=True)
    # State code for the transition
    state_code = Column(String, nullable=False)


class SupervisionToPrisonTransitions(PathwaysBase):
    """ETL data imported from
    `recidiviz.calculator.query.state.views.dashboard.pathways.event_level.supervision_to_prison_transitions`
    """

    __tablename__ = "supervision_to_prison_transitions"

    # Date that the transition occurred
    transition_date = Column(Date, primary_key=True, nullable=False)
    # Denormalized transition year
    year = Column(Integer, nullable=False)
    # Denormalized transition month
    month = Column(Integer, nullable=False)
    # Person ID for the transition
    person_id = Column(String, primary_key=True, nullable=False)
    # Type of supervision the person was under
    supervision_type = Column(String, nullable=True)
    # Level of supervision the person was under
    supervision_level = Column(String, nullable=True)
    # Age group of the person when the transition occurred (see recidiviz.calculator.query.bq_utils.add_age_groups)
    age_group = Column(String, nullable=True)
    # Age of the person
    age = Column(Integer, nullable=True)
    # Gender of the person
    gender = Column(String, nullable=True)
    # `prioritized_race_or_ethnicity` of the person
    race = Column(String, nullable=True)
    # ID of the person's supervising officer at time of release
    supervising_officer = Column(String, nullable=True)
    # When the ending supervision period started
    supervision_start_date = Column(Date, nullable=True)
    # District that the person is in
    supervision_district = Column(String, nullable=True)
    # Bin of when the transition occurred (see recidiviz.calculator.query.bq_utils.get_binned_time_period_months)
    time_period = Column(String, nullable=True)
    # Binned length of supervision in months
    length_of_stay = Column(String, nullable=True)
    # State code for the transition
    state_code = Column(String, nullable=False)
