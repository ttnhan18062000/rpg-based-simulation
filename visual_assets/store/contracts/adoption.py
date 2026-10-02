"""`AdoptionRecord` and `RevocationRecord`: the human-gated decisions."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from visual_assets.store.contracts.base import (
    BoundedText,
    LicenceState,
    PersonText,
    ProvenanceText,
    StoreRecord,
)
from visual_assets.store.identities import (
    AdoptionId,
    CandidateId,
    FileHash,
    IntakeId,
    RevocationId,
    SourceAssetId,
    SourceRevision,
    UtcTimestamp,
    VisualKey,
    revision_number,
)


def check_parent(revision: str, parent: str | None) -> None:
    """The parent is `None` exactly for `r0001`, and otherwise an earlier revision."""
    if (revision == "r0001") != (parent is None):
        raise ValueError("parent_revision is None exactly when source_revision is r0001")
    if parent is not None and revision_number(parent) >= revision_number(revision):
        raise ValueError("parent_revision must be earlier than source_revision")


class AdoptionRecord(StoreRecord):
    record_type: Literal["adoption_record"]
    schema_version: Literal[1]
    adoption_id: AdoptionId
    intake_id: IntakeId
    candidate_id: CandidateId
    approver_name: PersonText
    approver_role: PersonText
    source_hash: FileHash
    source_asset_id: SourceAssetId
    source_revision: SourceRevision
    parent_revision: SourceRevision | None
    visual_key: VisualKey
    licence_state: LicenceState
    licence_evidence_ref: ProvenanceText
    decided_at: UtcTimestamp

    @model_validator(mode="after")
    def _rules(self) -> AdoptionRecord:
        check_parent(self.source_revision, self.parent_revision)
        if self.licence_state is LicenceState.WITHDRAWN:
            raise ValueError("a WITHDRAWN licence state cannot be adopted")
        return self


class IntakeTarget(StoreRecord):
    kind: Literal["intake"]
    intake_id: IntakeId


class SourceRevisionTarget(StoreRecord):
    kind: Literal["source_revision"]
    source_asset_id: SourceAssetId
    source_revision: SourceRevision


RevocationTarget = Annotated[IntakeTarget | SourceRevisionTarget, Field(discriminator="kind")]


class RevocationRecord(StoreRecord):
    record_type: Literal["revocation_record"]
    schema_version: Literal[1]
    revocation_id: RevocationId
    target: RevocationTarget
    reason: BoundedText
    approver_name: PersonText
    approver_role: PersonText
    decided_at: UtcTimestamp
