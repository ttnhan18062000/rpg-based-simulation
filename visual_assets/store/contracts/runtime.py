"""`RuntimeManifest`: the small contract the client build consumes from one release candidate (proposal 9.3, Profile A).

It carries exact release identity, artifact hashes, publisher-generated file names (derived from the pixel hash, never a path), decoded
sizes and the fallback-contract version, and nothing from the protected provenance: no approver, source path, licence record, review
note or artifact id. Its size bound is `MAX_MANIFEST_BYTES`, like the candidate manifest it is exported from.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import StringConstraints, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import Dimension, StoreRecord
from visual_assets.store.contracts.definitions import Family
from visual_assets.store.identities import CatalogId, FileHash, PixelHash, ReleaseId, VisualKey

RuntimeFile = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}\.png$")]


class RuntimeEntry(StoreRecord):
    visual_key: VisualKey
    family: Family
    pixel_hash: PixelHash
    file: RuntimeFile  # exactly `<64 hex>.png`, derived from `pixel_hash`
    width: Dimension
    height: Dimension

    @model_validator(mode="after")
    def _file_is_derived(self) -> RuntimeEntry:
        if self.file != self.pixel_hash.split(":", 1)[1] + ".png":
            raise ValueError("file must be the pixel hash's hex digest plus .png")
        return self


class RuntimeManifest(StoreRecord):
    record_type: Literal["runtime_manifest"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    candidate_manifest_hash: FileHash  # of the exact candidate manifest bytes this was exported from
    registry_hash: FileHash
    fallback_contract_version: Literal[1]
    entries: tuple[RuntimeEntry, ...]
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"

    @model_validator(mode="after")
    def _entries(self) -> RuntimeManifest:
        keys = [e.visual_key for e in self.entries]
        if len(set(keys)) != len(keys):
            raise ValueError("runtime entries must have unique visual keys")
        if keys != sorted(keys):
            raise ValueError("runtime entries must be sorted by visual key")
        if len(keys) > config.MAX_VISUAL_KEYS:
            raise ValueError(f"more than {config.MAX_VISUAL_KEYS} entries")
        return self
