"""`adopt`: the human gate that turns an intake-passed candidate into a new immutable source revision.

HUMAN-GATED: no agent or MCP tool may call this (the boundary test forbids the drawing server from importing it). Every
refusal has its own `GateError.code` and happens before anything is written; `confirm` is asked last, after every other
check, and the files are then published all together or not at all (`catalogwrite.publish`). The licence state and its
evidence come ONLY from the human's own arguments, never from the producer's package, and a name is recorded, not
authenticated (the terminal check and typed id stop accidents and scripts, not impersonation).
"""

from __future__ import annotations

from pydantic import ValidationError

from visual_assets.store import config, records, rendering
from visual_assets.store.catalog.registry import Registry, load_registry
from visual_assets.store.catalogwrite import Confirm, publish
from visual_assets.store.contracts import (
    AdoptionRecord,
    CandidateHandoffPackage,
    ContractError,
    ReviewRenderCheck,
    SourceRecord,
    canonical_json,
    parse_record,
)
from visual_assets.store.contracts.base import Evidence, IntakeVerdict, LicenceState
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.contracts.handoff import SourceFormat
from visual_assets.store.errors import GateError, IdentityError, IntakeError, RegistryError, RenderError, StageError
from visual_assets.store.identities import IntakeId, SourceAssetId, SourceRevision, UtcTimestamp, check, next_revision
from visual_assets.store.intake import quarantine, service, validator

PREVIEW_WARNING = (
    "WARNING: you are adopting source.aseprite, but a human reviews preview.png. Until the store renders the review image itself "
    "(planned: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE) nothing proves the preview depicts this source."
)
_MARKERS = {marker.value for marker in Evidence}


def _refuse(code: str, message: str) -> GateError:
    return GateError(code, message)


def _arg(tp, value, code: str, what: str):
    try:
        return check(tp, value)
    except IdentityError:
        raise _refuse(code, f"{what} is not valid") from None


def _lineage(source_asset_id: str, new: bool, parent: str | None) -> tuple[str, str | None]:
    """(revision to create, its parent) under the explicit choice the human made."""
    if new == (parent is not None):
        raise _refuse("invalid_mode", "choose exactly one of: a new source asset (new) or a parent revision (parent)")
    existing = records.list_revisions(source_asset_id)
    if new:
        if existing or (records.sources_dir() / source_asset_id).exists():
            raise _refuse("source_asset_exists", f"{source_asset_id} already exists; name its latest unrevoked revision as the parent")
        return "r0001", None
    _arg(SourceRevision, parent, "invalid_parent", "the parent revision")
    if not existing:
        raise _refuse("unknown_source_asset", f"{source_asset_id} does not exist; adopt it as a new source asset")
    revoked = records.revoked_revisions(source_asset_id)
    live = [revision for revision in existing if revision not in revoked]
    if not live:
        raise _refuse("all_revisions_revoked", f"every revision of {source_asset_id} is revoked; adopt under a new id")
    if parent != live[-1]:
        raise _refuse("parent_not_latest_unrevoked", f"the parent must be the latest unrevoked revision, {live[-1]}, not {parent}")
    try:
        return next_revision(existing[-1]), parent
    except IdentityError:
        raise _refuse("revision_limit", f"{source_asset_id} has no revision numbers left") from None


def _verify_store_render(
    intake_id: str, directory, files: quarantine.PackageFiles, staged: dict[str, str], renderer: rendering.RenderTool | None
) -> bytes:
    """The store's own render of the staged source must match the producer's preview, re-done NOW.

    A file in the gitignored quarantine can be written by any local process, so a stored check is evidence for the human, never the gate. This
    re-renders at adoption time and compares again, and also requires the review-time check to describe the very image being adopted (`stale` otherwise).
    Returns the exact stored check bytes (they are copied into the tracked provenance and hashed into the AdoptionRecord).
    """
    if renderer is None:
        raise _refuse("renderer_unavailable", "adopt needs the store's own render of the source (Aseprite), and none is available on this machine")
    try:
        stored_bytes = quarantine.read_one(directory, quarantine.RENDER_CHECK_FILE)
    except StageError as exc:
        if exc.code == "missing_file":
            raise _refuse("review_render_missing", f"{intake_id} has no store-rendered review; run `review` where Aseprite is available") from None
        raise _refuse("review_render_corrupt", f"the stored render check cannot be read safely ({exc.code})") from None
    try:
        stored = parse_record(ReviewRenderCheck, stored_bytes)
    except ContractError as exc:
        raise _refuse("review_render_corrupt", f"the stored render check is invalid ({exc.code})") from None
    if (stored.intake_id, stored.source_hash, stored.producer_preview_hash) != (intake_id, staged["source.aseprite"], staged["preview.png"]):
        raise _refuse("review_render_stale", "the stored render check describes different bytes than the ones being adopted; review again")
    try:
        now = rendering.compare_preview(
            intake_id=intake_id, source=files.source, preview=files.preview, tool=renderer, created_at=stored.created_at
        )
    except RenderError as exc:
        raise _refuse(exc.code, exc.message) from None
    if now.check.verdict is RenderVerdict.MISMATCH or stored.verdict is RenderVerdict.MISMATCH:
        raise _refuse("preview_mismatch", "the store's own render of the source does not match the producer's preview; this candidate cannot be adopted")
    if now.check.rendered_pixel_hash != stored.rendered_pixel_hash:
        raise _refuse("review_render_stale", "the image the human reviewed is not the image the source renders to now; review again")
    return stored_bytes


def adopt(
    intake_id: str,
    *,
    visual_key: str,
    approver: str,
    approver_role: str,
    licence_state: str,
    licence_evidence_ref: str,
    source_asset_id: str,
    new: bool = False,
    parent: str | None = None,
    decided_at: str,
    confirm: Confirm,
    registry: Registry | None = None,
    renderer: rendering.RenderTool | None = None,
) -> AdoptionRecord:
    """Adopt `intake_id` as a new revision of `source_asset_id`. Raises `GateError`; writes only on success."""
    _arg(UtcTimestamp, decided_at, "bad_decided_at", "decided_at")
    _arg(SourceAssetId, source_asset_id, "invalid_source_asset_id", "the source asset id")

    try:
        result = service.show(intake_id)
    except IntakeError as exc:
        raise _refuse(exc.code, exc.message) from None
    if result.verdict is not IntakeVerdict.PASSED:
        raise _refuse("intake_not_passed", f"{intake_id} is {result.verdict.value}; only a PASSED intake can be adopted")
    if records.intake_revoked_locally(intake_id):
        raise _refuse("intake_revoked", f"{intake_id} was revoked")

    directory = config.QUARANTINE_ROOT / intake_id
    try:
        files = quarantine.read_directory(directory, extra_allowed=quarantine.EXTRA_FILES)
        result_bytes = quarantine.read_one(directory, quarantine.RESULT_FILE)
    except StageError as exc:
        if exc.code == "oversize_file" and "source.aseprite" in exc.message:
            raise _refuse("source_too_large", f"the source exceeds {config.MAX_SOURCE_BYTES} bytes (ADR D2: sources are committed without Git LFS)") from None
        raise _refuse("staged_bytes_unreadable", f"the staged files of {intake_id} cannot be read safely ({exc.code})") from None
    staged = {
        "package.json": validator.file_hash(files.package),
        "source.aseprite": validator.file_hash(files.source),
        "preview.png": validator.file_hash(files.preview),
    }
    if {f.name: f.file_hash for f in result.staged_files} != staged or staged["package.json"] != result.package_hash:
        raise _refuse("staged_bytes_changed", f"the staged bytes of {intake_id} no longer match the recorded intake hashes")

    try:
        existing = records.find_adoption_for_intake(intake_id)
        if existing is not None:
            if existing.source_revision in records.revoked_revisions(existing.source_asset_id):
                raise _refuse("adoption_revoked", f"{intake_id} was adopted as {existing.source_asset_id} {existing.source_revision}, which is revoked")
            raise _refuse("already_adopted", f"{intake_id} was already adopted as {existing.source_asset_id} {existing.source_revision}")
    except (StageError, ContractError) as exc:
        raise _refuse("catalog_unreadable", f"an adoption record could not be read ({exc.code})") from None

    try:  # the SAME BYTES must not reach the catalog through another intake (R4): not after a revocation, not twice
        copies = records.revisions_with_source_hash(staged["source.aseprite"])
        revoked_copies = [(sid, rev) for sid, rev in copies if rev in records.revoked_revisions(sid)]
        local_copy = records.locally_revoked_source_hashes().get(staged["source.aseprite"])
    except (StageError, ContractError) as exc:
        raise _refuse("catalog_unreadable", f"existing records could not be read ({exc.code})") from None
    if revoked_copies:
        sid, rev = revoked_copies[0]
        raise _refuse("source_bytes_revoked", f"these exact bytes are revoked revision {sid} {rev}; a revocation cannot be sidestepped by a new intake")
    if local_copy is not None and local_copy != intake_id:
        raise _refuse("source_bytes_revoked", f"these exact bytes belong to {local_copy}, which was revoked on this machine")
    if copies:
        sid, rev = copies[0]
        raise _refuse("duplicate_source", f"these exact bytes are already adopted as {sid} {rev}; adopt a genuinely different source")

    try:
        known = (registry if registry is not None else load_registry()).keys
    except RegistryError as exc:
        raise _refuse("registry_unreadable", str(exc)) from None
    if visual_key not in known:
        raise _refuse("unknown_visual_key", "the visual key is not in the registry (keys are never registered dynamically)")
    try:
        holders = [holder for holder in records.key_holders(visual_key) if holder != source_asset_id]
    except (StageError, ContractError) as exc:
        raise _refuse("catalog_unreadable", f"existing records could not be read ({exc.code})") from None
    if holders:
        raise _refuse("visual_key_taken", f"{holders[0]} already holds this visual key; revoke its revisions first to replace it")

    state = getattr(licence_state, "value", licence_state)
    if state != LicenceState.CLEARED.value:
        raise _refuse("licence_not_cleared", f"only a CLEARED licence can be adopted (got {state!r}); the licence review is U-02")
    if not isinstance(licence_evidence_ref, str) or licence_evidence_ref in _MARKERS or not licence_evidence_ref:
        raise _refuse("licence_evidence_missing", "give a real licence evidence reference, not NOT_APPLICABLE, UNAVAILABLE or empty")
    if not approver or not approver.strip() or not approver_role or not approver_role.strip():
        raise _refuse("invalid_approver", "an approver name and role are required")

    try:
        revision, parent_revision = _lineage(source_asset_id, new, parent)
    except (StageError, ContractError) as exc:
        raise _refuse("catalog_unreadable", f"existing records could not be read ({exc.code})") from None
    review_bytes = _verify_store_render(intake_id, directory, files, staged, renderer)

    try:
        package = parse_record(CandidateHandoffPackage, files.package)
    except ContractError as exc:
        raise _refuse("staged_package_invalid", f"the staged package.json no longer parses ({exc.code})") from None

    ad_id = records.adoption_id_for(intake_id, source_asset_id, revision)
    try:
        adoption = AdoptionRecord(
            record_type="adoption_record", schema_version=1, adoption_id=ad_id, intake_id=intake_id,
            intake_hash=validator.file_hash(result_bytes), review_hash=validator.file_hash(review_bytes),
            candidate_id=result.candidate_id,
            approver_name=approver, approver_role=approver_role, source_hash=staged["source.aseprite"],
            source_asset_id=source_asset_id, source_revision=revision, parent_revision=parent_revision,
            visual_key=visual_key, licence_state=LicenceState.CLEARED, licence_evidence_ref=licence_evidence_ref,
            decided_at=decided_at,
        )
        adoption_bytes = canonical_json(adoption)
        source = SourceRecord(
            record_type="source_record", schema_version=1, source_asset_id=source_asset_id, source_revision=revision,
            source_hash=staged["source.aseprite"], parent_revision=parent_revision, adoption_id=ad_id,
            adoption_hash=validator.file_hash(adoption_bytes), source_format=SourceFormat.ASEPRITE,
            width=package.width, height=package.height,
        )
        source_bytes = canonical_json(source)
    except (ValidationError, ContractError) as exc:
        detail = exc.errors()[0]["loc"] if isinstance(exc, ValidationError) else exc.code
        raise _refuse("invalid_argument", f"an argument is not acceptable ({detail})") from None

    notices = (
        PREVIEW_WARNING,
        f"adopt {intake_id} as {source_asset_id} {revision}" + (f" (parent {parent_revision})" if parent_revision else " (new source asset)"),
        "the store re-rendered the source just now and its pixels MATCH the producer's preview",
        f"visual key {visual_key}; licence recorded as CLEARED, evidence {licence_evidence_ref!r} (stated by you, not taken from the package)",
        f"approver {approver!r} ({approver_role}); recorded, not authenticated",
    )
    if not confirm(intake_id, notices):
        raise _refuse("not_confirmed", "the adoption was not confirmed; nothing was written")

    aseprite_path, record_path = records.source_paths(source_asset_id, revision)
    publish([
        (aseprite_path, files.source),
        (records.intake_dir() / f"{intake_id}.json", result_bytes),
        (records.review_copy_path(intake_id), review_bytes),
        (records.adoptions_dir() / f"{ad_id}.json", adoption_bytes),
        (record_path, source_bytes),  # last: the SourceRecord is what makes the revision exist
    ])
    return adoption
