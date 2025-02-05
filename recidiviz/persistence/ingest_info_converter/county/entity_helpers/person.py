# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2019 Recidiviz, Inc.
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
"""Converts an ingest_info proto Person to a persistence entity."""

import re
from typing import Optional

from recidiviz.common.constants.county.person_characteristics import (
    RESIDENCY_STATUS_SUBSTRING_MAP,
    Ethnicity,
    Gender,
    Race,
    ResidencyStatus,
)
from recidiviz.common.str_field_utils import normalize
from recidiviz.persistence.ingest_info_converter.utils.converter_utils import (
    fn,
    parse_birthdate,
    parse_external_id,
)
from recidiviz.persistence.ingest_info_converter.utils.ingest_info_proto_enum_mapper import (
    IngestInfoProtoEnumMapper,
)

# Suffixes used in county names in uszipcode library
from recidiviz.persistence.ingest_info_converter.utils.names import parse_name
from recidiviz.persistence.ingest_info_converter.utils.zipcodes import (
    ZipcodeDatabaseManager,
)

USZIPCODE_COUNTY_SUFFIXES = [
    "BOROUGH",
    "CENSUS AREA",
    "CITY",
    "CITY AND BOROUGH",
    "COUNTY",
    "MUNICIPIO",
    "PARISH",
]


def copy_fields_to_builder(person_builder, proto, metadata):
    """Mutates the provided |person_builder| by converting an ingest_info proto
    Person.

    Note: This will not copy children into the Builder!
    """
    enum_fields = {
        "gender": Gender,
        "race": Race,
        "ethnicity": Ethnicity,
    }
    proto_enum_mapper = IngestInfoProtoEnumMapper(
        proto, enum_fields, metadata.enum_overrides
    )

    new = person_builder

    # Enum mappings
    new.race = proto_enum_mapper.get(Race)
    new.race_raw_text = fn(normalize, "race", proto)
    new.ethnicity = proto_enum_mapper.get(Ethnicity)
    new.ethnicity_raw_text = fn(normalize, "ethnicity", proto)
    new.gender = proto_enum_mapper.get(Gender)
    new.gender_raw_text = fn(normalize, "gender", proto)

    # 1-to-1 mappings
    new.external_id = fn(parse_external_id, "person_id", proto)
    new.full_name = parse_name(proto)
    new.birthdate, new.birthdate_inferred_from_age = parse_birthdate(
        proto, "birthdate", "age"
    )
    new.residency_status = fn(_parse_residency_status, "place_of_residence", proto)
    new.resident_of_region = fn(
        _parse_is_resident, "place_of_residence", proto, metadata.region
    )

    new.jurisdiction_id = fn(
        normalize, "jurisdiction_id", proto, default=metadata.jurisdiction_id
    )

    new.region = metadata.region


def _parse_is_resident(place_of_residence: str, region: str) -> Optional[bool]:
    """Returns (True) if person is resident of |region|, (False) if they are
    not, and (None) if it cannot be determined
    """

    zip_code = None
    zip_code_matches = re.findall(r"\d{5}", place_of_residence)
    if not zip_code_matches:
        return None
    # If more than one match is present, take the last one (to account for
    # cases where there is a 5-digit address)
    zip_code = zip_code_matches[-1]

    # Region code us_xx is state, us_xx_xxx... is county
    if len(region) == 5:
        return _parse_is_state_resident(zip_code, region)
    return _parse_is_county_resident(zip_code, region)


def _parse_is_county_resident(residence_zip_code: str, region: str) -> Optional[bool]:
    # Remove 'us_xx_' prefix
    region_county = region[6:]
    # Replace underscores with spaces because uszipcode uses spaces
    normalized_region_county = region_county.upper().replace("_", " ")

    residence_county = ZipcodeDatabaseManager.county_for_zipcode(residence_zip_code)
    if not residence_county:
        return None

    # uszipcode county names only contain hyphens and periods as special
    # characters
    normalized_residence_county = (
        residence_county.upper().replace("-", " ").replace(".", "")
    )

    # Compare region county to base version of residence county, as well as
    # residence county with any matching suffixes stripped
    possible_county_names = {normalized_residence_county}
    for suffix in USZIPCODE_COUNTY_SUFFIXES:
        suffix_length = len(suffix)
        if normalized_residence_county[-(suffix_length):] == suffix:
            possible_county_names.add(
                normalized_residence_county[: -(suffix_length + 1)]
            )
    for county_name in possible_county_names:
        if normalized_region_county == county_name:
            return True
    return False


def _parse_is_state_resident(residence_zip_code: str, region: str) -> Optional[bool]:
    region_state_code = region[-2:].upper()
    residence_state_code = ZipcodeDatabaseManager.state_for_zipcode(residence_zip_code)
    if not residence_state_code:
        return None
    return region_state_code == residence_state_code


def _parse_residency_status(place_of_residence: str) -> ResidencyStatus:
    """Returns the residency status of a person, e.g. PERMANENT or HOMELESS."""
    normalized_place_of_residence = place_of_residence.upper()
    for substring, residency_status in RESIDENCY_STATUS_SUBSTRING_MAP.items():
        if substring in normalized_place_of_residence:
            return residency_status
    # If place of residence is provided and no other status is explicitly
    # provided, assumed to be permanent
    return ResidencyStatus.PERMANENT
