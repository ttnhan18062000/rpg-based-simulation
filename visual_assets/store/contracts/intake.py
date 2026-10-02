"""`IntakeResult`: the independent validator's immutable verdict on a staged candidate."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from visual_assets.store.contracts.base import BoundedText, IntakeVerdict, StoreRecord
from visual_assets.store.identities import CandidateId, FileHash, IntakeId, UtcTimestamp

MAX_FINDINGS = 64  # provisional (U-05)
STAGED_FILE_NAMES = ("handoff.json", "source.aseprite", "preview.png")


class IntakeFindingCode(str, Enum):
    PACKAGE_INVALID = "PACKAGE_INVALID"
    ASSERTION_MISSING = "ASSERTION_MISSING"
    UNKNOWN_FILE = "UNKNOWN_FILE"
    MISSING_FILE = "MISSING_FILE"
    PATH_ESCAPE = "PATH_ESCAPE"
    SYMLINK = "SYMLINK"
    OVERSIZE = "OVERSIZE"
    HASH_MISMATCH = "HASH_MISMATCH"
    FORMAT_MISMATCH = "FORMAT_MISMATCH"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    COUNT_MISMATCH = "COUNT_MISMATCH"
    UNSUPPORTED_FEATURE = "UNSUPPORTED_FEATURE"
    LICENCE_NOT_ACCEPTABLE = "LICENCE_NOT_ACCEPTABLE"
    PARENT_MISMATCH = "PARENT_MISMATCH"


class IntakeFinding(StoreRecord):
    code: IntakeFindingCode
    detail: BoundedText


class StagedFile(StoreRecord):
    name: Literal["handoff.json", "source.aseprite", "preview.png"]
    file_hash: FileHash


class IntakeResult(StoreRecord):
    record_type: Literal["intake_result"]
    schema_version: Literal[1]
    intake_id: IntakeId
    candidate_id: CandidateId
    package_hash: FileHash
    staged_files: Annotated[tuple[StagedFile, ...], Field(max_length=len(STAGED_FILE_NAMES))]
    verdict: IntakeVerdict
    findings: Annotated[tuple[IntakeFinding, ...], Field(max_length=MAX_FINDINGS)]
    validator_version: BoundedText
    created_at: UtcTimestamp

    @model_validator(mode="after")
    def _verdict_matches_findings(self) -> IntakeResult:
        names = [f.name for f in self.staged_files]
        if len(set(names)) != len(names):
            raise ValueError("staged_files names must be unique")
        if self.verdict is IntakeVerdict.PASSED and self.findings:
            raise ValueError("a PASSED intake has no findings")
        if self.verdict is IntakeVerdict.QUARANTINED and not self.findings:
            raise ValueError("a QUARANTINED intake needs at least one finding")
        return self
