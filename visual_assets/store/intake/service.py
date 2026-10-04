"""Intake, review, list and show. Library code never reads the clock: `created_at` is passed in.

`intake` stages a package into the gitignored quarantine, judges it with the independent validator and writes an
immutable `IntakeResult` INSIDE the quarantine directory (nothing tracked is written; adoption, a later step, is the
only thing that may copy it into the catalog). `review` exports a PASSED candidate's preview and a text summary to the
gitignored review area for a human to look at. Neither adopts anything.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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


def claims(intake_id: str) -> CandidateHandoffPackage | None:
    """The staged package as the producer wrote it (its statements are claims), or None when it does not parse."""
    directory = _stage_directory(intake_id)
    try:
        return parse_record(CandidateHandoffPackage, quarantine.read_one(directory, quarantine.PACKAGE_FILE))
    except (StageError, ContractError):
        return None


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


@dataclass(frozen=True)
class ReviewMaterial:
    """A PASSED, unrevoked, still-intact intake, ready to be shown to a human (everything verified against the recorded hashes)."""

    intake_id: str
    result: IntakeResult
    package: CandidateHandoffPackage
    files: quarantine.PackageFiles


UNVERIFIED_NOTE = (
    "The preview is producer-supplied and UNVERIFIED: nothing yet proves it depicts the source "
    "(the store has not rendered the source itself)."
)


def _summary(package: CandidateHandoffPackage, result: IntakeResult, notes: Sequence[str]) -> bytes:
    def shown(value: object) -> str:
        return str(getattr(value, "value", value))

    lines = [
        *notes,
        "REVIEW ONLY. This candidate is NOT adopted, published or active.",
        f"intake_id: {result.intake_id}",
        f"candidate_id: {package.candidate_id}",
        f"validator: {result.validator_version}, passed at {result.created_at}",
        "--- claimed by the producer (intake checked the bytes, not these statements) ---",
        f"producer_class: {shown(package.producer_class)} (state {shown(package.producer_state)}, "
        f"validation {shown(package.producer_validation)})",
        f"creator: {shown(package.creator)}",
        f"editor: {shown(package.editor)}  adapter: {shown(package.adapter)}",
        f"tool: {shown(package.tool)} {shown(package.tool_version)}",
        f"brief: {shown(package.brief_id)}",
        f"human review: {shown(package.human_review_ref)}",
        f"licence (claimed by producer, NOT a clearance): {shown(package.licence_state)} (evidence {shown(package.licence_evidence_ref)})",
        "--- checked against the staged bytes ---",
        f"size: {package.width}x{package.height}  frames: {package.frame_count}  layers: {package.layer_count}  "
        f"cels: {package.cel_count}  tags: {package.tag_count}  palette: {package.palette_size}",
        f"source hash: {package.source_hash}",
        f"preview hash: {package.preview_hash}",
        "declared limitations:" + ("" if package.declared_limitations else " none"),
        *(f"  - {item}" for item in package.declared_limitations),
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _review_matches(target: Path, expected: Mapping[str, bytes]) -> bool:
    try:
        return not target.is_symlink() and sorted(p.name for p in target.iterdir()) == sorted(expected) and all(
            quarantine.read_one_any(target, name, config.MAX_PNG_FILE_BYTES) == data for name, data in expected.items()  # the store's own render is not bounded by the producer preview limit
        )
    except (StageError, OSError):
        return False


def prepare_review(intake_id: str) -> ReviewMaterial:
    """Verify an intake can be reviewed and return what a human is shown. Raises `IntakeError` / `StageError` otherwise."""
    directory = _stage_directory(intake_id)
    result = _load_result(directory)
    if result.verdict is not IntakeVerdict.PASSED:
        raise IntakeError("not_passed", f"{intake_id} is {result.verdict.value}; only a PASSED intake can be reviewed")
    if os.path.lexists(directory / quarantine.REVOCATION_FILE):
        raise IntakeError("intake_revoked", f"{intake_id} was revoked; it cannot be reviewed")
    files = quarantine.read_directory(directory, extra_allowed=quarantine.EXTRA_FILES)
    if _staged_files(files) != result.staged_files or validator.file_hash(files.package) != result.package_hash:
        raise IntakeError("staged_bytes_changed", f"{intake_id}: staged bytes no longer match the recorded hashes")
    try:
        package = parse_record(CandidateHandoffPackage, files.package)
    except ContractError as exc:
        raise IntakeError("corrupt_result", f"{intake_id}: staged package.json no longer parses ({exc.code})") from None
    return ReviewMaterial(intake_id, result, package, files)


def export_review(material: ReviewMaterial, *, notes: Sequence[str] = (UNVERIFIED_NOTE,), extra_files: Mapping[str, bytes] | None = None) -> Path:
    """Write the review directory (the producer's preview, a summary, any extra files) or confirm an identical one exists."""
    expected = {
        PREVIEW_COPY: material.files.preview,
        SUMMARY_FILE: _summary(material.package, material.result, notes),
        **(extra_files or {}),
    }
    root = quarantine.ensure_root(config.REVIEW_ROOT)
    target = root / material.intake_id
    if target.exists() or target.is_symlink():
        if not _review_matches(target, expected):
            raise IntakeError("review_exists_differs", f"{target.name} already exists in the review area with different content")
        return target
    target.mkdir(mode=0o700)
    try:
        for name, data in expected.items():
            quarantine.write_new(target / name, data)
    except BaseException:
        quarantine.remove_partial(target)
        raise
    return target


def review(intake_id: str) -> Path:
    """Export a PASSED, still-intact candidate to `config.REVIEW_ROOT/<intake_id>/` (producer preview, UNVERIFIED). Needs no Aseprite."""
    return export_review(prepare_review(intake_id))
