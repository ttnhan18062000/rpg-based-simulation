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

from pydantic import AfterValidator, Field, StringConstraints, model_serializer, model_validator

from visual_assets.store import config
from visual_assets.store.contracts.base import BoundedText, PersonText, StoreRecord, drop_absent
from visual_assets.store.contracts.definitions import AxisValue, Family
from visual_assets.store.contracts.runtime import RuntimeDetail, RuntimeFile
from visual_assets.store.identities import (
    AdoptionId,
    DraftId,
    DraftSetId,
    FileHash,
    PixelHash,
    SetAdoptionId,
    SourceAssetId,
    SourceRevision,
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
    # ADR D22: present = the NEXT revision of the existing source asset `source_asset_id`, whose latest unrevoked revision was this one when the draft was kept (`draft keep --revises`).
    # Absent = a new source asset, as before, so a set without revisions serialises byte-identically to what it always did.
    parent_revision: SourceRevision | None = None

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail", "parent_revision")


DropReason = Annotated[BoundedText, StringConstraints(max_length=80)]


class DroppedDraft(StoreRecord):
    """The record that a draft was removed from its set by `draft drop` (ADR D22): the slot, the intake it held and why. The reason is the person's own text, never evidence."""

    visual_key: VisualKey
    detail: AxisValue | None = None
    draft_id: DraftId
    reason: DropReason

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail")


class DraftSet(StoreRecord):
    record_type: Literal["draft_set"]
    schema_version: Literal[1]
    set_id: DraftSetId
    entries: tuple[DraftEntry, ...]
    dropped: tuple[DroppedDraft, ...] = ()  # drops of this set, oldest first; omitted when empty so a set that never lost a draft keeps its bytes (and its recorded hash)

    @model_serializer(mode="wrap")
    def _omit_empty_dropped(self, handler):  # type: ignore[no-untyped-def]
        data = handler(self)
        if not data.get("dropped"):
            data.pop("dropped", None)
        return data

    @model_validator(mode="after")
    def _entries(self) -> DraftSet:
        if len(self.entries) > config.MAX_DRAFT_SET_ENTRIES:
            raise ValueError(f"more than {config.MAX_DRAFT_SET_ENTRIES} entries")
        slots = _slots(self.entries)
        if len(set(slots)) != len(slots):
            raise ValueError("a draft set has one entry per slot")
        if slots != sorted(slots):
            raise ValueError("draft entries must be sorted by visual key, then detail")
        if len(self.dropped) > config.MAX_DROPPED_DRAFTS:
            raise ValueError(f"more than {config.MAX_DROPPED_DRAFTS} dropped drafts")
        kept_ids = {e.draft_id for e in self.entries}
        dropped_ids = [x.draft_id for x in self.dropped]
        if len(set(dropped_ids)) != len(dropped_ids) or kept_ids & set(dropped_ids):
            raise ValueError("a dropped draft is listed once and is not also kept")
        for name, values in (("draft id", [e.draft_id for e in self.entries]), ("source asset id", [e.source_asset_id for e in self.entries])):
            if len(set(values)) != len(values):
                raise ValueError(f"every entry needs its own {name}")
        return self


class SetAdoptedEntry(StoreRecord):
    visual_key: VisualKey
    detail: AxisValue | None = None
    adoption_id: AdoptionId
    intake_id: DraftId
    parent_revision: SourceRevision | None = None  # ADR D22: present for a revision of an existing source asset (the same value the AdoptionRecord holds), absent for a new one

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail", "parent_revision")


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


def _preview_dim(value: int) -> int:
    if not 1 <= value <= config.MAX_PREVIEW_DIM:
        raise ValueError(f"a preview dimension is 1..{config.MAX_PREVIEW_DIM}")
    return value


PreviewDimension = Annotated[int, AfterValidator(_preview_dim)]


def _only_true(value: bool) -> bool:
    if value is not True:
        raise ValueError("`adopted` is only ever the literal true")
    return value


class DraftPreviewEntry(StoreRecord):
    visual_key: VisualKey
    family: Family
    detail: AxisValue | None = None
    source_asset_id: SourceAssetId
    draft_id: DraftId
    pixel_hash: PixelHash  # of the preview PNG: the image a reviewer sees, the same hash the DraftSet entry holds
    file: RuntimeFile  # `<64 hex>.png`, derived from `pixel_hash`
    width: PreviewDimension  # of the preview PNG, in pixels
    height: PreviewDimension
    scale: Annotated[int, Field(ge=1, le=16)]  # the preview is the tile at this whole-number scale: the page draws it at 1/scale, smoothing off
    # Only in this export, never in a DraftSet: a live ADOPTED slot the set does not hold, shown so the map is complete. It is a reference to catalog art, not a draft under
    # review; the page labels it "adopted (reference)". Always the literal `true`, omitted otherwise.
    adopted: Annotated[bool, AfterValidator(_only_true)] | None = None

    @model_serializer(mode="wrap")
    def _omit_absent_detail(self, handler):  # type: ignore[no-untyped-def]
        return drop_absent(handler(self), "detail", "adopted")

    @model_validator(mode="after")
    def _rules(self) -> DraftPreviewEntry:
        if self.file != self.pixel_hash.split(":", 1)[1] + ".png":
            raise ValueError("file must be the pixel hash's hex digest plus .png")
        if self.width % self.scale or self.height % self.scale:
            raise ValueError("the preview size must be a whole multiple of its scale")
        return self


class DraftPreviewManifest(StoreRecord):
    """What the isolated preview page loads to show one draft set. A record type of its own: it is never a `runtime_manifest` (the type and a
    required `set_id` / `draft_set_hash` make each unparseable as the other, in Python and in the client), so nothing a release or the pilot page reads can load it."""

    record_type: Literal["draft_preview_manifest"]
    schema_version: Literal[1]
    set_id: DraftSetId
    draft_set_hash: FileHash  # the file hash of the exact `draft_set.json` bytes: the same value `adopt-set` prints in its confirmation
    registry_hash: FileHash
    entries: tuple[DraftPreviewEntry, ...]
    details: tuple[RuntimeDetail, ...] = ()  # the declared axis of each key that declares one and has an entry, as in the runtime manifest
    size_bound: ClassVar[str] = "MAX_MANIFEST_BYTES"  # a manifest-class export: 256 maximum-length entries do not fit the ordinary record bound

    @model_serializer(mode="wrap")
    def _omit_empty_details(self, handler):  # type: ignore[no-untyped-def]
        data = handler(self)
        if not data.get("details"):
            data.pop("details", None)
        return data

    @model_validator(mode="after")
    def _entries(self) -> DraftPreviewManifest:
        if len(self.entries) > config.MAX_DRAFT_SET_ENTRIES:
            raise ValueError(f"more than {config.MAX_DRAFT_SET_ENTRIES} entries")
        slots = _slots(self.entries)
        if len(set(slots)) != len(slots) or slots != sorted(slots):
            raise ValueError("preview entries are unique and sorted by visual key, then detail")
        declared = [d.visual_key for d in self.details]
        if len(set(declared)) != len(declared) or declared != sorted(declared) or len(declared) > config.MAX_DETAIL_KEYS:
            raise ValueError("details must be unique, sorted by visual key and at most MAX_DETAIL_KEYS")
        values = {d.visual_key: d.values for d in self.details}
        defaults = {d.visual_key: d.default for d in self.details}
        for entry in self.entries:
            if entry.detail is not None and entry.visual_key not in values:
                raise ValueError("an entry names a detail value for a key with no declared axis")
            if entry.detail is not None and entry.detail not in values[entry.visual_key]:
                raise ValueError("an entry's detail value must be one of its key's declared values")
        effective = [(e.visual_key, e.detail if e.detail is not None else defaults.get(e.visual_key)) for e in self.entries]
        if len(set(effective)) != len(effective):
            raise ValueError("two entries fill one slot (no detail value means the key's declared default)")
        return self
