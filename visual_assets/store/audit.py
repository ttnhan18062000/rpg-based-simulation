"""`audit_chain`: rebuild, from the catalog tree alone, intake result -> adoption record -> source record -> source bytes.

Read-only. For every source revision it checks each link, using the hashes the records carry (the SourceRecord holds the
hash of the exact adoption record bytes, the adoption record holds the hash of the exact intake result bytes and of the
source bytes), and reports EVERY break with a stable code. Stated limit: someone who edits an adoption record AND the
SourceRecord that points at it consistently is not caught by the catalog alone; git history is the backstop. A leftover
`.tmp-*` directory is reported as a note, never as a failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from visual_assets.store import config, records
from visual_assets.store.contracts import AdoptionRecord, IntakeResult, RevocationRecord, ReviewRenderCheck, SourceRecord, parse_record, record_bound
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.errors import ContractError, StageError
from visual_assets.store.identities import revision_number
from visual_assets.store.intake.validator import file_hash

_IGNORED = {".gitkeep"}
TEMP = ".tmp-"  # a leftover temporary directory is a note, never a break


@dataclass(frozen=True)
class AuditBreak:
    code: str
    path: str  # relative to the catalog root
    detail: str


@dataclass
class AuditReport:
    breaks: list[AuditBreak] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # False once a record that names others could not be read: orphan checks on what it names would be guesses
    adoptions_known: bool = True
    intakes_known: bool = True

    @property
    def ok(self) -> bool:
        return not self.breaks


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name


def _load(cls, path: Path, root: Path, report: AuditReport, missing: str, unreadable: str, limit: int | None = None):
    """(record, bytes) or (None, None) after recording the break."""
    if not path.exists() and not path.is_symlink():
        report.breaks.append(AuditBreak(missing, _rel(root, path), "the file is missing"))
        return None, None
    try:
        data = records.read_file(path, limit if limit is not None else (record_bound(cls) if cls is not None else config.MAX_RECORD_BYTES))
        return (parse_record(cls, data) if cls is not None else None), data
    except (StageError, ContractError) as exc:
        report.breaks.append(AuditBreak(unreadable, _rel(root, path), f"cannot be read ({exc.code})"))
        return None, None


def audit_chain(catalog_root: Path | str | None = None) -> AuditReport:
    root = Path(catalog_root) if catalog_root is not None else config.CATALOG_ROOT
    report = AuditReport()
    referenced_adoptions: set[str] = set()
    referenced_intakes: set[str] = set()

    sources = records.sources_dir(root)
    if sources.is_dir() and not sources.is_symlink():
        for entry in sorted(sources.iterdir()):
            if entry.name in _IGNORED or entry.name.startswith(TEMP):
                continue
            if not entry.is_dir() or entry.is_symlink() or entry.name not in records.list_source_ids(root):
                report.breaks.append(AuditBreak("ORPHAN_FILE", _rel(root, entry), "not a source asset directory"))
                continue
            _audit_source(root, entry.name, report, referenced_adoptions, referenced_intakes)

    _audit_unreferenced(root, report, referenced_adoptions, referenced_intakes)
    _audit_revocations(root, report)
    for path in sorted(root.rglob(".tmp-*")) if root.is_dir() else []:
        report.notes.append(f"leftover temporary directory {_rel(root, path)} (safe to delete)")
    return report


def _audit_source(root: Path, sid: str, report: AuditReport, adoptions: set[str], intakes: set[str]) -> None:
    directory = records.sources_dir(root) / sid
    revisions = records.list_revisions(sid, root)
    names = {p.name for p in directory.iterdir() if p.name not in _IGNORED}
    expected = {name for rev in revisions for name in (f"{rev}.aseprite", f"{rev}.source.json")}
    for stray in sorted(names - expected):
        match = records.REVISION_FILE.fullmatch(stray)
        code = "ORPHAN_FILE"
        detail = "a source revision file without its SourceRecord" if match else "unexpected file in a source directory"
        report.breaks.append(AuditBreak(code, _rel(root, directory / stray), detail))

    for revision in revisions:
        bytes_path, record_path = records.source_paths(sid, revision, root)
        source, _ = _load(SourceRecord, record_path, root, report, "SOURCE_RECORD_MISSING", "SOURCE_RECORD_UNREADABLE")
        if source is None:
            report.adoptions_known = report.intakes_known = False
            continue
        if source.source_asset_id != sid or source.source_revision != revision:
            report.breaks.append(AuditBreak("SOURCE_RECORD_MISMATCH", _rel(root, record_path),
                                            f"the record says {source.source_asset_id} {source.source_revision}"))
        data = _read_source_bytes(bytes_path, root, report)
        if data is not None and file_hash(data) != source.source_hash:
            report.breaks.append(AuditBreak("SOURCE_BYTES_HASH_MISMATCH", _rel(root, bytes_path), "the source bytes do not hash to the recorded value"))
        _check_parent(root, sid, revision, source, revisions, record_path, report)

        adoption_path = records.adoptions_dir(root) / f"{source.adoption_id}.json"
        adoptions.add(source.adoption_id)
        adoption, adoption_bytes = _load(AdoptionRecord, adoption_path, root, report, "ADOPTION_MISSING", "ADOPTION_UNREADABLE")
        if adoption is None:
            report.intakes_known = False
            continue
        if file_hash(adoption_bytes) != source.adoption_hash:
            report.breaks.append(AuditBreak("ADOPTION_HASH_MISMATCH", _rel(root, adoption_path),
                                            "the adoption record bytes differ from the hash the SourceRecord holds"))
        _check_adoption(root, sid, revision, source, adoption, adoption_path, report)

        intakes.add(adoption.intake_id)
        intake_path = records.intake_dir(root) / f"{adoption.intake_id}.json"
        result, result_bytes = _load(IntakeResult, intake_path, root, report, "INTAKE_MISSING", "INTAKE_UNREADABLE")
        if result is None:
            continue
        if file_hash(result_bytes) != adoption.intake_hash:
            report.breaks.append(AuditBreak("INTAKE_HASH_MISMATCH", _rel(root, intake_path),
                                            "the intake result bytes differ from the hash the adoption record holds"))
        _check_intake(root, adoption, result, intake_path, report)

        review_path = records.review_copy_path(adoption.intake_id, root)
        review, review_bytes = _load(ReviewRenderCheck, review_path, root, report, "REVIEW_MISSING", "REVIEW_UNREADABLE")
        if review is None:
            continue
        if file_hash(review_bytes) != adoption.review_hash:
            report.breaks.append(AuditBreak("REVIEW_HASH_MISMATCH", _rel(root, review_path),
                                            "the render check bytes differ from the hash the adoption record holds"))
        if (review.intake_id != adoption.intake_id or review.source_hash != adoption.source_hash
                or review.verdict is not RenderVerdict.MATCH):
            report.breaks.append(AuditBreak("REVIEW_MISMATCH", _rel(root, review_path),
                                            "the render check does not describe the adopted source or did not match the preview"))


def _read_source_bytes(path: Path, root: Path, report: AuditReport) -> bytes | None:
    if not path.exists() and not path.is_symlink():
        report.breaks.append(AuditBreak("SOURCE_BYTES_MISSING", _rel(root, path), "the source file is missing"))
        return None
    try:
        return records.read_file(path, config.MAX_SOURCE_BYTES)
    except StageError as exc:
        report.breaks.append(AuditBreak("SOURCE_BYTES_UNREADABLE", _rel(root, path), f"cannot be read ({exc.code})"))
        return None


def _check_parent(root, sid, revision, source, revisions, record_path, report) -> None:
    parent = source.parent_revision
    if revision == "r0001":
        ok = parent is None
    else:
        ok = parent in revisions and revision_number(parent) < revision_number(revision)
    if not ok:
        report.breaks.append(AuditBreak("PARENT_BROKEN", _rel(root, record_path), f"parent {parent} is not an earlier existing revision"))


def _check_adoption(root, sid, revision, source, adoption, path, report) -> None:
    problems = []
    if (adoption.source_asset_id, adoption.source_revision) != (sid, revision):
        problems.append("it names a different source revision")
    if adoption.source_hash != source.source_hash:
        problems.append("its source hash differs from the SourceRecord")
    if adoption.parent_revision != source.parent_revision:
        problems.append("its parent differs from the SourceRecord")
    if adoption.adoption_id != source.adoption_id or adoption.adoption_id != records.adoption_id_for(adoption.intake_id, sid, revision):
        problems.append("its id does not derive from its intake, source asset and revision")
    for problem in problems:
        report.breaks.append(AuditBreak("ADOPTION_MISMATCH", _rel(root, path), problem))


def _check_intake(root, adoption, result, path, report) -> None:
    problems = []
    if result.intake_id != adoption.intake_id or path.stem != adoption.intake_id:
        problems.append("its intake id differs")
    if result.verdict is not IntakeVerdict.PASSED:
        problems.append("its verdict is not PASSED")
    if result.candidate_id != adoption.candidate_id:
        problems.append("its candidate id differs from the adoption record")
    staged = {f.name: f.file_hash for f in result.staged_files}
    if staged.get("source.aseprite") != adoption.source_hash:
        problems.append("its staged source hash differs from the adopted source hash")
    for problem in problems:
        report.breaks.append(AuditBreak("INTAKE_MISMATCH", _rel(root, path), problem))


def _audit_unreferenced(root: Path, report: AuditReport, adoptions: set[str], intakes: set[str]) -> None:
    if not report.adoptions_known:
        report.notes.append("adoption records were not checked for orphans because a SourceRecord could not be read (it names the adoption)")
    if not report.intakes_known:
        report.notes.append("intake copies were not checked for orphans because a SourceRecord or adoption record could not be read (they name the intake)")
    for base, referenced, label, known in ((records.adoptions_dir(root), adoptions, "adoption record", report.adoptions_known),
                                           (records.intake_dir(root), intakes, "intake result", report.intakes_known)):
        if not base.is_dir() or base.is_symlink() or not known:
            continue
        for path in sorted(base.iterdir()):
            if path.name in _IGNORED or path.name.startswith(TEMP):
                continue
            if path.suffix != ".json" or path.name.split(".")[0] not in referenced:
                report.breaks.append(AuditBreak("ORPHAN_FILE", _rel(root, path), f"an {label} no SourceRecord refers to"))


def _audit_revocations(root: Path, report: AuditReport) -> None:
    base = records.revocations_dir(root)
    if not base.is_dir() or base.is_symlink():
        return
    for path in sorted(base.iterdir()):
        if path.name in _IGNORED or path.name.startswith(TEMP):
            continue
        record, _ = _load(RevocationRecord, path, root, report, "REVOCATION_MISSING", "REVOCATION_UNREADABLE")
        if record is None:
            continue
        if path.stem != record.revocation_id:
            report.breaks.append(AuditBreak("REVOCATION_MISMATCH", _rel(root, path), "the file name is not the record's revocation id"))
        target = record.target
        if getattr(target, "kind", "") == "source_revision" and target.source_revision not in records.list_revisions(target.source_asset_id, root):  # type: ignore[union-attr]
            report.breaks.append(AuditBreak("REVOCATION_DANGLING", _rel(root, path), "it revokes a source revision that does not exist"))
