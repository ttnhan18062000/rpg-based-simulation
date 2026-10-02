"""`IntakeResult`: the independent validator's immutable verdict on a staged candidate.

Findings are only for a package that WAS staged and then judged. A package refused before any byte was copied
(symlink, extra file, oversize, ...) never produces an `IntakeResult`; that is a `StageError`, not a finding.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from visual_assets.store.contracts.base import BoundedText, IntakeVerdict, StoreRecord
from visual_assets.store.identities import CandidateId, FileHash, IntakeId, UtcTimestamp

MAX_FINDINGS = 64  # provisional (U-05)
STAGED_FILE_NAMES = ("package.json", "source.aseprite", "preview.png")


class IntakeFindingCode(str, Enum):
    # package.json itself
    PACKAGE_UNREADABLE = "PACKAGE_UNREADABLE"  # not UTF-8 / not JSON / NaN / over the size bound
    PACKAGE_DUPLICATE_KEY = "PACKAGE_DUPLICATE_KEY"
    PACKAGE_UNKNOWN_FIELD = "PACKAGE_UNKNOWN_FIELD"
    PACKAGE_MISSING_FIELD = "PACKAGE_MISSING_FIELD"
    PACKAGE_WRONG_RECORD_TYPE = "PACKAGE_WRONG_RECORD_TYPE"
    PACKAGE_UNSUPPORTED_VERSION = "PACKAGE_UNSUPPORTED_VERSION"
    PACKAGE_INVALID = "PACKAGE_INVALID"  # any other schema violation
    ASSERTION_MISSING = "ASSERTION_MISSING"
    # claims about the staged bytes
    SOURCE_HASH_MISMATCH = "SOURCE_HASH_MISMATCH"
    PREVIEW_HASH_MISMATCH = "PREVIEW_HASH_MISMATCH"
    # the Aseprite source
    SOURCE_BAD_MAGIC = "SOURCE_BAD_MAGIC"
    SOURCE_HEADER_SIZE_MISMATCH = "SOURCE_HEADER_SIZE_MISMATCH"
    SOURCE_TRUNCATED = "SOURCE_TRUNCATED"
    SOURCE_TRUNCATED_CHUNK = "SOURCE_TRUNCATED_CHUNK"
    SOURCE_MALFORMED = "SOURCE_MALFORMED"
    SOURCE_UNSUPPORTED_COLOR_DEPTH = "SOURCE_UNSUPPORTED_COLOR_DEPTH"
    DIMENSION_OUT_OF_BOUNDS = "DIMENSION_OUT_OF_BOUNDS"
    WIDTH_MISMATCH = "WIDTH_MISMATCH"
    HEIGHT_MISMATCH = "HEIGHT_MISMATCH"
    FRAME_COUNT_MISMATCH = "FRAME_COUNT_MISMATCH"
    LAYER_COUNT_MISMATCH = "LAYER_COUNT_MISMATCH"
    CEL_COUNT_MISMATCH = "CEL_COUNT_MISMATCH"
    TAG_COUNT_MISMATCH = "TAG_COUNT_MISMATCH"
    PALETTE_SIZE_MISMATCH = "PALETTE_SIZE_MISMATCH"
    PALETTE_UNVERIFIABLE = "PALETTE_UNVERIFIABLE"  # all-black stored palette: loaded size depends on decoded pixels
    # the preview PNG
    PNG_SIGNATURE_INVALID = "PNG_SIGNATURE_INVALID"
    PNG_MALFORMED = "PNG_MALFORMED"
    PREVIEW_DIMENSION_MISMATCH = "PREVIEW_DIMENSION_MISMATCH"
    PREVIEW_OUT_OF_BOUNDS = "PREVIEW_OUT_OF_BOUNDS"
    # policy
    LICENCE_WITHDRAWN = "LICENCE_WITHDRAWN"
    PRODUCER_NOT_ACTIVE = "PRODUCER_NOT_ACTIVE"
    PRODUCER_VALIDATION_FAILED = "PRODUCER_VALIDATION_FAILED"
    UNSUPPORTED_LIMITATION = "UNSUPPORTED_LIMITATION"


class IntakeFinding(StoreRecord):
    code: IntakeFindingCode
    detail: BoundedText


class StagedFile(StoreRecord):
    name: Literal["package.json", "source.aseprite", "preview.png"]
    file_hash: FileHash


class IntakeResult(StoreRecord):
    record_type: Literal["intake_result"]
    schema_version: Literal[1]
    intake_id: IntakeId
    # `UNAVAILABLE` only when package.json could not be parsed, so no candidate id was ever claimed
    candidate_id: CandidateId | Literal["UNAVAILABLE"]
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
        if self.verdict is IntakeVerdict.PASSED and self.candidate_id == "UNAVAILABLE":
            raise ValueError("a PASSED intake has a candidate id")
        if self.verdict is IntakeVerdict.PASSED and names != list(STAGED_FILE_NAMES):
            raise ValueError("a PASSED intake stages exactly package.json, source.aseprite, preview.png")
        return self
