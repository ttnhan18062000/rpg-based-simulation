"""`ReleaseCandidateManifest`: an immutable candidate set, one entry per slot (a visual key, plus a detail value when the key declares a detail axis). Nothing here names or implies an active release (D6)."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue
from visual_assets.store.identities import ArtifactId, CatalogId, FileHash, PixelHash, ReleaseId, VisualKey


class ReleaseEntry(StoreRecord):
    visual_key: VisualKey
    artifact_id: ArtifactId
    pixel_hash: PixelHash
    detail: AxisValue | None = None  # the slot's detail value; None only for a key without a detail axis (the entry is then the key's single slot)

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class ReleaseCandidateManifest(StoreRecord):
    record_type: Literal["release_candidate_manifest"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    registry_hash: FileHash
    entries: tuple[ReleaseEntry, ...]
    status: Literal["CANDIDATE"]
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"  # up to MAX_VISUAL_KEYS entries: far bigger than a small record

    @model_validator(mode="after")
    def _entries(self) -> ReleaseCandidateManifest:
        slots = [(e.visual_key, e.detail or "") for e in self.entries]
        if len(set(slots)) != len(slots):
            raise ValueError("release entries must have unique (visual key, detail) slots")
        if slots != sorted(slots):
            raise ValueError("release entries must be sorted by visual key, then detail")
        if len(slots) > config.MAX_VISUAL_KEYS:
            raise ValueError(f"more than {config.MAX_VISUAL_KEYS} entries")
        return self
