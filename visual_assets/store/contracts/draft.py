"""`DraftSet` and `SetAdoptionRecord`: durable, reviewable sets of unadopted drafts, and the one human decision that adopts a reviewed set.

A draft set lives in git OUTSIDE the catalog (`visual_assets/drafts/<set_id>/`). It records no approval: it is a candidate collection the human reviews as a
whole later. Its entries name a slot (a visual key, plus a detail value when the key declares a detail axis), the source asset id the entry will be
adopted as, and two hashes: the preview's pixels and the intake result. The source's hash is not repeated here: it is bound through
the chain source bytes -> the staged-file hash inside the kept `intake_result.json` -> `intake_hash`, which keeps a full set under the ordinary record bound. `adopt-set` re-proves every entry against Aseprite and then
writes one ordinary `AdoptionRecord` per entry plus one `SetAdoptionRecord`, which binds the decision to the exact bytes of the set the human reviewed
(`draft_set_hash`). Neither record changes what an adoption, a release or a runtime manifest means.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import BoundedText, PersonText, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue
from visual_assets.store.identities import (
    AdoptionId,
    DraftId,
    DraftSetId,
    FileHash,
    PixelHash,
    SetAdoptionId,
    SourceAssetId,
    UtcTimestamp,
    VisualKey,
)


def _slots(entries) -> list[tuple[str, str]]:
    return [(e.visual_key, e.detail or "") for e in entries]


class DraftEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None  # None = the key's declared default (or the key itself when it has no axis), as in `AdoptionRecord.detail_value`
    source_asset_id: SourceAssetId  # the id the entry is adopted under; settled when the draft is kept, so a collision shows early
    draft_id: DraftId  # the intake the draft was kept from; also the entry's folder name
    pixel_hash: PixelHash  # pixels-v1 of the preview PNG: the image the human reviews
    intake_hash: FileHash  # hash of the exact IntakeResult bytes kept beside the entry

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class DraftSet(StoreRecord):
    record_type: Literal["draft_set"]
    schema_version: Literal[1]
    set_id: DraftSetId
    entries: tuple[DraftEntry, ...]

    @model_validator(mode="after")
    def _entries(self) -> DraftSet:
        if len(self.entries) > config.MAX_DRAFT_SET_ENTRIES:
            raise ValueError(f"more than {config.MAX_DRAFT_SET_ENTRIES} entries")
        slots = _slots(self.entries)
        if len(set(slots)) != len(slots):
            raise ValueError("a draft set has one entry per slot")
        if slots != sorted(slots):
            raise ValueError("draft entries must be sorted by visual key, then detail")
        for name, values in (("draft id", [e.draft_id for e in self.entries]), ("source asset id", [e.source_asset_id for e in self.entries])):
            if len(set(values)) != len(values):
                raise ValueError(f"every entry needs its own {name}")
        return self


class SetAdoptedEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None
    adoption_id: AdoptionId
    intake_id: DraftId

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class SetAdoptionRecord(StoreRecord):
    record_type: Literal["set_adoption_record"]
    schema_version: Literal[1]
    set_adoption_id: SetAdoptionId
    set_id: DraftSetId
    draft_set_hash: FileHash  # hash of the exact DraftSet bytes the human reviewed and the command adopted
    review_evidence_ref: BoundedText  # what the human reviewed (stated by them, e.g. a preview page); free text, never taken from a draft
    approver_name: PersonText
    approver_role: PersonText
    decided_at: UtcTimestamp
    entries: Annotated[tuple[SetAdoptedEntry, ...], Field(min_length=1)]
    size_bound: ClassVar[str] = "MAX_RECORD_BYTES"  # 256 entries fit the ordinary record bound (docs/assets/budgets.md)

    @model_validator(mode="after")
    def _entries(self) -> SetAdoptionRecord:
        if len(self.entries) > config.MAX_DRAFT_SET_ENTRIES:
            raise ValueError(f"more than {config.MAX_DRAFT_SET_ENTRIES} entries")
        slots = _slots(self.entries)
        if len(set(slots)) != len(slots) or slots != sorted(slots):
            raise ValueError("set adoption entries are unique and sorted by visual key, then detail")
        return self
