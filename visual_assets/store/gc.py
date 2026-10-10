"""`gc`: list (and, only on request, delete) local and generated files nothing needs. Dry run by default.

Garbage means: quarantine directories with no adoption and no pending review (a QUARANTINED or revoked intake, or a leftover `.tmp-*`), review exports whose
intake is adopted, revoked, gone or expired, generated PNGs no artifact record refers to, and, as retention, a PASSED never-adopted intake (with its review
export) older than `config.MAX_UNADOPTED_INTAKE_AGE_DAYS`, counted from the intake's own `created_at` against a caller-supplied cutoff. A younger PASSED, unrevoked intake is "pending review" and is kept.
Deleting a locally revoked intake also deletes its local revocation record (it lives inside that directory). Deletion removes ONLY listed items, each
verified to sit under the quarantine root, the review root or `generated/`; it never touches `sources/`, `provenance/` or `manifests/`.

`gc` never deletes a tracked object or record: tracked history is git's job and the audit chain is hash-anchored. `tracked_unreferenced()` only REPORTS artifacts no
committed release candidate refers to. If `gc` ever gains a deletion kind for tracked objects, a typed roots record must exist first (its own ticket).
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config, deletionlog, records
from visual_assets.store.contracts import ArtifactRecord, IntakeResult, ReleaseCandidateManifest, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.errors import ContractError, GateError, StageError
from visual_assets.store.identities import UtcTimestamp, check
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.intake import quarantine

_INTAKE = re.compile(r"in-[0-9a-f]{16}")
_PNG = re.compile(r"([0-9a-f]{64})\.png")


@dataclass(frozen=True)
class GcItem:
    kind: str  # quarantine | review | generated
    path: Path
    reason: str


def _adopted(intake_id: str) -> bool:
    return (records.intake_dir() / f"{intake_id}.json").exists()


def _expired(result: IntakeResult, expire_before: str) -> bool:
    """The intake is older than the retention bound: created strictly before the cutoff (an intake exactly on the cutoff is kept).
    Timestamps are fixed-width UTC (`UtcTimestamp`), so string order is time order and no clock or date arithmetic is needed here."""
    return result.created_at < expire_before


def collect(expire_before: str) -> list[GcItem]:
    check(UtcTimestamp, expire_before)  # string order is time order only for the canonical fixed-width form: a malformed cutoff would silently change what expires
    items: list[GcItem] = []
    expired: set[str] = set()
    q = config.QUARANTINE_ROOT
    if q.is_dir() and not q.is_symlink():
        for entry in sorted(q.iterdir()):
            if entry.name.startswith(quarantine.TEMP_PREFIX):
                items.append(GcItem("quarantine", entry, "a leftover temporary directory"))
            elif _INTAKE.fullmatch(entry.name) and entry.is_dir() and not entry.is_symlink() and not _adopted(entry.name):
                revoked = records.intake_revoked_locally(entry.name)
                try:
                    result = parse_record(IntakeResult, quarantine.read_one(entry, quarantine.RESULT_FILE))
                except (StageError, ContractError):
                    continue  # an unreadable intake is not ours to judge; `list` reports it
                if revoked or result.verdict is IntakeVerdict.QUARANTINED:
                    items.append(GcItem("quarantine", entry, "revoked, not adopted" if revoked else "QUARANTINED, not adopted"))
                elif _expired(result, expire_before):
                    expired.add(entry.name)
                    items.append(GcItem("quarantine", entry, f"PASSED, not adopted, older than {config.MAX_UNADOPTED_INTAKE_AGE_DAYS} days"))
    r = config.REVIEW_ROOT
    if r.is_dir() and not r.is_symlink():
        for entry in sorted(r.iterdir()):
            if not _INTAKE.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
                continue
            gone = not (q / entry.name).is_dir()
            if gone or _adopted(entry.name) or records.intake_revoked_locally(entry.name):
                items.append(GcItem("review", entry, "its intake is gone, adopted or revoked"))
            elif entry.name in expired:
                items.append(GcItem("review", entry, "its intake expired"))
    g = records.generated_dir()
    if g.is_dir() and not g.is_symlink():
        for directory in sorted(g.iterdir()):
            if not directory.is_dir() or directory.is_symlink():
                continue
            referenced = {m.group(1) for p in directory.glob("*.artifact.json") if (m := re.match(r"([0-9a-f]{64})\.", p.name))}
            for png in sorted(directory.iterdir()):
                if (m := _PNG.fullmatch(png.name)) and m.group(1) not in referenced and png.is_file() and not png.is_symlink():
                    items.append(GcItem("generated", png, "no artifact record refers to it"))
    return items


def tracked_unreferenced() -> list[Path]:
    """Artifact records (tracked) that no committed release candidate refers to. REPORT ONLY: they are tracked history and are never deleted."""
    referenced: set[tuple[str, str]] = set()
    manifests = records.manifests_dir()
    if manifests.is_dir():
        for path in sorted(manifests.glob("*/rc-*.json")):
            try:
                candidate = parse_record(ReleaseCandidateManifest, path.read_bytes())
            except (OSError, ContractError):
                continue  # an unreadable manifest is `verify`'s to report
            referenced |= {(e.artifact_id, e.pixel_hash) for e in candidate.entries}
    out: list[Path] = []
    g = records.generated_dir()
    if g.is_dir() and not g.is_symlink():
        for path in sorted(g.glob("*/*.artifact.json")):
            try:
                record = parse_record(ArtifactRecord, path.read_bytes())
            except (OSError, ContractError):
                continue
            if (record.artifact_id, record.pixel_hash) not in referenced:
                out.append(path)
    return out


def _inside(path: Path, root: Path) -> bool:
    """`path` is under `root` and neither it nor any directory between is a symlink."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    return True


def gc(*, expire_before: str, delete: bool = False, decided_at: str | None = None) -> list[GcItem]:
    """The garbage list. `expire_before` is the cutoff timestamp (`now` minus `config.MAX_UNADOPTED_INTAKE_AGE_DAYS`), computed by the caller: library code never reads the clock. With `delete=True` (which also needs `decided_at`, the caller's clock for the log) each listed item is removed (after re-checking it is where it should be); otherwise nothing changes.

    ADR D24: before any removal every record is built and the log is checked for room, so a full log refuses with nothing deleted; then each item is appended to the local deletion log BEFORE it is removed. The caller holds the store lock."""
    items = collect(expire_before)
    if delete:
        if decided_at is None:
            raise GateError("decided_at_required", "gc --delete records when it decided: pass decided_at")
        check(UtcTimestamp, decided_at)
        roots = {"quarantine": config.QUARANTINE_ROOT, "review": config.REVIEW_ROOT, "generated": records.generated_dir()}
        planned: list[tuple[GcItem, bytes]] = []
        prev = deletionlog.last_hash()
        for item in items:
            root = roots[item.kind]
            if not _inside(item.path, root):
                continue
            try:
                content = deletionlog.content_hash(item.path)
            except OSError:
                raise GateError("deletion_unreadable", f"{item.path.name} cannot be read to record its hash; nothing was deleted") from None
            _, line = deletionlog.build_record(kind=item.kind, relative=item.path.relative_to(root).as_posix(), content=content, reason=item.reason,
                                               decided_at=decided_at, prev_hash=prev)
            planned.append((item, line))
            prev = file_hash(line)
        deletionlog.require_room(sum(len(line) for _, line in planned))
        deletionlog.require_clean_tail()
        for item, line in planned:
            deletionlog.append(line)
            if item.path.is_dir() and not item.path.is_symlink():
                shutil.rmtree(item.path)
            else:
                item.path.unlink(missing_ok=True)
    return items
