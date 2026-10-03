"""Semantic registry records: `VisualKeyDefinition`, `AliasEntry`, `VisualKeyRegistry`."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from visual_assets.store.contracts.base import BoundedText, StoreRecord
from visual_assets.store.identities import VisualKey

Family = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,31}$")]
AxisName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,31}$")]
AxisValue = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_]{0,31}$")]

MAX_AXES = 8  # budget: docs/assets/budgets.md
MAX_AXIS_VALUES = 64  # budget: docs/assets/budgets.md


class VariantAxis(StoreRecord):
    name: AxisName
    values: Annotated[tuple[AxisValue, ...], Field(min_length=1, max_length=MAX_AXIS_VALUES)]

    @model_validator(mode="after")
    def _unique(self) -> VariantAxis:
        if len(set(self.values)) != len(self.values):
            raise ValueError("axis values must be unique")
        return self


class VisualKeyDefinition(StoreRecord):
    key: VisualKey
    family: Family
    description: BoundedText
    variant_axes: Annotated[tuple[VariantAxis, ...], Field(max_length=MAX_AXES)]
    optional: bool = False  # a release may omit an optional key; every other registry key needs an artifact

    @model_validator(mode="after")
    def _unique_axes(self) -> VisualKeyDefinition:
        names = [a.name for a in self.variant_axes]
        if len(set(names)) != len(names):
            raise ValueError("axis names must be unique")
        return self


class AliasEntry(StoreRecord):
    alias: VisualKey
    target: VisualKey


class VisualKeyRegistry(StoreRecord):
    record_type: Literal["visual_key_registry"]
    schema_version: Literal[1]
    keys: tuple[VisualKeyDefinition, ...]
    aliases: tuple[AliasEntry, ...]
