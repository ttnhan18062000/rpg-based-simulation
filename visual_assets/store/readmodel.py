"""Read-only, shaped views of the store for agents: intakes, sources, artifacts and release candidates.

Everything returned is a small dict of primitive values: never raw file contents, never an absolute path, and every listing is bounded. Nothing here
writes, and a record that cannot be read is reported as `readable: false` rather than hidden or guessed at. Statements a producer made are labelled as
claims and are never presented as clearances.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from visual_assets.store import config, intake as intake_api, pixels, records
from visual_assets.store.contracts import ArtifactRecord, ReleaseCandidateManifest, parse_record, record_bound
from visual_assets.store.errors import ContractError, IdentityError, IntakeError, ReadError, StageError
from visual_assets.store.identities import IntakeId, ReleaseId, SourceAssetId, SourceRevision, check

KINDS = ("intake", "source", "artifact", "release")
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
_ARTIFACT_RECORD = re.compile(r"([0-9a-f]{64})\.(r[0-9]{4})\.artifact\.json")
_ARTIFACT_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
_INTAKE_ID = re.compile(r"in-[0-9a-f]{16}")  # intake ids always have exactly this shape


def _kind(kind: str) -> str:
    if kind not in KINDS:
        raise ReadError("unknown_kind", f"kind must be one of {', '.join(KINDS)}")
    return kind


def _limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise ReadError("invalid_limit", f"limit must be an integer 1..{MAX_LIMIT}")
    return limit


def _value(value: object) -> Any:
    return getattr(value, "value", value)


def _bounded(items: list[dict], limit: int, extra: dict | None = None) -> dict:
    out = {"count": min(len(items), limit), "truncated": len(items) > limit, "items": items[:limit]}
    out.update(extra or {})
    return out


def list_items(kind: str, limit: int = DEFAULT_LIMIT) -> dict:
    """A bounded listing of one kind. `truncated` says whether more existed than `limit`."""
    kind, limit = _kind(kind), _limit(limit)
    items: list[dict] = []
    extra: dict = {}
    try:
        if kind == "intake":
            results, problems = intake_api.list_results()
            for r in results:
                items.append({
                    "intake_id": r.intake_id, "verdict": r.verdict.value, "candidate_id": r.candidate_id, "created_at": r.created_at,
                    "adopted": (records.intake_dir() / f"{r.intake_id}.json").exists(), "revoked": records.intake_revoked_locally(r.intake_id),
                })
            extra["unreadable"] = len(problems)
        elif kind == "source":
            for sid in records.list_source_ids():
                for rev in records.list_revisions(sid):
                    try:
                        parent = records.load_source(sid, rev).parent_revision
                        readable = True
                    except (StageError, ContractError):
                        parent, readable = None, False
                    items.append({"source_asset_id": sid, "revision": rev, "parent_revision": parent, "readable": readable,
                                  "build_eligible": records.is_eligible(sid, rev)})
        elif kind == "artifact":
            base = records.generated_dir()
            if base.is_dir() and not base.is_symlink():
                for directory in sorted(base.iterdir()):
                    if directory.is_dir() and not directory.is_symlink() and _ARTIFACT_ID.fullmatch(directory.name):
                        for entry in sorted(directory.iterdir()):
                            m = _ARTIFACT_RECORD.fullmatch(entry.name)
                            if m:
                                items.append({"artifact_id": directory.name, "source_revision": m.group(2), "pixel_hash": pixels.HASH_PREFIX + m.group(1)})
        else:
            base = records.manifests_dir()
            if base.is_dir() and not base.is_symlink():
                for directory in sorted(base.iterdir()):
                    if directory.is_dir() and not directory.is_symlink() and _ARTIFACT_ID.fullmatch(directory.name):
                        for path in sorted(directory.glob("rc-*.json")):
                            try:
                                entries = len(parse_record(ReleaseCandidateManifest, records.read_file(path, record_bound(ReleaseCandidateManifest))).entries)
                                readable = True
                            except (StageError, ContractError):
                                entries, readable = None, False
                            items.append({"catalog_id": directory.name, "release_id": path.stem, "entries": entries, "readable": readable, "status": "CANDIDATE"})
    except (StageError, ContractError) as exc:
        raise ReadError("unreadable", f"the store could not be listed ({exc.code})") from None
    return _bounded(items, limit, {"kind": kind, **extra})


def show_item(kind: str, item_id: str) -> dict:
    """One record as a shaped summary. `item_id` is an intake id, `<source_asset_id>/<rNNNN>`, an artifact id, or `<catalog_id>/<rc-NNNN>`."""
    kind = _kind(kind)
    try:
        if kind == "intake":
            return _show_intake(item_id)
        if kind == "source":
            return _show_source(item_id)
        if kind == "artifact":
            return _show_artifact(item_id)
        return _show_release(item_id)
    except (StageError, ContractError) as exc:
        raise ReadError("unreadable", f"that record could not be read ({exc.code})") from None


def _show_intake(item_id: str) -> dict:
    if not isinstance(item_id, str) or not _INTAKE_ID.fullmatch(item_id):
        raise ReadError("invalid_id", "an intake id looks like in-<16 hex>")
    try:
        check(IntakeId, item_id)
        result = intake_api.show(item_id)
    except IdentityError:
        raise ReadError("invalid_id", "not a valid intake id") from None
    except IntakeError as exc:
        raise ReadError("unknown_id" if exc.code == "unknown_intake" else exc.code, exc.message) from None
    claimed = intake_api.claims(item_id)
    return {
        "kind": "intake", "intake_id": result.intake_id, "verdict": result.verdict.value, "candidate_id": result.candidate_id,
        "created_at": result.created_at, "validator_version": result.validator_version,
        "findings": [{"code": f.code.value, "detail": f.detail} for f in result.findings],
        "staged_files": [{"name": f.name, "file_hash": f.file_hash} for f in result.staged_files],
        "adopted": (records.intake_dir() / f"{item_id}.json").exists(), "revoked": records.intake_revoked_locally(item_id),
        "claimed_by_producer": None if claimed is None else {
            "note": "unverified statements by the producer, not a clearance",
            "licence_state": claimed.licence_state.value, "producer_class": claimed.producer_class.value,
            "creator": str(_value(claimed.creator)), "brief_id": str(_value(claimed.brief_id)),
        },
    }


def _show_source(item_id: str) -> dict:
    sid, _, rev = item_id.partition("/")
    try:
        check(SourceAssetId, sid)
        check(SourceRevision, rev)
    except IdentityError:
        raise ReadError("invalid_id", "a source id looks like <source_asset_id>/<rNNNN>") from None
    if rev not in records.list_revisions(sid):
        raise ReadError("unknown_id", "no such source revision")
    source = records.load_source(sid, rev)
    adoption = records.load_adoption(source.adoption_id)
    return {
        "kind": "source", "source_asset_id": sid, "revision": rev, "parent_revision": source.parent_revision, "source_hash": source.source_hash,
        "width": source.width, "height": source.height, "build_eligible": records.is_eligible(sid, rev),
        "revoked": rev in records.revoked_revisions(sid),
        "adoption": {
            "adoption_id": adoption.adoption_id, "intake_id": adoption.intake_id, "visual_key": adoption.visual_key,
            "approver_name": adoption.approver_name, "approver_role": adoption.approver_role, "decided_at": adoption.decided_at,
            "licence_state": adoption.licence_state.value, "licence_note": "stated by the approver at adoption",
        },
    }


def _show_artifact(item_id: str) -> dict:
    if not _ARTIFACT_ID.fullmatch(item_id or ""):
        raise ReadError("invalid_id", "not a valid artifact id")
    directory = records.generated_dir() / item_id
    if not directory.is_dir() or directory.is_symlink():
        raise ReadError("unknown_id", "no such artifact")
    out = []
    for path in sorted(directory.glob("*.artifact.json"))[:MAX_LIMIT]:
        record = parse_record(ArtifactRecord, records.read_file(path, record_bound(ArtifactRecord)))
        out.append({
            "source_revision": record.source_revision, "source_asset_id": record.source_asset_id, "pixel_hash": record.pixel_hash,
            "png_hash": record.png_hash, "width": record.width, "height": record.height, "scale_class": record.scale_class,
            "tool": f"{record.build.tool_name} {record.build.tool_version}",
        })
    return {"kind": "artifact", "artifact_id": item_id, "records": out, "truncated": len(list(directory.glob("*.artifact.json"))) > MAX_LIMIT}


def _show_release(item_id: str) -> dict:
    cid, _, rid = item_id.partition("/")
    try:
        check(ReleaseId, rid)
    except IdentityError:
        raise ReadError("invalid_id", "a release id looks like <catalog_id>/<rc-NNNN>") from None
    if not _ARTIFACT_ID.fullmatch(cid or ""):
        raise ReadError("invalid_id", "a release id looks like <catalog_id>/<rc-NNNN>")
    path: Path = records.manifests_dir() / cid / f"{rid}.json"
    if not path.is_file() or path.is_symlink():
        raise ReadError("unknown_id", "no such release candidate")
    manifest = parse_record(ReleaseCandidateManifest, records.read_file(path, record_bound(ReleaseCandidateManifest)))
    entries = [{"visual_key": e.visual_key, "artifact_id": e.artifact_id, "pixel_hash": e.pixel_hash} for e in manifest.entries]
    return {
        "kind": "release", "catalog_id": manifest.catalog_id, "release_id": manifest.release_id, "status": manifest.status,
        "note": "a release CANDIDATE only: nothing is active", "registry_hash": manifest.registry_hash,
        "entries": entries[:MAX_LIMIT], "entry_count": len(entries), "truncated": len(entries) > MAX_LIMIT,
    }
