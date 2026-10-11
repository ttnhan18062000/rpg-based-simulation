"""Animation metadata read from an adopted `.aseprite` source (`TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`).

DERIVED from the source bytes (frame durations, tags), never declared by a producer, and carried per SOURCE REVISION on the `SourceRecord`: no registry field, no change to the
runtime manifest, nothing the client reads. Aseprite has no per-sprite loop mode; looping lives in each tag (`repeat`) and its `direction`, so those two are what is carried and no
sprite-level loop mode is invented. `RuntimeAnimation` is the opt-in `export-runtime --animation` file; no flag, no file.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, StringConstraints, model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import BoundedText, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue
from visual_assets.store.identities import CatalogId, ReleaseId, VisualKey

Direction = Literal["forward", "reverse", "ping_pong", "ping_pong_reverse"]  # Aseprite's tag directions 0..3, in order
DURATION_MS = Annotated[int, Field(ge=1, le=65535)]  # a frame header holds a WORD; 0 is refused at intake
FrameIndex = Annotated[int, Field(ge=0)]
TagName = Annotated[BoundedText, StringConstraints(min_length=1, max_length=32)]


class AnimationTag(StoreRecord):
    name: TagName
    from_frame: FrameIndex  # zero-based, inclusive
    to_frame: FrameIndex
    direction: Direction
    repeat: Annotated[int, Field(ge=0, le=65535)]  # Aseprite's repeat count; 0 means loop forever


class SourceAnimation(StoreRecord):
    frame_durations_ms: tuple[DURATION_MS, ...]  # one per frame; present only for a source with more than one frame
    tags: tuple[AnimationTag, ...] = ()

    @model_validator(mode="after")
    def _consistent(self) -> SourceAnimation:
        frames = len(self.frame_durations_ms)
        if not 2 <= frames <= config.MAX_ANIMATION_FRAMES:
            raise ValueError(f"animation needs 2..{config.MAX_ANIMATION_FRAMES} frames")
        if len(self.tags) > config.MAX_ANIMATION_TAGS:
            raise ValueError(f"more than {config.MAX_ANIMATION_TAGS} tags")
        names = [t.name for t in self.tags]
        if len(set(names)) != len(names):
            raise ValueError("tag names must be unique")
        for tag in self.tags:
            if not 0 <= tag.from_frame <= tag.to_frame < frames:
                raise ValueError(f"tag {tag.name!r} range is outside the {frames} frames")
        return self


class RuntimeAnimationEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None
    frame_durations_ms: tuple[DURATION_MS, ...]
    tags: tuple[AnimationTag, ...] = ()

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class RuntimeAnimation(StoreRecord):
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"

    record_type: Literal["runtime_animation"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    entries: tuple[RuntimeAnimationEntry, ...]  # only the keys whose source has animation, sorted by key and detail
