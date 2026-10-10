"""Slice metadata of an adopted source, derived from the source bytes (`TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`, ADR D25).

`intake/aseprite.read_facts` already walked the slice chunks and quarantined anything out of bounds or inconsistent; this turns the facts of a source that passed intake into the contract
records carried on its `SourceRecord`, sorted by name. A source with no slice is `None`, so its record is byte-identical to one written before the field existed. Slice user data is ignored.
"""

from __future__ import annotations

from pydantic import ValidationError

from visual_assets.store.contracts.slices import SliceKey, SlicePivot, SliceRect, SourceSlice
from visual_assets.store.intake import aseprite


class SliceError(Exception):
    """The source's slice facts do not form valid `SourceSlice` records (intake should have quarantined it; adoption refuses rather than store a bad record)."""


def slices_from_source(source: bytes) -> tuple[SourceSlice, ...] | None:
    facts, problems = aseprite.read_facts(source)
    if facts is None or any(code.value.startswith(("SLICE_", "SOURCE_")) for code, _ in problems):
        raise SliceError("the source's slice metadata is invalid")
    if not facts.slices:
        return None
    try:
        return tuple(sorted((_record(raw) for raw in facts.slices), key=lambda s: s.name))
    except ValidationError as exc:
        raise SliceError("the source's slice metadata does not form a valid record") from exc


def _record(raw: aseprite.RawSlice) -> SourceSlice:
    return SourceSlice(
        name=raw.name,
        keys=tuple(
            SliceKey(
                frame=k.frame, bounds=SliceRect(x=k.x, y=k.y, w=k.w, h=k.h),
                center=None if k.center is None else SliceRect(x=k.center[0], y=k.center[1], w=k.center[2], h=k.center[3]),
                pivot=None if k.pivot is None else SlicePivot(x=k.pivot[0], y=k.pivot[1]),
            )
            for k in raw.keys
        ),
    )
