"""`revoke` and `is_build_eligible`. HUMAN-GATED like `adopt`: no agent or MCP tool may call `revoke`.

A revocation never deletes anything. Revoking a source revision writes a tracked `provenance/revocations/<id>.json`; revoking
an intake that was never adopted writes `revocation.json` inside its (gitignored) quarantine directory. `is_build_eligible`
is the single function later code asks, and it fails closed: anything it cannot read or prove makes a revision ineligible.
"""

from __future__ import annotations

import hashlib
import re

from pydantic import ValidationError

from visual_assets.store import config, records
from visual_assets.store.catalogwrite import Confirm, publish
from visual_assets.store.contracts import ContractError, RevocationRecord, canonical_json
from visual_assets.store.contracts.adoption import IntakeTarget, SourceRevisionTarget
from visual_assets.store.errors import GateError, IdentityError, StageError, StoreError
from visual_assets.store.identities import IntakeId, SourceAssetId, SourceRevision, UtcTimestamp, check
from visual_assets.store.intake import quarantine

_REVISION_TARGET = re.compile(r"([a-z0-9][a-z0-9_-]{0,63})/(r[0-9]{4})")


def revocation_id_for(kind: str, target: str) -> str:
    return "rv-" + hashlib.sha256(f"{kind}\n{target}".encode()).hexdigest()[:16]


def parse_target(target: str) -> tuple[str, str]:
    """("intake", intake_id) or ("source_revision", "<source_asset_id>/<rNNNN>")."""
    if isinstance(target, str) and target.startswith("in-"):
        try:
            check(IntakeId, target)
        except IdentityError:
            raise GateError("invalid_target", "not a valid intake id") from None
        return "intake", target
    if isinstance(target, str) and _REVISION_TARGET.fullmatch(target):
        sid, rev = target.split("/")
        try:
            check(SourceAssetId, sid)
            check(SourceRevision, rev)
        except IdentityError:
            raise GateError("invalid_target", "not a valid source revision") from None
        return "source_revision", target
    raise GateError("invalid_target", "a target is an intake id (in-...) or <source_asset_id>/<rNNNN>")


def revoke(
    target: str, *, reason: str, approver: str, approver_role: str, decided_at: str, confirm: Confirm
) -> RevocationRecord:
    """Revoke an intake or a source revision. Raises `GateError`; writes only on success."""
    try:
        check(UtcTimestamp, decided_at)
    except IdentityError:
        raise GateError("bad_decided_at", "decided_at must be a real YYYY-MM-DDTHH:MM:SSZ timestamp") from None
    kind, text = parse_target(target)
    rv_id = revocation_id_for(kind, text)

    try:
        if kind == "intake":
            directory = config.QUARANTINE_ROOT / text
            if directory.is_symlink() or not directory.is_dir():
                raise GateError("unknown_target", f"no quarantined intake {text}")
            if records.find_adoption_for_intake(text) is not None or (records.intake_dir() / f"{text}.json").exists():
                raise GateError("intake_adopted", f"{text} was adopted; revoke its source revision instead")
            if records.intake_revoked_locally(text):
                raise GateError("already_revoked", f"{text} is already revoked")
            target_record = IntakeTarget(kind="intake", intake_id=text)
        else:
            sid, rev = text.split("/")
            if rev not in records.list_revisions(sid):
                raise GateError("unknown_target", f"no source revision {text}")
            if rev in records.revoked_revisions(sid):
                raise GateError("already_revoked", f"{text} is already revoked")
            target_record = SourceRevisionTarget(kind="source_revision", source_asset_id=sid, source_revision=rev)
    except (StageError, ContractError) as exc:
        raise GateError("catalog_unreadable", f"existing records could not be read ({exc.code})") from None

    try:
        record = RevocationRecord(
            record_type="revocation_record", schema_version=1, revocation_id=rv_id, target=target_record,
            reason=reason, approver_name=approver, approver_role=approver_role, decided_at=decided_at,
        )
        data = canonical_json(record)
    except (ValidationError, ContractError) as exc:
        detail = exc.errors()[0]["loc"] if isinstance(exc, ValidationError) else exc.code
        raise GateError("invalid_argument", f"an argument is not acceptable ({detail})") from None

    notices = (
        f"revoke {kind.replace('_', ' ')} {text}: this can never be undone and makes it ineligible for build and release; nothing is deleted",
        f"approver {approver!r} ({approver_role}); recorded, not authenticated",
    )
    if not confirm(text, notices):
        raise GateError("not_confirmed", "the revocation was not confirmed; nothing was written")

    if kind == "intake":
        quarantine.write_new(config.QUARANTINE_ROOT / text / quarantine.REVOCATION_FILE, data)
    else:
        publish([(records.revocations_dir() / f"{rv_id}.json", data)])
    return record


def is_build_eligible(source_asset_id: str, revision: str) -> bool:
    """True only for an existing, readable source revision with no revocation. Fails closed on any doubt."""
    return records.is_eligible(source_asset_id, revision)
