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
"""Contains base Dimension classes."""

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional, Type, TypeVar

import attr

from recidiviz.common.constants.enum_overrides import EnumOverrides

DimensionT = TypeVar("DimensionT", bound="Dimension")


class Dimension:
    """Each dimension is represented as a class that is used to hold the values for that dimension and perform any
    necessary validation. All dimensions are categorical. Those with a pre-defined set of values are implemented as
    enums. Others are classes with a single text field to hold any value, and are potentially normalized to a
    pre-defined set of values as a separate dimension.
    """

    @classmethod
    @abstractmethod
    def get(
        cls: Type[DimensionT],
        dimension_cell_value: str,
        enum_overrides: Optional[EnumOverrides] = None,
    ) -> DimensionT:
        """Create an instance of the dimension based on the given value.

        Raises an error if it is unable to create an instance of a dimension. Only returns None if the value is
        explicitly ignored in `enum_overrides`.
        """

    @classmethod
    @abstractmethod
    def build_overrides(
        cls: Type[DimensionT], mapping_overrides: Dict[str, str]
    ) -> EnumOverrides:
        """
        Builds EnumOverrides for this Dimension, based on the provided mapping_overrides.
        Should raise an error if this Dimension is not normalized or if overrides are not supported.
        """

    @classmethod
    @abstractmethod
    def is_normalized(cls) -> bool:
        """
        Returns whether the dimensions cls is normalized
        """

    @classmethod
    @abstractmethod
    def dimension_identifier(cls) -> str:
        """The globally unique dimension_identifier of this dimension, used when storing it in the database.

        E.g. 'metric/population/type' or 'global/facility/raw'.
        """

    @classmethod
    @abstractmethod
    def get_generated_dimension_classes(cls) -> List[Type["Dimension"]]:
        """Returns a list of Dimensions that the current dimension will generate"""

    @classmethod
    @abstractmethod
    def generate_dimension_classes(
        cls, dimension_cell_value: str, enum_overrides: Optional[EnumOverrides] = None
    ) -> List["Dimension"]:
        """Generates Dimensions based on the dimension cell value provided"""

    @property
    @abstractmethod
    def dimension_value(self) -> str:
        """The value of this dimension instance.

        E.g. 'FEMALE' is a potential value for an instance of the 'global/raw/gender' dimension.
        """


@attr.s(frozen=True)
class RawDimension(Dimension, metaclass=ABCMeta):
    """Base class to use to create a raw version of a normalized dimension.

    Child classes are typically created by passing a normalized dimension class to `raw_type_for_dimension`, which will
    create a raw, or not normalized, copy version of the dimension.
    """

    value: str = attr.ib(converter=str)

    @classmethod
    def get(
        cls, dimension_cell_value: str, enum_overrides: Optional[EnumOverrides] = None
    ) -> "RawDimension":
        if enum_overrides is not None:
            raise ValueError(
                f"Unexpected enum_overrides when building raw dimension value: {enum_overrides}"
            )
        return cls(dimension_cell_value)

    @classmethod
    def build_overrides(cls, mapping_overrides: Dict[str, str]) -> EnumOverrides:
        raise ValueError("Can't raise override for RawDimension class")

    @classmethod
    def is_normalized(cls) -> bool:
        return False

    @classmethod
    def get_generated_dimension_classes(cls) -> List[Type[Dimension]]:
        return []

    @classmethod
    def generate_dimension_classes(
        cls, dimension_cell_value: str, enum_overrides: Optional[EnumOverrides] = None
    ) -> List[Dimension]:
        return []

    @property
    def dimension_value(self) -> str:
        return self.value