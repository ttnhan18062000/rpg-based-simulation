"""`ReleaseCandidateManifest`: an immutable candidate set. Nothing here names or implies an active release (D6)."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import StoreRecord
from visual_assets.store.identities import ArtifactId, CatalogId, FileHash, PixelHash, ReleaseId, VisualKey


class ReleaseEntry(StoreRecord):
    visual_key: VisualKey
    artifact_id: ArtifactId
    pixel_hash: PixelHash


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
        keys = [e.visual_key for e in self.entries]
        if len(set(keys)) != len(keys):
            raise ValueError("release entries must have unique visual keys")
        if len(keys) > config.MAX_VISUAL_KEYS:
            raise ValueError(f"more than {config.MAX_VISUAL_KEYS} entries")
        return self
