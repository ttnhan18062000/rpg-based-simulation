"""Slice metadata read from an adopted `.aseprite` source (`TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`; ADR D25).

A slice is a named rectangle of the sprite, optionally with a 9-slice centre and a pivot, with one key per frame where it changes. DERIVED from the source bytes (Aseprite's slice chunk), never declared by a
producer, and carried per SOURCE REVISION on the `SourceRecord`: no registry field, no change to the runtime manifest, nothing the client reads. All geometry is in SOURCE pixels, relative to the image
(never an atlas); the centre and pivot are relative to the slice's own top-left corner, exactly as Aseprite stores them. The pivot may sit on the far edge of the slice (edges are inclusive), the centre must lie inside it.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, StringConstraints, model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import BoundedText, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue
from visual_assets.store.identities import CatalogId, ReleaseId, VisualKey

SliceName = Annotated[BoundedText, StringConstraints(min_length=1, max_length=32)]  # the animation tag rule
Coordinate = Annotated[int, Field(ge=-(2**31), le=2**31 - 1)]  # Aseprite stores a signed 32-bit LONG
Extent = Annotated[int, Field(ge=1, le=2**31 - 1)]  # a slice or centre is at least one pixel in each direction
FrameIndex = Annotated[int, Field(ge=0)]


class SliceRect(StoreRecord):
    x: Coordinate
    y: Coordinate
    w: Extent
    h: Extent


class SlicePivot(StoreRecord):
    x: Coordinate
    y: Coordinate


class SliceKey(StoreRecord):
    frame: FrameIndex  # zero-based; the key holds from this frame until the next key of the slice
    bounds: SliceRect  # in source pixels, relative to the image
    center: SliceRect | None = None  # the 9-slice centre, relative to the slice's own top-left corner
    pivot: SlicePivot | None = None  # relative to the slice's own top-left corner

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "center", "pivot")

    @model_validator(mode="after")
    def _inside_the_slice(self) -> SliceKey:
        b = self.bounds
        if self.center is not None:
            c = self.center
            if not (0 <= c.x and 0 <= c.y and c.x + c.w <= b.w and c.y + c.h <= b.h):
                raise ValueError("the 9-slice centre is not inside its slice")
        if self.pivot is not None and not (0 <= self.pivot.x <= b.w and 0 <= self.pivot.y <= b.h):
            raise ValueError("the pivot is not inside its slice")
        return self


class SourceSlice(StoreRecord):
    name: SliceName
    keys: tuple[SliceKey, ...]

    @model_validator(mode="after")
    def _consistent(self) -> SourceSlice:
        if not 1 <= len(self.keys) <= config.MAX_SLICE_KEYS:
            raise ValueError(f"a slice needs 1..{config.MAX_SLICE_KEYS} keys")
        frames = [k.frame for k in self.keys]
        if frames != sorted(set(frames)):
            raise ValueError("slice keys must be sorted by frame, one per frame")
        if len({k.center is None for k in self.keys}) > 1:
            raise ValueError("the 9-slice centre is on every key of a slice or on none")
        if len({k.pivot is None for k in self.keys}) > 1:
            raise ValueError("the pivot is on every key of a slice or on none")
        return self


def check_slices(slices: tuple[SourceSlice, ...], *, width: int, height: int, frame_count: int) -> None:
    """The rules that need the source's own size and frame count; `SourceRecord` calls this. Raises ValueError."""
    if len(slices) > config.MAX_SOURCE_SLICES:
        raise ValueError(f"more than {config.MAX_SOURCE_SLICES} slices")
    names = [s.name for s in slices]
    if names != sorted(set(names)):
        raise ValueError("slices must be sorted by name, names unique")
    for one in slices:
        for key in one.keys:
            b = key.bounds
            if key.frame >= frame_count:
                raise ValueError(f"slice {one.name!r} has a key past the {frame_count} frames")
            if not (0 <= b.x and 0 <= b.y and b.x + b.w <= width and b.y + b.h <= height):
                raise ValueError(f"slice {one.name!r} lies outside the {width}x{height} canvas")


class RuntimeSliceKey(StoreRecord):
    frame: FrameIndex
    x: Coordinate  # in the EXPORTED image's pixels (source pixels times the build scale), relative to the image, never to an atlas sheet
    y: Coordinate
    w: Extent
    h: Extent
    center: SliceRect | None = None  # relative to the slice's own corner, scaled the same way
    pivot: SlicePivot | None = None

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "center", "pivot")


class RuntimeSlice(StoreRecord):
    name: SliceName
    keys: tuple[RuntimeSliceKey, ...]


class RuntimeSliceEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None
    slices: tuple[RuntimeSlice, ...]

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class RuntimeSlices(StoreRecord):
    """The opt-in `export-runtime --slices` file; no flag, no file."""

    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"

    record_type: Literal["runtime_slices"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    entries: tuple[RuntimeSliceEntry, ...]  # only the keys whose source has slices, sorted by key and detail
