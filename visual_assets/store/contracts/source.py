"""`SourceRecord`: one immutable adopted editable-source revision."""

from __future__ import annotations

from typing import Literal

from pydantic import model_serializer, model_validator

from visual_assets.store.contracts.adoption import check_parent
from visual_assets.store.contracts.animation import SourceAnimation
from visual_assets.store.contracts.base import Dimension, StoreRecord, drop_absent
from visual_assets.store.contracts.handoff import SourceFormat
from visual_assets.store.identities import AdoptionId, FileHash, SourceAssetId, SourceRevision


class SourceRecord(StoreRecord):
    record_type: Literal["source_record"]
    schema_version: Literal[1]
    source_asset_id: SourceAssetId
    source_revision: SourceRevision
    source_hash: FileHash
    parent_revision: SourceRevision | None
    adoption_id: AdoptionId
    adoption_hash: FileHash  # hash of the exact AdoptionRecord bytes; an edited approver no longer matches
    source_format: SourceFormat
    width: Dimension
    height: Dimension
    # derived from the source bytes at adoption (frame durations and tags); omitted for a one-frame source, so every record written before the field existed is byte-identical
    animation: SourceAnimation | None = None

    @model_serializer(mode="wrap")
    def _omit_absent_animation(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "animation")

    @model_validator(mode="after")
    def _parent(self) -> SourceRecord:
        check_parent(self.source_revision, self.parent_revision)
        return self
