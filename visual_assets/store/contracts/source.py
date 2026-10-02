"""`SourceRecord`: one immutable adopted editable-source revision."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from visual_assets.store.contracts.adoption import check_parent
from visual_assets.store.contracts.base import Dimension, StoreRecord
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

    @model_validator(mode="after")
    def _parent(self) -> SourceRecord:
        check_parent(self.source_revision, self.parent_revision)
        return self
