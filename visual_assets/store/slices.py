"""Slice metadata of an adopted source, derived from the source bytes (`TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`, ADR D25).

`intake/aseprite.read_facts` already walked the slice chunks and quarantined anything out of bounds or inconsistent; this turns the facts of a source that passed intake into the contract
records carried on its `SourceRecord`, sorted by name. A source with no slice is `None`, so its record is byte-identical to one written before the field existed. Slice user data is ignored.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from pydantic import ValidationError

from visual_assets.store import records
from visual_assets.store.contracts import canonical_json
from visual_assets.store.contracts.slices import (
    RuntimeSlice, RuntimeSliceEntry, RuntimeSliceKey, RuntimeSlices, SliceKey, SlicePivot, SliceRect, SourceSlice,
)
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


class SliceScaleError(Exception):
    """The scale that maps a source's pixels onto its exported artifact could not be resolved (unknown scale class, or the artifact is not the source times that scale)."""


_REVISION_OF_RECORD = re.compile(r"^[0-9a-f]{64}\.(r\d{4})\.artifact\.json$")


def _scaled(key: SliceKey, scale: int) -> RuntimeSliceKey:
    b = key.bounds
    return RuntimeSliceKey(
        frame=key.frame, x=b.x * scale, y=b.y * scale, w=b.w * scale, h=b.h * scale,
        center=None if key.center is None else SliceRect(x=key.center.x * scale, y=key.center.y * scale, w=key.center.w * scale, h=key.center.h * scale),
        pivot=None if key.pivot is None else SlicePivot(x=key.pivot.x * scale, y=key.pivot.y * scale),
    )


def runtime_slices_bytes(entries, *, catalog_id: str, release_id: str, scales: Mapping[str, int]) -> bytes:
    """The bytes of `slices.json` for the opt-in `export-runtime --slices`: for each release entry whose source has slices, those of the newest source revision that built the entry's artifact, with the
    geometry in the EXPORTED image's pixels (source pixels times the build scale of the artifact's scale class, from the export config in `scales`). Entries without slices are omitted; the manifest is untouched.
    Raises `SliceScaleError` when the scale class is unknown or the artifact's size is not the source's size times that scale."""
    out: list[RuntimeSliceEntry] = []
    for entry in entries:
        digest = entry.pixel_hash.split(":", 1)[1]
        source_asset_id, scale_class = entry.artifact_id.rsplit("--", 1)
        directory = records.generated_dir() / entry.artifact_id
        revisions = sorted(m.group(1) for p in directory.glob(f"{digest}.r*.artifact.json") if (m := _REVISION_OF_RECORD.match(p.name)))
        if not revisions:
            continue
        source = records.load_source(source_asset_id, revisions[-1])
        if source.slices is None:
            continue
        scale = scales.get(scale_class)
        found = records.load_artifact_for(source_asset_id, revisions[-1], scale_class)
        if scale is None or found is None or found[0].width != source.width * scale or found[0].height != source.height * scale:
            raise SliceScaleError(f"the scale of {entry.visual_key} cannot be resolved from its export config and artifact")
        out.append(RuntimeSliceEntry(
            visual_key=entry.visual_key, detail=entry.detail,
            slices=tuple(RuntimeSlice(name=one.name, keys=tuple(_scaled(k, scale) for k in one.keys)) for one in source.slices),
        ))
    manifest = RuntimeSlices(
        record_type="runtime_slices", schema_version=1, catalog_id=catalog_id, release_id=release_id,
        entries=tuple(sorted(out, key=lambda e: (e.visual_key, e.detail or ""))),
    )
    return canonical_json(manifest)
