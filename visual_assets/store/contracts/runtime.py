"""`RuntimeManifest`: the small contract the client build consumes from one release candidate (proposal 9.3, Profile A).

It carries exact release identity, artifact hashes, publisher-generated file names (derived from the pixel hash, never a path), decoded
sizes and the fallback-contract version, and nothing from the protected provenance: no approver, source path, licence record, review
note or artifact id. Its size bound is `MAX_MANIFEST_BYTES`, like the candidate manifest it is exported from.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import StringConstraints, model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import Dimension, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue, DetailAxis, Family
from visual_assets.store.identities import CatalogId, FileHash, PixelHash, ReleaseId, VisualKey

RuntimeFile = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}\.png$")]


class RuntimeEntry(StoreRecord):
    visual_key: VisualKey
    family: Family
    pixel_hash: PixelHash
    file: RuntimeFile  # exactly `<64 hex>.png`, derived from `pixel_hash`
    width: Dimension
    height: Dimension
    detail: AxisValue | None = None  # the slot's detail value; present exactly for a key listed in the manifest's `details`

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")

    @model_validator(mode="after")
    def _file_is_derived(self) -> RuntimeEntry:
        if self.file != self.pixel_hash.split(":", 1)[1] + ".png":
            raise ValueError("file must be the pixel hash's hex digest plus .png")
        return self


class RuntimeDetail(DetailAxis):
    """One key's declared detail axis, copied from the registry: the client picks over these DECLARED values, so adding art for a declared value never reshuffles the map."""

    visual_key: VisualKey


class RuntimeManifest(StoreRecord):
    record_type: Literal["runtime_manifest"]
    schema_version: Literal[1]
    catalog_id: CatalogId
    release_id: ReleaseId
    candidate_manifest_hash: FileHash  # of the exact candidate manifest bytes this was exported from
    registry_hash: FileHash
    fallback_contract_version: Literal[1]
    entries: tuple[RuntimeEntry, ...]
    details: tuple[RuntimeDetail, ...] = ()  # one per key that declares a detail axis and has an entry, sorted by visual key
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"

    @model_serializer(mode="wrap")
    def _omit_empty_details(self, handler):  # type: ignore[no-untyped-def]
        data = handler(self)
        if not data.get("details"):
            data.pop("details", None)
        return data

    @model_validator(mode="after")
    def _entries(self) -> RuntimeManifest:
        slots = [(e.visual_key, e.detail or "") for e in self.entries]
        if len(set(slots)) != len(slots):
            raise ValueError("runtime entries must have unique (visual key, detail) slots")
        if slots != sorted(slots):
            raise ValueError("runtime entries must be sorted by visual key, then detail")
        if len(slots) > config.MAX_VISUAL_KEYS:
            raise ValueError(f"more than {config.MAX_VISUAL_KEYS} entries")
        declared = [d.visual_key for d in self.details]
        if len(set(declared)) != len(declared) or declared != sorted(declared):
            raise ValueError("details must be unique and sorted by visual key")
        if len(declared) > config.MAX_DETAIL_KEYS:
            raise ValueError(f"more than {config.MAX_DETAIL_KEYS} details")
        values = {d.visual_key: d.values for d in self.details}
        for entry in self.entries:
            if (entry.visual_key in values) != (entry.detail is not None):
                raise ValueError("an entry has a detail value exactly when its key is listed in details")
            if entry.detail is not None and entry.detail not in values[entry.visual_key]:
                raise ValueError("an entry's detail value must be one of its key's declared values")
        return self
