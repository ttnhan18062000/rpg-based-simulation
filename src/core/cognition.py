"""
src/core/cognition.py
───────────────────────────────────────────────────────────────────────────────
Phase 11 — Cognition Model Hierarchy and Components.

All dataclasses are strictly frozen data schemas representing the structured 
nested hierarchy under EntityState.cognition. No services or business logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from src.core.self_model import (
    KnowledgeModelComponent,
    KnowledgeFact,
    UnknownFact
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Subjective Model Sub-components
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PerceivedEntity:
    entity_id: int
    kind: str
    position: Tuple[float, float]
    salience: float
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class PerceivedResource:
    node_id: int
    kind: str
    position: Tuple[float, float]
    salience: float
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class PerceivedService:
    service_id: str
    position: Tuple[float, float]
    salience: float


@dataclass(frozen=True, slots=True)
class PerceivedThreat:
    threat_id: str
    position: Tuple[float, float]
    salience: float
    threat_level: float


@dataclass(frozen=True, slots=True)
class PerceivedOpportunity:
    opportunity_id: str
    kind: str
    salience: float


@dataclass(frozen=True, slots=True)
class IgnoredSignal:
    signal_id: str
    reason: str
    tick: int


@dataclass(frozen=True, slots=True)
class PerceptionModel:
    """Phase 12 Perception container."""
    attention_focus: Tuple[str, ...] = ()
    perceived_entities: Mapping[int, PerceivedEntity] = field(default_factory=dict)
    perceived_resources: Mapping[str, PerceivedResource] = field(default_factory=dict)
    perceived_services: Mapping[str, PerceivedService] = field(default_factory=dict)
    perceived_threats: Mapping[str, PerceivedThreat] = field(default_factory=dict)
    perceived_opportunities: Mapping[str, PerceivedOpportunity] = field(default_factory=dict)
    ignored_signals: Tuple[IgnoredSignal, ...] = ()
    last_updated_tick: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "attention_focus": list(self.attention_focus),
            "perceived_entities": {str(k): {"salience": round(v.salience, 4)} for k, v in sorted(self.perceived_entities.items())},
            "perceived_resources": {k: {"salience": round(v.salience, 4)} for k, v in sorted(self.perceived_resources.items())},
            "perceived_services": {k: {"salience": round(v.salience, 4)} for k, v in sorted(self.perceived_services.items())},
            "perceived_threats": {k: {"salience": round(v.salience, 4)} for k, v in sorted(self.perceived_threats.items())},
            "perceived_opportunities": {k: {"salience": round(v.salience, 4)} for k, v in sorted(self.perceived_opportunities.items())},
            "ignored_signals_count": len(self.ignored_signals),
            "last_updated_tick": self.last_updated_tick
        }


@dataclass(frozen=True, slots=True)
class RecoveryState:
    """Phase 16 Recovery State Shell."""
    recent_near_death: bool = False
    confidence_loss: float = 0.0
    retry_readiness: float = 1.0
    recovery_until_tick: Optional[int] = None
    trauma_tags: Tuple[str, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "recent_near_death": self.recent_near_death,
            "confidence_loss": round(self.confidence_loss, 4),
            "retry_readiness": round(self.retry_readiness, 4),
            "recovery_until_tick": self.recovery_until_tick,
            "trauma_tags": list(self.trauma_tags)
        }


@dataclass(frozen=True, slots=True)
class RiskModel:
    """Phase 13 Risk Beliefs Shell."""
    risks: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "risks": dict(sorted(self.risks.items()))
        }


@dataclass(frozen=True, slots=True)
class DeadlineEntry:
    target_id: str
    expiry_tick: int


@dataclass(frozen=True, slots=True)
class CooldownEntry:
    target_id: str
    ready_tick: int


@dataclass(frozen=True, slots=True)
class StalenessEntry:
    fact_id: str
    last_verified_tick: int


@dataclass(frozen=True, slots=True)
class DelayRiskEntry:
    risk_factor: float


@dataclass(frozen=True, slots=True)
class TemporalModel:
    """Phase 13 Temporal awareness container."""
    deadlines: Mapping[str, DeadlineEntry] = field(default_factory=dict)
    cooldowns: Mapping[str, CooldownEntry] = field(default_factory=dict)
    stale_facts: Mapping[str, StalenessEntry] = field(default_factory=dict)
    urgency: Mapping[str, float] = field(default_factory=dict)
    delay_risks: Mapping[str, DelayRiskEntry] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "deadlines": dict(sorted(self.deadlines.items())),
            "cooldowns": dict(sorted(self.cooldowns.items())),
            "stale_facts": dict(sorted(self.stale_facts.items())),
            "urgency": {k: round(v, 4) for k, v in sorted(self.urgency.items())}
        }


@dataclass(frozen=True, slots=True)
class EmotionalModel:
    """Phase 16 Emotional State Shell."""
    fear: float = 0.0
    confidence: float = 0.5
    frustration: float = 0.0
    curiosity: float = 0.0
    satisfaction: float = 0.0
    panic: float = 0.0
    boredom: float = 0.0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "fear": round(self.fear, 4),
            "confidence": round(self.confidence, 4),
            "frustration": round(self.frustration, 4),
            "curiosity": round(self.curiosity, 4),
            "satisfaction": round(self.satisfaction, 4),
            "panic": round(self.panic, 4),
            "boredom": round(self.boredom, 4)
        }


@dataclass(frozen=True, slots=True)
class SubjectiveModel:
    """Subjective model grouping perception, self, knowledge, risk, time, and emotion."""
    perception: PerceptionModel = field(default_factory=PerceptionModel)
    knowledge: KnowledgeModelComponent = field(default_factory=KnowledgeModelComponent)
    risk: RiskModel = field(default_factory=RiskModel)
    time: TemporalModel = field(default_factory=TemporalModel)
    emotion: EmotionalModel = field(default_factory=EmotionalModel)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "perception": self.perception.to_canonical_dict(),
            "knowledge": self.knowledge.to_canonical_dict(),
            "risk": self.risk.to_canonical_dict(),
            "time": self.time.to_canonical_dict(),
            "emotion": self.emotion.to_canonical_dict()
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Memory Model Sub-components
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExperienceMemory:
    """Phase 13 Shell."""
    records: Tuple[Any, ...] = ()
    capacity: int = 50

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"capacity": self.capacity}


@dataclass(frozen=True, slots=True)
class CausalMemoryEntry:
    event_id: str
    event_kind: str
    interpreted_causes: Tuple[str, ...]
    confidence: float
    future_advice: Tuple[str, ...]
    tick: int
    region_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class CausalMemory:
    """Phase 13 Causal Memory Container."""
    entries: Tuple[CausalMemoryEntry, ...] = ()
    capacity: int = 30

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "entries_count": len(self.entries),
            "capacity": self.capacity
        }


@dataclass(frozen=True, slots=True)
class RegionVisitMemory:
    region_id: str
    visit_count: int
    familiarity: float
    is_dangerous: bool = False


@dataclass(frozen=True, slots=True)
class RouteMemory:
    route_id: str
    safety_score: float


@dataclass(frozen=True, slots=True)
class ResourceSiteMemory:
    site_id: str
    resource_kind: str
    position: Tuple[float, float]


@dataclass(frozen=True, slots=True)
class FailedSearchMemory:
    site_id: str
    tick: int


@dataclass(frozen=True, slots=True)
class SpatialMemory:
    """Phase 13 Spatial Memory Container."""
    visited_regions: Mapping[str, RegionVisitMemory] = field(default_factory=dict)
    safe_routes: Mapping[str, RouteMemory] = field(default_factory=dict)
    dangerous_routes: Mapping[str, RouteMemory] = field(default_factory=dict)
    known_resource_sites: Mapping[str, ResourceSiteMemory] = field(default_factory=dict)
    failed_search_locations: Mapping[str, FailedSearchMemory] = field(default_factory=dict)
    home_base: Optional[str] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "visited_regions_count": len(self.visited_regions),
            "home_base": self.home_base
        }


@dataclass(frozen=True, slots=True)
class HabitMemory:
    """Phase 16 Shell."""
    patterns: Mapping[str, float] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"patterns": dict(sorted(self.patterns.items()))}


@dataclass(frozen=True, slots=True)
class CombatMemory:
    """Phase 4 Combat memory Shell."""
    opponent_stats: Mapping[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"opponents_tracked": len(self.opponent_stats)}


@dataclass(frozen=True, slots=True)
class SocialMemory:
    """Cooperation history Shell."""
    coop_outcomes: Tuple[Any, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"coop_records_count": len(self.SocialMemory.coop_outcomes) if hasattr(self, "SocialMemory") else 0}


@dataclass(frozen=True, slots=True)
class MemoryModel:
    """Aggregates causal, spatial, combat, habit, and social memory structures."""
    experience: ExperienceMemory = field(default_factory=ExperienceMemory)
    causal: CausalMemory = field(default_factory=CausalMemory)
    spatial: SpatialMemory = field(default_factory=SpatialMemory)
    habit: HabitMemory = field(default_factory=HabitMemory)
    combat: CombatMemory = field(default_factory=CombatMemory)
    social: SocialMemory = field(default_factory=SocialMemory)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "experience": self.experience.to_canonical_dict(),
            "causal": self.causal.to_canonical_dict(),
            "spatial": self.spatial.to_canonical_dict(),
            "habit": self.habit.to_canonical_dict(),
            "combat": self.combat.to_canonical_dict(),
            "social": self.social.to_canonical_dict()
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Motivation Model Sub-components
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class IdentityDoctrine:
    """Doctrine/class constraints.

    CONFIRMED DEAD LEGACY CODE (TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE, 2026-09-07): no
    real entity ever gets a non-default `class_id`, so this dataclass is always constructed with
    its bare defaults in production. See `src/domains/motivation/{resolver,service}.py`'s own
    module docstrings and `docs/guidelines/intentional_divergences.md` §2.53 for the full
    disclosure — superseded by `AdventureRouteScorer.score()`'s `personality_bias` mechanism.
    """
    class_id: Optional[str] = None
    preferred_route_tags: Mapping[str, float] = field(default_factory=dict)
    avoided_route_tags: Mapping[str, float] = field(default_factory=dict)
    combat_style_bias: Mapping[str, float] = field(default_factory=dict)
    cooperation_bias: Mapping[str, float] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "preferred_route_tags": {k: round(v, 4) for k, v in sorted(self.preferred_route_tags.items())},
            "avoided_route_tags": {k: round(v, 4) for k, v in sorted(self.avoided_route_tags.items())}
        }


@dataclass(frozen=True, slots=True)
class ValuePreferenceProfile:
    """Value scales (greed, pride, curiosity, caution).

    CONFIRMED DEAD LEGACY CODE (TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE, 2026-09-07): zero
    real construction of a non-default profile exists anywhere in `src/`, so every field stays at
    its bare 0.5 default in production. See `docs/guidelines/intentional_divergences.md` §2.53 for
    the full disclosure — superseded by `AdventureRouteScorer.score()`'s `personality_bias`
    mechanism.
    """
    survival: float = 0.5
    reward: float = 0.5
    knowledge: float = 0.5
    loyalty: float = 0.5
    pride: float = 0.5
    curiosity: float = 0.5
    caution: float = 0.5

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "survival": round(self.survival, 4),
            "reward": round(self.reward, 4),
            "knowledge": round(self.knowledge, 4),
            "loyalty": round(self.loyalty, 4),
            "pride": round(self.pride, 4),
            "curiosity": round(self.curiosity, 4),
            "caution": round(self.caution, 4)
        }


@dataclass(frozen=True, slots=True)
class RoleFitPreference:
    """Role/item class preferences."""
    weapon_tags: Mapping[str, float] = field(default_factory=dict)
    armor_tags: Mapping[str, float] = field(default_factory=dict)
    skill_tags: Mapping[str, float] = field(default_factory=dict)
    party_role_tags: Mapping[str, float] = field(default_factory=dict)
    quest_tags: Mapping[str, float] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "weapon_tags": {k: round(v, 4) for k, v in sorted(self.weapon_tags.items())},
            "armor_tags": {k: round(v, 4) for k, v in sorted(self.armor_tags.items())}
        }


@dataclass(frozen=True, slots=True)
class AmbitionProfile:
    """Future strategic objectives goals."""
    strategic_value_targets: Tuple[str, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"strategic_value_targets": list(self.strategic_value_targets)}


@dataclass(frozen=True, slots=True)
class MoralPreferenceProfile:
    """Moral behaviors scales."""
    altruism: float = 0.5

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"altruism": round(self.altruism, 4)}


@dataclass(frozen=True, slots=True)
class NamedIntentionBundle:
    """A dying wish seeded onto an heir at the moment of a benefactor's death
    (idea 58, A Dying Wish -- TCK-20260904-LINEAGE-DEATH-DISPATCH). Deliberately
    NOT named "Intention" -- that name already belongs to CommittedIntention
    (src/core/strategic.py), a distinct self-generated multi-step-planning model.
    Honorable, ignorable, or rejectable: nothing in this codebase reads `status`
    to force an action, so seeding this bundle never auto-executes anything."""
    text: Optional[str] = None
    source_entity_id: Optional[int] = None
    created_tick: Optional[int] = None
    status: str = "PENDING"  # PENDING | HONORED | REJECTED

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_entity_id": self.source_entity_id,
            "created_tick": self.created_tick,
            "status": self.status,
        }

    @classmethod
    def empty(cls) -> "NamedIntentionBundle":
        return cls()


@dataclass(frozen=True, slots=True)
class MotivationModel:
    """Identity values and traits that bias action selections."""
    doctrine: IdentityDoctrine = field(default_factory=IdentityDoctrine)
    values: ValuePreferenceProfile = field(default_factory=ValuePreferenceProfile)
    role_fit: RoleFitPreference = field(default_factory=RoleFitPreference)
    ambition: AmbitionProfile = field(default_factory=AmbitionProfile)
    moral: MoralPreferenceProfile = field(default_factory=MoralPreferenceProfile)
    named_intention: NamedIntentionBundle = field(default_factory=NamedIntentionBundle)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "doctrine": self.doctrine.to_canonical_dict(),
            "values": self.values.to_canonical_dict(),
            "role_fit": self.role_fit.to_canonical_dict(),
            "ambition": self.ambition.to_canonical_dict(),
            "moral": self.moral.to_canonical_dict(),
            "named_intention": self.named_intention.to_canonical_dict()
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Commitment Model Sub-components
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CommitmentEntry:
    """Quest or Contract obligation descriptor."""
    id: str
    kind: str
    target_id: Optional[str] = None
    strength: float = 1.0
    deadline_tick: Optional[int] = None
    created_tick: int = 0


@dataclass(frozen=True, slots=True)
class AbandonedCommitmentEntry:
    """Trace of broken obligations."""
    id: str
    tick_abandoned: int
    penalty: float = 0.0


@dataclass(frozen=True, slots=True)
class CommitmentModel:
    """Accepted active obligations and promises."""
    active_commitments: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    quest_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    contract_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    party_obligations: Mapping[str, CommitmentEntry] = field(default_factory=dict)
    abandoned_commitments: Tuple[AbandonedCommitmentEntry, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "active_commitments_count": len(self.active_commitments),
            "abandoned_commitments_count": len(self.abandoned_commitments)
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Relationship Model Sub-components
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class TrustEntry:
    """Private trust rating towards another entity."""
    entity_id: int
    value: float = 0.5
    bond_strength: float = 0.0


@dataclass(frozen=True, slots=True)
class PublicReputationProfile:
    """Public visible labels."""
    labels: Mapping[str, float] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {"labels": {k: round(v, 4) for k, v in sorted(self.labels.items())}}


@dataclass(frozen=True, slots=True)
class PartnerMemory:
    """History of dynamic party partnerships."""
    entity_id: int
    shared_quest_count: int = 0


@dataclass(frozen=True, slots=True)
class RelationshipModel:
    """Private social bonds, trust, public reputation, and betrayal logs."""
    private_trust: Mapping[int, TrustEntry] = field(default_factory=dict)
    public_reputation: PublicReputationProfile = field(default_factory=PublicReputationProfile)
    known_partners: Mapping[int, PartnerMemory] = field(default_factory=dict)
    betrayal_records: Tuple[Any, ...] = ()

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "private_trust_count": len(self.private_trust),
            "public_reputation": self.public_reputation.to_canonical_dict(),
            "betrayal_records_count": len(self.betrayal_records)
        }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Role Model Sub-components (TCK-20260831-ROLE-MODEL-IMITATION)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RoleModelBundle:
    """Who this entity watches/admires as a role model, and how faithfully it can imitate them."""
    admired_entity_id: Optional[int] = None
    admired_since_tick: Optional[int] = None
    last_reconsidered_tick: Optional[int] = None
    imitation_fidelity: float = 0.5  # matches RoleModelImitationService.DEFAULT_FIDELITY

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "admired_entity_id": self.admired_entity_id,
            "admired_since_tick": self.admired_since_tick,
            "last_reconsidered_tick": self.last_reconsidered_tick,
            "imitation_fidelity": round(self.imitation_fidelity, 4),
        }

    @classmethod
    def empty(cls) -> "RoleModelBundle":
        return cls()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Global CognitionModel Container
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CognitionModel:
    """The central unified nested hierarchy for all derived entity cognition."""
    subjective: SubjectiveModel = field(default_factory=SubjectiveModel)
    memory: MemoryModel = field(default_factory=MemoryModel)
    motivation: MotivationModel = field(default_factory=MotivationModel)
    commitment: CommitmentModel = field(default_factory=CommitmentModel)
    relationships: RelationshipModel = field(default_factory=RelationshipModel)
    role_model: RoleModelBundle = field(default_factory=RoleModelBundle)

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "subjective": self.subjective.to_canonical_dict(),
            "memory": self.memory.to_canonical_dict(),
            "motivation": self.motivation.to_canonical_dict(),
            "commitment": self.commitment.to_canonical_dict(),
            "relationships": self.relationships.to_canonical_dict(),
            "role_model": self.role_model.to_canonical_dict()
        }

    @classmethod
    def empty(cls) -> "CognitionModel":
        return cls()
