"""`CandidateHandoffPackage`: what a producer (manual drawing or CAP-A) hands to intake. Not an adoption."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field

from visual_assets.store.contracts.base import (
    BoundedText,
    Count,
    Dimension,
    LicenceState,
    PositiveCount,
    ProducerClass,
    ProvenanceText,
    StoreRecord,
)
from visual_assets.store.identities import CandidateId, FileHash, SourceRevision

HANDOFF_ASSERTION = "HANDOFF_IS_NOT_ADOPTION_PUBLICATION_OR_ACTIVATION"
SOURCE_FILE_NAME = "source.aseprite"
PREVIEW_FILE_NAME = "preview.png"
MAX_LIMITATIONS = 16  # provisional (U-05)


class SourceFormat(str, Enum):
    ASEPRITE = "ASEPRITE"


class ProducerState(str, Enum):
    """Lifecycle state the producer reports (proposal 9.6). Intake quarantines anything not ACTIVE."""

    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"


class ProducerValidation(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"


class CandidateHandoffPackage(StoreRecord):
    record_type: Literal["candidate_handoff_package"]
    schema_version: Literal[1]
    candidate_id: CandidateId
    # files are named from a fixed allowlist, never by path
    source_file_name: Literal["source.aseprite"]
    preview_file_name: Literal["preview.png"]
    source_hash: FileHash
    source_revision: SourceRevision
    expected_parent: SourceRevision | Literal["NOT_APPLICABLE"]
    producer_class: ProducerClass
    creator: ProvenanceText
    editor: ProvenanceText
    adapter: ProvenanceText
    tool: ProvenanceText
    tool_version: ProvenanceText
    source_format: SourceFormat
    width: Dimension
    height: Dimension
    frame_count: PositiveCount
    layer_count: PositiveCount
    cel_count: Count
    tag_count: Count
    palette_size: Count
    preview_hash: FileHash
    brief_id: ProvenanceText
    human_review_ref: ProvenanceText
    licence_state: LicenceState
    licence_evidence_ref: ProvenanceText
    producer_state: ProducerState
    producer_validation: ProducerValidation
    declared_limitations: Annotated[tuple[BoundedText, ...], Field(max_length=MAX_LIMITATIONS)]
    assertion: Literal["HANDOFF_IS_NOT_ADOPTION_PUBLICATION_OR_ACTIVATION"]
