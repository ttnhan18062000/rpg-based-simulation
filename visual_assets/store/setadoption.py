"""`adopt-set`: the human gate that adopts one REVIEWED draft set in one decision (AM-F01 keeps its human gate; its unit becomes a reviewed set).

HUMAN-GATED: no agent or MCP tool may call this (the boundary test forbids the drawing server from importing it). For every entry of the set it re-proves, with
the store's own Aseprite NOW, that the draft's source renders to exactly the draft's preview (a hard refusal on any mismatch, no stored check is trusted), and
runs the same checks `adopt` runs (staged bytes, the same bytes not adopted or revoked, the key and detail slot declared and free, the licence and approver). It
then shows ONE confirmation listing every entry, the DraftSet's file hash and the evidence the human states, and writes all files together or none: per entry the
source, the intake result copy, a fresh ReviewRenderCheck, an ordinary `AdoptionRecord` and a `SourceRecord`, then one `SetAdoptionRecord` binding the decision to
the exact bytes of the set. Entries are always NEW source assets; replacing a held slot means revoking it first, as with `adopt`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from visual_assets.store import adoption, drafts, records, rendering
from visual_assets.store.catalog.registry import Registry
from visual_assets.store.catalogwrite import Confirm, publish
from visual_assets.store.contracts import CandidateHandoffPackage, ContractError, SetAdoptionRecord, canonical_json, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.draft import SetAdoptedEntry
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.errors import DraftError, GateError, RenderError, StageError
from visual_assets.store.identities import SetAdoptionId, SourceAssetId, UtcTimestamp, check
from visual_assets.store.intake import validator

def set_adoption_id_for(set_id: str, draft_set_hash: str) -> str:
    return "sa-" + hashlib.sha256("\n".join((set_id, draft_set_hash)).encode()).hexdigest()[:16]


def _refuse(code: str, message: str) -> GateError:
    return GateError(code, message)


def adopt_set(
    set_id: str,
    *,
    approver: str,
    approver_role: str,
    licence_state: str,
    licence_evidence_ref: str,
    review_evidence_ref: str,
    decided_at: str,
    confirm: Confirm,
    registry: Registry | None = None,
    renderer: rendering.RenderTool | None = None,
    drafts_root: Path | None = None,
) -> SetAdoptionRecord:
    """Adopt every entry of `set_id` or nothing. Raises `GateError`; writes only on success."""
    try:
        check(UtcTimestamp, decided_at)
    except Exception:
        raise _refuse("bad_decided_at", "decided_at is not valid") from None
    adoption.check_licence_and_approver(licence_state, licence_evidence_ref, approver, approver_role)
    if not isinstance(review_evidence_ref, str) or not review_evidence_ref.strip():
        raise _refuse("review_evidence_missing", "state what you reviewed (--review-evidence), for example the preview page of this set")
    if renderer is None:
        raise _refuse("renderer_unavailable", "adopt-set needs the store's own render of every source (Aseprite), and none is available on this machine")

    try:
        record, set_bytes = drafts.load_set(set_id, drafts_root)
    except DraftError as exc:
        raise _refuse(exc.code, exc.message) from None
    findings = drafts.verify_set(set_id, registry=registry, root=drafts_root)
    if findings:
        raise _refuse("draft_set_invalid", f"{len(findings)} problem(s) in the draft set, first {findings[0].code}: {findings[0].detail}")
    if not record.entries:
        raise _refuse("empty_set", f"{set_id} has no entries")
    draft_set_hash = validator.file_hash(set_bytes)

    to_publish: list[tuple[Path, bytes]] = []
    adopted: list[SetAdoptedEntry] = []
    seen_slots: set[tuple[str, str | None]] = set()
    seen_bytes: set[str] = set()
    lines: list[str] = []
    for entry in record.entries:
        try:
            files = drafts.read_entry(set_id, entry, drafts_root)
        except DraftError as exc:
            raise _refuse(exc.code, exc.message) from None
        try:
            if records.find_adoption_for_intake(entry.draft_id) is not None:
                raise _refuse("already_adopted", f"{entry.draft_id} was already adopted")
        except (StageError, ContractError) as exc:
            raise _refuse("catalog_unreadable", f"an adoption record could not be read ({exc.code})") from None
        source_hash = validator.file_hash(files.source)
        adoption.check_source_bytes_are_new(entry.draft_id, source_hash)
        _, slot, slot_name = adoption.check_slot(registry, entry.visual_key, entry.detail, entry.source_asset_id)
        # nothing of this set is written yet, so the catalog checks above cannot see the set's own earlier entries
        if (entry.visual_key, slot) in seen_slots:
            raise _refuse("duplicate_slot", f"two entries of {set_id} fill {slot_name}")
        if source_hash in seen_bytes:
            raise _refuse("duplicate_source", f"two entries of {set_id} have the same source bytes")
        seen_slots.add((entry.visual_key, slot))
        seen_bytes.add(source_hash)
        try:
            check(SourceAssetId, entry.source_asset_id)
        except Exception:
            raise _refuse("invalid_source_asset_id", f"{entry.source_asset_id!r} is not valid") from None
        revision, parent = adoption.new_source_asset(entry.source_asset_id)

        try:
            comparison = rendering.compare_preview(intake_id=entry.draft_id, source=files.source, preview=files.preview, tool=renderer, created_at=decided_at)
        except RenderError as exc:
            raise _refuse(exc.code, f"{entry.draft_id}: {exc.message}") from None
        if comparison.check.verdict is RenderVerdict.MISMATCH or comparison.check.rendered_pixel_hash != entry.pixel_hash:
            raise _refuse("preview_mismatch", f"{entry.draft_id} ({slot_name}): the store's own render of the source does not match the draft's preview; this set cannot be adopted")
        review_bytes = canonical_json(comparison.check)
        try:
            package = parse_record(CandidateHandoffPackage, files.package)
        except ContractError as exc:
            raise _refuse("staged_package_invalid", f"{entry.draft_id}: package.json no longer parses ({exc.code})") from None
        if files.result.verdict is not IntakeVerdict.PASSED:
            raise _refuse("intake_not_passed", f"{entry.draft_id} is not PASSED")

        ad_id, _adoption, adoption_bytes, source_bytes = adoption.build_entry_records(
            intake_id=entry.draft_id, result=files.result, result_bytes=files.result_bytes, review_bytes=review_bytes,
            source_hash=source_hash, package=package, source_asset_id=entry.source_asset_id, revision=revision,
            parent_revision=parent, visual_key=entry.visual_key, detail_value=entry.detail, licence_evidence_ref=licence_evidence_ref,
            approver=approver, approver_role=approver_role, decided_at=decided_at,
        )
        aseprite_path, record_path = records.source_paths(entry.source_asset_id, revision)
        to_publish += [
            (aseprite_path, files.source),
            (records.intake_dir() / f"{entry.draft_id}.json", files.result_bytes),
            (records.review_copy_path(entry.draft_id), review_bytes),
            (records.adoptions_dir() / f"{ad_id}.json", adoption_bytes),
            (record_path, source_bytes),
        ]
        adopted.append(SetAdoptedEntry(visual_key=entry.visual_key, detail=entry.detail, adoption_id=ad_id, intake_id=entry.draft_id))
        lines.append(f"  {slot_name}{' (the key\'s default detail value)' if entry.detail is None and slot is not None else ''}: "
                     f"{entry.source_asset_id} {revision} from {entry.draft_id}, the store's render MATCHES the draft preview")

    try:
        sa_id = set_adoption_id_for(set_id, draft_set_hash)
        set_record = SetAdoptionRecord(
            record_type="set_adoption_record", schema_version=1, set_adoption_id=sa_id, set_id=set_id, draft_set_hash=draft_set_hash,
            review_evidence_ref=review_evidence_ref, approver_name=approver, approver_role=approver_role, decided_at=decided_at, entries=tuple(adopted),
        )
        set_bytes_out = canonical_json(set_record)
    except Exception as exc:
        raise _refuse("invalid_argument", f"an argument is not acceptable ({getattr(exc, 'code', type(exc).__name__)})") from None
    to_publish.append((records.set_adoptions_dir() / f"{sa_id}.json", set_bytes_out))

    notices = (
        f"adopt the REVIEWED draft set {set_id}: {len(adopted)} entries, ALL or NONE",
        f"the DraftSet file hash is {draft_set_hash}: check it is the set you reviewed (the preview page shows the same hash)",
        "the store re-rendered every source just now and each render MATCHES its draft preview, pixel for pixel",
        *lines,
        f"licence recorded as CLEARED for every entry, evidence {licence_evidence_ref!r} (stated by you, not taken from any draft)",
        f"what you reviewed: {review_evidence_ref!r} (stated by you)",
        f"approver {approver!r} ({approver_role}); recorded, not authenticated",
    )
    if not confirm(set_id, notices):
        raise _refuse("not_confirmed", "the set adoption was not confirmed; nothing was written")
    publish(to_publish)
    return set_record
