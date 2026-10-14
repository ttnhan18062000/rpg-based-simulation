"""Animation metadata of an adopted source, derived from the source bytes (`TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`).

`intake/aseprite.read_facts` already walked the frame headers and the tags chunk and quarantined anything out of bounds or inconsistent; this turns the facts of a source that passed
intake into the contract record carried on its `SourceRecord`. A source with one frame is not animation: `None`, so its record is byte-identical to one written before the field existed.
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from visual_assets.store import records
from visual_assets.store.contracts import canonical_json
from visual_assets.store.contracts.animation import AnimationTag, RuntimeAnimation, RuntimeAnimationEntry, SourceAnimation
from visual_assets.store.intake import aseprite

DIRECTIONS = ("forward", "reverse", "ping_pong", "ping_pong_reverse")


class AnimationError(Exception):
    """The source's animation facts do not form a valid `SourceAnimation` (intake should have quarantined it; adoption refuses rather than store a bad record)."""


def animation_from_source(source: bytes) -> SourceAnimation | None:
    facts, problems = aseprite.read_facts(source)
    if facts is None or any(code.value.startswith(("ANIMATION_", "SOURCE_")) for code, _ in problems):
        raise AnimationError("the source's animation metadata is invalid")
    if facts.frames < 2:
        return None
    try:
        return SourceAnimation(
            frame_durations_ms=facts.frame_durations_ms,
            tags=tuple(AnimationTag(name=t.name, from_frame=t.from_frame, to_frame=t.to_frame, direction=DIRECTIONS[t.direction], repeat=t.repeat) for t in facts.animation_tags),
        )
    except (ValidationError, IndexError) as exc:
        raise AnimationError("the source's animation metadata does not form a valid record") from exc


_REVISION_OF_RECORD = re.compile(r"^[0-9a-f]{64}\.(r\d{4})\.artifact\.json$")


def runtime_animation_bytes(entries, *, catalog_id: str, release_id: str) -> bytes:
    """The bytes of `animation.json` for the opt-in `export-runtime --animation`: for each release entry whose source has more than one frame, the durations and tags of the
    newest source revision that built the entry's artifact (the one `build` takes), read from its `SourceRecord`. Entries of a one-frame source are omitted; the manifest is untouched."""
    out: list[RuntimeAnimationEntry] = []
    for entry in entries:
        digest = entry.pixel_hash.split(":", 1)[1]
        source_asset_id = entry.artifact_id.rsplit("--", 1)[0]
        directory = records.generated_dir() / entry.artifact_id
        revisions = sorted(m.group(1) for p in directory.glob(f"{digest}.r*.artifact.json") if (m := _REVISION_OF_RECORD.match(p.name)))
        if not revisions:
            continue
        found = records.load_source(source_asset_id, revisions[-1]).animation
        if found is not None:
            out.append(RuntimeAnimationEntry(visual_key=entry.visual_key, detail=entry.detail, frame_durations_ms=found.frame_durations_ms, tags=found.tags))
    manifest = RuntimeAnimation(
        record_type="runtime_animation", schema_version=1, catalog_id=catalog_id, release_id=release_id,
        entries=tuple(sorted(out, key=lambda e: (e.visual_key, e.detail or ""))),
    )
    return canonical_json(manifest)
