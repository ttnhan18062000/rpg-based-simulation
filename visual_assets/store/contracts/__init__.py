"""Typed, versioned store records. Pure: no file, clock or path access."""

from visual_assets.store.contracts.adoption import AdoptionRecord, RevocationRecord
from visual_assets.store.contracts.artifact import ArtifactRecord
from visual_assets.store.contracts.base import canonical_json, parse_record, record_bound
from visual_assets.store.contracts.definitions import VisualKeyRegistry
from visual_assets.store.contracts.draft import DraftSet, SetAdoptionRecord
from visual_assets.store.contracts.handoff import CandidateHandoffPackage
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.contracts.release import ReleaseCandidateManifest
from visual_assets.store.contracts.review import ReviewRenderCheck
from visual_assets.store.contracts.runtime import RuntimeManifest
from visual_assets.store.contracts.source import SourceRecord
from visual_assets.store.errors import ContractError

RECORD_TYPES = (
    CandidateHandoffPackage,
    IntakeResult,
    ReviewRenderCheck,
    AdoptionRecord,
    RevocationRecord,
    SourceRecord,
    ArtifactRecord,
    ReleaseCandidateManifest,
    VisualKeyRegistry,
    RuntimeManifest,
    DraftSet,
    SetAdoptionRecord,
)

__all__ = ["RECORD_TYPES", "ContractError", "canonical_json", "parse_record", "record_bound", *(c.__name__ for c in RECORD_TYPES)]
