"""`ReviewRenderCheck`: the store's own rendering of a candidate's source compared with the producer's preview.

A human reviews `preview.png` but adopts `source.aseprite`; intake cannot prove the preview depicts the source. The store therefore renders the
staged source itself (sandboxed Aseprite) at the preview's scale and compares decoded-pixel hashes. This record is the result. It is evidence for the
human; `adopt` never trusts a stored copy on its own, it re-renders at adoption time and compares again.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from visual_assets.store.contracts.base import BoundedText, StoreRecord
from visual_assets.store.identities import FileHash, IntakeId, PixelHash, UtcTimestamp


class RenderVerdict(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"


class ReviewRenderCheck(StoreRecord):
    record_type: Literal["review_render_check"]
    schema_version: Literal[1]
    intake_id: IntakeId
    source_hash: FileHash
    producer_preview_hash: FileHash
    rendered_png_hash: FileHash
    producer_pixel_hash: PixelHash
    rendered_pixel_hash: PixelHash
    scale: Annotated[int, Field(ge=1, le=16)]
    verdict: RenderVerdict
    tool_name: BoundedText
    tool_version: BoundedText
    created_at: UtcTimestamp

    @model_validator(mode="after")
    def _verdict_follows_the_hashes(self) -> ReviewRenderCheck:
        same = self.producer_pixel_hash == self.rendered_pixel_hash
        if same != (self.verdict is RenderVerdict.MATCH):
            raise ValueError("the verdict is MATCH exactly when the two pixel hashes are equal")
        return self
