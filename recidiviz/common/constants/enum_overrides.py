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
# =============================================================================
"""Contains logic related to EnumOverrides."""

from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, Optional, Set, Type, TypeVar

import attr

from recidiviz.common.str_field_utils import normalize

EnumMapperFn = Callable[[str], Optional[Enum]]
EnumIgnorePredicate = Callable[[str], bool]

EnumT = TypeVar("EnumT", bound=Enum)

# pylint doesn't support custom decorators, so these attributes can't be subscripted.
# https://github.com/PyCQA/pylint/issues/1694
# pylint: disable=unsubscriptable-object
@attr.s(frozen=True)
class EnumOverrides:
    """Contains region-specific mappings from string keys to Enum values. EnumOverrides
    objects should be created using EnumOverrides.Builder.
    """

    _str_mappings_dict: Dict[Type[Enum], Dict[str, Enum]] = attr.ib()
    _mapper_fns_dict: Dict[Type[Enum], Set["EnumMapperFn"]] = attr.ib()
    _ignores: Dict[Type[Enum], Set[str]] = attr.ib()
    _ignore_predicates_dict: Dict[Type[Enum], Set[EnumIgnorePredicate]] = attr.ib()

    def should_ignore(self, label: str, enum_class: Type[Enum]) -> bool:
        predicate_calls = (
            predicate(label) for predicate in self._ignore_predicates_dict[enum_class]
        )
        return label in self._ignores[enum_class] or any(predicate_calls)

    def parse(self, label: str, enum_class: Type[EnumT]) -> Optional[Enum]:
        """Parses the provided string text into an enum based on the provided mappings.
        Returns None if there is no configured mapping or the string value is marked in
        the ignores list.
        """
        if self.should_ignore(label, enum_class):
            return None

        direct_lookup = self._str_mappings_dict[enum_class].get(label)
        if direct_lookup:
            return direct_lookup

        matches = {
            mapper_fn(label)
            for mapper_fn in self._mapper_fns_dict[enum_class]
            if mapper_fn(label) is not None
        }
        if len(matches) > 1:
            raise ValueError(
                f"Overrides map matched too many values from label {label}: [{matches}]"
            )
        if matches:
            return matches.pop()
        return None

    # pylint: disable=protected-access
    def to_builder(self) -> "Builder":
        builder = self.Builder()
        builder._str_mappings_dict = self._str_mappings_dict
        builder._mapper_fns_dict = self._mapper_fns_dict
        builder._ignores = self._ignores
        builder._ignore_predicates_dict = self._ignore_predicates_dict
        return builder

    @classmethod
    def empty(cls) -> "EnumOverrides":
        return cls.Builder().build()

    class Builder:
        """Builder for EnumOverrides objects."""

        def __init__(self) -> None:
            self._str_mappings_dict: Dict[Type[Enum], Dict[str, Enum]] = defaultdict(
                dict
            )
            self._mapper_fns_dict: Dict[Type[Enum], Set[EnumMapperFn]] = defaultdict(
                set
            )
            self._ignores: Dict[Type[Enum], Set[str]] = defaultdict(set)
            self._ignore_predicates_dict: Dict[
                Type[Enum], Set[EnumIgnorePredicate]
            ] = defaultdict(set)

        def build(self) -> "EnumOverrides":
            return EnumOverrides(
                self._str_mappings_dict,
                self._mapper_fns_dict,
                self._ignores,
                self._ignore_predicates_dict,
            )

        def add_mapper_fn(
            self,
            mapper_fn: EnumMapperFn,
            mapped_cls: Type[Enum],
            from_field: Optional[Type[Enum]] = None,
        ) -> "EnumOverrides.Builder":
            """Adds a |mapper_fn| which maps field values to enums within the
            |mapped_cls|. |mapper_fn| must be a Callable which, given a string value,
            returns an enum of class |mapped_cls| or None.

            Optionally, the |from_field| parameter allows values to be mapped across
            fields. For example:
                `add_mapper_fn(bond_status_mapper, BondStatus, BondType)`
            remaps the bond_type field to a bond_status when the bond_status_mapper
            returns an enum value. Mappings *between* entity types are not allowed.

            Note: take care not to add multiple mapper functions which map the same
            field value to different enums, as EnumOverrides.parse will throw an
            exception.
            """
            if from_field is None:
                from_field = mapped_cls
            self._mapper_fns_dict[from_field].add(mapper_fn)
            return self

        def add(
            self,
            label: str,
            mapped_enum: Enum,
            from_field: Optional[Type[Enum]] = None,
            force_overwrite: bool = False,
            normalize_label: bool = True,
        ) -> "EnumOverrides.Builder":
            """Adds a mapping from |label| to |mapped_enum|. As |label| must be a
            string, the provided field value must match the string exactly to constitute
             a match.

            Optionally, the |from_field| parameter allows values to be mapped across fields. For example:
            `add('PENDING', BondStatus.PENDING, BondType)` remaps the bond_type field to a bond_status when the
            bond_type is set to 'PENDING'. Mappings *between* entity types are not allowed.

            If the |force_overwrite| parameter is set, then it is permitted to change the entity enum an
            existing label maps to. Without it, attempting to re-set a label to a different value will raise
            an exception.
            """
            if from_field is None:
                from_field = mapped_enum.__class__
            if normalize_label:
                label = normalize(label, remove_punctuation=True)
            if (
                not force_overwrite
                and (
                    old_mapping := self._str_mappings_dict[from_field].get(
                        label, mapped_enum
                    )
                )
                != mapped_enum
            ):
                # A mapping already exists for this label and it differs from the
                # mapped value that was passed in.
                raise ValueError(
                    "Cannot override a mapping that has already been set. "
                    f"{label} was mapped to {old_mapping} but call was made to map to {mapped_enum}"
                )
            self._str_mappings_dict[from_field][label] = mapped_enum
            return self

        def ignore_with_predicate(
            self, predicate: EnumIgnorePredicate, from_field: Type[Enum]
        ) -> "EnumOverrides.Builder":
            """Marks strings matching |predicate| as ignored values for |from_field| enum class."""
            self._ignore_predicates_dict[from_field].add(predicate)
            return self

        def ignore(
            self, label: str, from_field: Type[Enum], normalize_label: bool = True
        ) -> "EnumOverrides.Builder":
            """Marks strings matching |label| as ignored values for |from_field| enum class."""
            if normalize_label:
                label = normalize(label, remove_punctuation=True)
            self._ignores[from_field].add(label)

            return self
