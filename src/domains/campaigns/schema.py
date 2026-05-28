"""
src/domains/campaigns/schema.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Campaign Spec and Result schemas.
All dataclasses are frozen so they are immutable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional


@dataclass(frozen=True, slots=True)
class CampaignPlaceholder:
    pass



@dataclass(frozen=True, slots=True)
class ActorDistribution:
    count: int
    start_region: str
    start_level: int
    class_distribution: Dict[str, int] = field(default_factory=dict)
    trait_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    campaign_id: str
    seed: int
    ticks: int
    world_pack: str
    actors: ActorDistribution
    initial_world_pressures: Tuple[str, ...] = ()
    expected_arc_families: Tuple[str, ...] = ()
    forbidden_behavior: Tuple[str, ...] = ()
    performance_budget: Dict[str, float] = field(default_factory=dict)
    scorecard_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CampaignEvent:
    event_id: str
    tick: int
    entity_id: Optional[int]
    category: str  # e.g., "combat", "crafting", "information", "social", "movement"
    event_type: str  # e.g., "combat_loss", "quest_completed", "resource_depleted", "recipe_learned"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EntityArcReport:
    entity_id: int
    arc_types: Tuple[str, ...]
    major_events: Tuple[Dict[str, Any], ...]
    behavior_change_proofs: Tuple[BehaviorChangeProof, ...]
    evidence_event_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BehaviorChangeProof:
    entity_id: int
    cause_event_id: str
    later_event_id: str
    change_kind: str
    explanation: str
    confidence: float


@dataclass(frozen=True, slots=True)
class WorldArcReport:
    region: str
    arc_type: str
    details: Dict[str, Any] = field(default_factory=dict)
    evidence_event_ids: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ForbiddenBehaviorReport:
    rule_violated: str
    entity_id: Optional[int]
    tick: int
    evidence_event_ids: Tuple[str, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class RouteDiversityReport:
    unique_route_families_used: int
    route_family_distribution: Dict[str, int]
    trait_to_route_correlation: Dict[str, Dict[str, float]]
    stagnant_entity_ratio: float
    repeated_failure_ratio: float
    identical_behavior_collapse: bool


@dataclass(frozen=True, slots=True)
class CampaignScorecard:
    self_model_usage: str  # "pass" | "fail" | "partial"
    route_decision_quality: str
    combat_learning: str
    information_learning: str
    reward_conversion: str
    cooperation_usage: str
    world_feedback_usage: str
    behavior_change_proofs: int
    route_diversity_score: float
    stagnant_entity_ratio: float
    forbidden_behavior_count: int
    verdict: str  # "pass" | "fail"


@dataclass(frozen=True, slots=True)
class CampaignResult:
    campaign_id: str
    final_state: Any  # AuthoritativeState or similar
    entity_arc_reports: Tuple[EntityArcReport, ...]
    world_arc_reports: Tuple[WorldArcReport, ...]
    forbidden_behaviors: Tuple[ForbiddenBehaviorReport, ...]
    route_diversity: RouteDiversityReport
    semantic_scorecard: CampaignScorecard
    performance_summary: Dict[str, Any]
