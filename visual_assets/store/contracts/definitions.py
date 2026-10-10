"""Semantic registry records: `VisualKeyDefinition`, `AliasEntry`, `VisualKeyRegistry`."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, StringConstraints, model_serializer, model_validator

from visual_assets.store.contracts.base import BoundedText, StoreRecord, drop_absent
from visual_assets.store.identities import VisualKey

Family = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,31}$")]
AxisName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,31}$")]
AxisValue = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_]{0,31}$")]

MAX_AXES = 8  # budget: docs/assets/budgets.md
MAX_AXIS_VALUES = 64  # budget: docs/assets/budgets.md
MAX_DETAIL_VALUES = 16  # budget: docs/assets/budgets.md; values on one key's detail axis (not MAX_AXIS_VALUES: the runtime manifest repeats them)


class VariantAxis(StoreRecord):
    name: AxisName
    values: Annotated[tuple[AxisValue, ...], Field(min_length=1, max_length=MAX_AXIS_VALUES)]

    @model_validator(mode="after")
    def _unique(self) -> VariantAxis:
        if len(set(self.values)) != len(self.values):
            raise ValueError("axis values must be unique")
        return self


class DetailAxis(StoreRecord):
    """A key's decorative detail axis: the only axis picked by a coordinate hash, and the only one with a mandatory default.

    Not a `variant_axes` entry on purpose: those are context-selected with strict precedence (proposal 9.2), this one is chosen
    per cell by the client, and its `default` is what an adoption without a `detail_value` fills.
    """

    values: Annotated[tuple[AxisValue, ...], Field(min_length=1, max_length=MAX_DETAIL_VALUES)]
    default: AxisValue

    @model_validator(mode="after")
    def _rules(self) -> DetailAxis:
        if len(set(self.values)) != len(self.values):
            raise ValueError("detail values must be unique")
        if self.default not in self.values:
            raise ValueError("the detail default must be one of its values")
        return self


SafetyClass = Literal["decorative", "identifying", "critical"]
FallbackKind = Literal["none", "flat_fill", "text", "glyph_and_text"]
LabelKey = Annotated[str, StringConstraints(pattern=r"^label\.[a-z][a-z0-9_.]{0,126}$")]


class Fallback(StoreRecord):
    """What shows when a key's image is gone (`docs/assets/fallback_safety.md`): a structured alternative instead of prose.

    `none`: nothing is drawn (only a decorative key may say so). `flat_fill`: the cell's flat colour, with `text` naming the hover text that carries the fact. `text`: `text` says which text carries it.
    `glyph_and_text`: the existing `glyph` (named, e.g. `lucide:Hammer`) plus `text`. The registry loader enforces which kinds need which parts (`catalog/registry.py::safety_problems`)."""

    kind: FallbackKind
    text: BoundedText | None = None
    glyph: BoundedText | None = None

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "text", "glyph")


class VisualKeyDefinition(StoreRecord):
    key: VisualKey
    family: Family
    description: BoundedText
    variant_axes: Annotated[tuple[VariantAxis, ...], Field(max_length=MAX_AXES)]
    optional: bool = False  # a release may omit an optional key; every other registry key needs an artifact
    detail: DetailAxis | None = None  # a slot is (key, detail value); a key without an axis has the single slot (key, None)
    # `AM1-W02.7`: the fallback-safety class and its structured alternative. Optional in the record so synthetic fixture keys and old records parse; the registry loader requires both on every real key.
    safety_class: SafetyClass | None = None
    fallback: Fallback | None = None
    # icon family only (W3C WAI functional-icon text): a translatable id and the default English text of what the icon is or does. A decorative key carries neither (empty alt).
    label_key: LabelKey | None = None
    label: BoundedText | None = None

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail", "safety_class", "fallback", "label_key", "label")

    @model_validator(mode="after")
    def _unique_axes(self) -> VisualKeyDefinition:
        names = [a.name for a in self.variant_axes]
        if len(set(names)) != len(names):
            raise ValueError("axis names must be unique")
        return self

    def effective_detail(self, detail_value: str | None) -> str | None:
        """The slot value an adoption or entry fills: `None` means this key's declared default, or no slot value for a key without an axis."""
        if self.detail is None:
            return None
        return self.detail.default if detail_value is None else detail_value


class AliasEntry(StoreRecord):
    alias: VisualKey
    target: VisualKey


class VisualKeyRegistry(StoreRecord):
    record_type: Literal["visual_key_registry"]
    schema_version: Literal[1]
    keys: tuple[VisualKeyDefinition, ...]
    aliases: tuple[AliasEntry, ...]
    size_bound: ClassVar[str] = "MAX_REGISTRY_BYTES"  # the registry is a hand-edited file of up to MAX_VISUAL_KEYS keys
