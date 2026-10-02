"""Intake, review, list and show. Library code never reads the clock: `created_at` is passed in.

`intake` stages a package into the gitignored quarantine, judges it with the independent validator and writes an
immutable `IntakeResult` INSIDE the quarantine directory (nothing tracked is written; adoption, a later step, is the
only thing that may copy it into the catalog). `review` exports a PASSED candidate's preview and a text summary to the
gitignored review area for a human to look at. Neither adopts anything.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.contracts.base import IntakeVerdict, canonical_json, parse_record
from visual_assets.store.contracts.handoff import CandidateHandoffPackage
from visual_assets.store.contracts.intake import IntakeResult, StagedFile
from visual_assets.store.errors import ContractError, IdentityError, IntakeError, StageError
from visual_assets.store.identities import IntakeId, UtcTimestamp, check
from visual_assets.store.intake import quarantine, validator

_INTAKE_DIR = re.compile(r"in-[0-9a-f]{16}")
SUMMARY_FILE = "summary.txt"
PREVIEW_COPY = "preview.png"


def _intake_id(files: quarantine.PackageFiles) -> str:
    """`in-` + 16 hex of sha256 over the package, source and preview FileHash strings, in that fixed order.

    Derived from all three files (asset-planner decision 2026-10-03), so the same package.json with different bytes is a
    different intake, never a stale result for other bytes.
    """
    joined = "\n".join(validator.file_hash(blob) for blob in (files.package, files.source, files.preview))
    return "in-" + hashlib.sha256(joined.encode("ascii")).hexdigest()[:16]


def _staged_files(files: quarantine.PackageFiles) -> tuple[StagedFile, ...]:
    return (
        StagedFile(name="package.json", file_hash=validator.file_hash(files.package)),
        StagedFile(name="source.aseprite", file_hash=validator.file_hash(files.source)),
        StagedFile(name="preview.png", file_hash=validator.file_hash(files.preview)),
    )


def _load_result(directory: Path) -> IntakeResult:
    try:
        return parse_record(IntakeResult, quarantine.read_one(directory, quarantine.RESULT_FILE))
    except StageError as exc:
        raise IntakeError("incomplete_stage", f"{directory.name} has no readable intake_result.json ({exc.code})") from None
    except ContractError as exc:
        raise IntakeError("corrupt_result", f"{directory.name}/intake_result.json is invalid ({exc.code})") from None


def _stage_directory(intake_id: str) -> Path:
    try:
        check(IntakeId, intake_id)
    except IdentityError:
        raise IntakeError("bad_intake_id", "not a valid intake id") from None
    directory = config.QUARANTINE_ROOT / intake_id
    if directory.is_symlink() or not directory.is_dir():
        raise IntakeError("unknown_intake", f"no quarantined intake {intake_id}")
    return directory


def intake(package_dir: Path | str, *, created_at: str) -> IntakeResult:
    """Stage, validate and record one package. Re-submitting the identical package returns the existing result."""
    try:
        check(UtcTimestamp, created_at)
    except IdentityError:
        raise IntakeError("bad_created_at", "created_at must be a real YYYY-MM-DDTHH:MM:SSZ timestamp") from None
    files = quarantine.read_directory(Path(package_dir))
    intake_id = _intake_id(files)
    staged = _staged_files(files)

    existing_dir = config.QUARANTINE_ROOT / intake_id
    if existing_dir.is_symlink() or existing_dir.exists():
        existing = _load_result(existing_dir)
        if existing.staged_files != staged:
            raise IntakeError(
                "intake_id_collision",
                f"{intake_id} already exists with different staged files (an id collision); nothing was written",
            )
        return existing

    judged = validator.validate(files.package, files.source, files.preview)
    result = IntakeResult(
        record_type="intake_result",
        schema_version=1,
        intake_id=intake_id,
        candidate_id=judged.package.candidate_id if judged.package is not None else "UNAVAILABLE",
        package_hash=validator.file_hash(files.package),
        staged_files=staged,
        verdict=IntakeVerdict.QUARANTINED if judged.findings else IntakeVerdict.PASSED,
        findings=judged.findings,
        validator_version=validator.VALIDATOR_VERSION,
        created_at=created_at,
    )
    result_bytes = canonical_json(result)

    quarantine.stage_atomically(
        intake_id,
        {
            quarantine.PACKAGE_FILE: files.package,
            quarantine.SOURCE_FILE: files.source,
            quarantine.PREVIEW_FILE: files.preview,
            quarantine.RESULT_FILE: result_bytes,
        },
    )
    return result


def show(intake_id: str) -> IntakeResult:
    return _load_result(_stage_directory(intake_id))


def list_results() -> tuple[list[IntakeResult], list[str]]:
    """Every readable result in the quarantine, plus the names of directories whose result is missing or invalid."""
    root = config.QUARANTINE_ROOT
    if root.is_symlink() or not root.is_dir():
        return [], []
    results: list[IntakeResult] = []
    problems: list[str] = []
    for entry in sorted(root.iterdir()):
        if not _INTAKE_DIR.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
            continue
        try:
            results.append(_load_result(entry))
        except IntakeError:
            problems.append(entry.name)
    return results, problems


def _summary(package: CandidateHandoffPackage, result: IntakeResult) -> bytes:
    def shown(value: object) -> str:
        return str(getattr(value, "value", value))

    lines = [
        "REVIEW ONLY. This candidate is NOT adopted, published or active.",
        f"intake_id: {result.intake_id}",
        f"candidate_id: {package.candidate_id}",
        f"validator: {result.validator_version}, passed at {result.created_at}",
        f"producer_class: {shown(package.producer_class)} (state {shown(package.producer_state)}, "
        f"validation {shown(package.producer_validation)})",
        f"creator: {shown(package.creator)}",
        f"editor: {shown(package.editor)}  adapter: {shown(package.adapter)}",
        f"tool: {shown(package.tool)} {shown(package.tool_version)}",
        f"size: {package.width}x{package.height}  frames: {package.frame_count}  layers: {package.layer_count}  "
        f"cels: {package.cel_count}  tags: {package.tag_count}  palette: {package.palette_size}",
        f"brief: {shown(package.brief_id)}",
        f"human review: {shown(package.human_review_ref)}",
        f"licence: {shown(package.licence_state)} (evidence {shown(package.licence_evidence_ref)})",
        f"source hash: {package.source_hash}",
        f"preview hash: {package.preview_hash}",
        "declared limitations:" + ("" if package.declared_limitations else " none"),
        *(f"  - {item}" for item in package.declared_limitations),
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _review_matches(target: Path, preview: bytes, summary: bytes) -> bool:
    try:
        return (
            not target.is_symlink()
            and quarantine.read_one_any(target, PREVIEW_COPY, config.MAX_PREVIEW_BYTES) == preview
            and quarantine.read_one_any(target, SUMMARY_FILE, config.MAX_RECORD_BYTES) == summary
        )
    except StageError:
        return False


def review(intake_id: str) -> Path:
    """Export a PASSED, still-intact candidate to `config.REVIEW_ROOT/<intake_id>/`. Needs no Aseprite."""
    directory = _stage_directory(intake_id)
    result = _load_result(directory)
    if result.verdict is not IntakeVerdict.PASSED:
        raise IntakeError("not_passed", f"{intake_id} is {result.verdict.value}; only a PASSED intake can be reviewed")
    files = quarantine.read_directory(directory, extra_allowed=(quarantine.RESULT_FILE,))
    if _staged_files(files) != result.staged_files or validator.file_hash(files.package) != result.package_hash:
        raise IntakeError("staged_bytes_changed", f"{intake_id}: staged bytes no longer match the recorded hashes")
    try:
        package = parse_record(CandidateHandoffPackage, files.package)
    except ContractError as exc:
        raise IntakeError("corrupt_result", f"{intake_id}: staged package.json no longer parses ({exc.code})") from None

    summary = _summary(package, result)
    root = quarantine.ensure_root(config.REVIEW_ROOT)
    target = root / intake_id
    if target.exists() or target.is_symlink():
        if not _review_matches(target, files.preview, summary):
            raise IntakeError("review_exists_differs", f"{target.name} already exists in the review area with different content")
        return target
    target.mkdir(mode=0o700)
    try:
        quarantine.write_new(target / PREVIEW_COPY, files.preview)
        quarantine.write_new(target / SUMMARY_FILE, summary)
    except BaseException:
        quarantine.remove_partial(target)
        raise
    return target
