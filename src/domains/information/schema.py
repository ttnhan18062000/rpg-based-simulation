"""
src/domains/information/schema.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — Information/Belief schemas.
Frozen, immutable dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Mapping
from src.core.self_model import KnowledgeFact, UnknownFact
from src.core.strategic import LeadState, SourceTrustEntry, BlockerState


class InformationSourceKind(str, Enum):
    GUIDE = "guide"
    GUILD = "guild"
    BLACKSMITH = "blacksmith"
    TRAVELER = "traveler"


@dataclass(frozen=True, slots=True)
class InformationSourceProfile:
    """
    Statically defined capabilities of an information provider.
    """
    source_id: str | int
    source_kind: str
    knowledge_scopes: Tuple[str, ...]
    accuracy: float
    freshness: float
    bias: float = 0.0
    cost_gold: int = 0
    max_answers_per_query: int = 3


@dataclass(frozen=True, slots=True)
class InformationSourceCandidate:
    """
    An evaluated candidate source for a query.
    """
    source_id: str | int
    source_kind: str
    expected_relevance: float
    expected_certainty: float
    cost_gold: int
    distance_cost: float
    trust_score: float
    reason: str


@dataclass(frozen=True, slots=True)
class InformationQuery:
    """
    Subjective query request.
    """
    subject: str
    kind: str  # "material_source" | "recipe_definition" | "danger_rating"


@dataclass(frozen=True, slots=True)
class NormalizedInformationResponse:
    """
    Standardized response content from any information provider.
    """
    query: InformationQuery
    source_id: str | int
    answer_kind: str  # "KNOWN_FACT" | "PARTIAL_LEAD" | "RUMOR" | "UNKNOWN" | "CONTRADICTION"
    facts: Tuple[KnowledgeFact, ...] = field(default_factory=tuple)
    leads: Tuple[LeadState, ...] = field(default_factory=tuple)
    unknowns: Tuple[UnknownFact, ...] = field(default_factory=tuple)
    certainty: float = 0.0
    contradiction_targets: Tuple[str, ...] = field(default_factory=tuple)
    cost_paid_gold: int = 0
    reason: Optional[str] = None


@dataclass(frozen=True, slots=True)
class InformationAssimilationResult:
    """
    Output delta after assimilating a normalized response.
    """
    knowledge_update: Optional[Any] = None  # Updated KnowledgeModelComponent
    strategic_update: Optional[Any] = None  # Updated StrategicComponent or StrategicUpdate
    source_trust_update: Optional[SourceTrustEntry] = None
    trace: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RouteImpactHint:
    """
    Subjective guidance to feed Phase 3 route scoring.
    """
    invalidated_route_families: Tuple[str, ...] = field(default_factory=tuple)
    boosted_route_families: Tuple[str, ...] = field(default_factory=tuple)
    new_blockers: Tuple[BlockerState, ...] = field(default_factory=tuple)
    resolved_blockers: Tuple[str, ...] = field(default_factory=tuple)
    reason: Optional[str] = None
