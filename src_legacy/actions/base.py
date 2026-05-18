from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, TypeVar, Generic, Union

from pydantic import Field

from src_legacy.core.models.enums import ActionType, GoalType, EmotionType, PersonalMotiveType, MovementIntention

from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.reason_codes import ActionReason, ReasonCode
if TYPE_CHECKING:
    from src_legacy.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src_legacy.core.aspects.combat import CombatTraceRecord
    from src_legacy.core.gameplay.classes import SkillInstance
    from src_legacy.core.gameplay.quests import Quest
    from src_legacy.core.effects import StatusEffect
    from src_legacy.core.gameplay.effects import EffectType
    from src_legacy.core.models.consequence import Consequence


from pydantic import Field, model_validator
from src_legacy.core.models.base import SimulationModel
from src_legacy.core.models.types import TargetUnion, BuildingTarget
from src_legacy.core.models.combat import CombatTraceRecord, CombatTraceDetails
from src_legacy.core.models.cognition import CognitionCapacityProfile

class ActionBatch(SimulationModel):
    """A batch of action proposals for a specific tick, used for Kafka/Persistence."""
    TRIPWIRE_EXEMPT: typing.ClassVar[bool] = True
    tick: int
    proposals: list[ActionProposal] = Field(default_factory=list)

class ActionProposal(SimulationModel):
    """An intent produced by a worker thread. [AOA STABILIZATION]
    
    The WorldLoop validates and applies (or rejects) each proposal.
    Pillar 3: Conflict Resolution & Authoritative Application.
    """
    TRIPWIRE_EXEMPT: typing.ClassVar[bool] = True
    actor_id: int
    verb: ActionType
    target: TargetUnion | None = None
    reason: ActionReason = Field(default_factory=lambda: ActionReason(code=ReasonCode.ADVANCING)) # [Milestone 7] Strictly typed
    new_ai_state: int | None = None
    
    # Typed updates for state synchronization (AOA Phase 5)
    updates: list[IntentUpdate] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='before')
    @classmethod
    def _coerce_action_fields(cls, data: Any) -> Any:
        """AOA Stabilization: Ensure fields are correctly coerced for project closure."""
        if not isinstance(data, dict):
            return data
            
        # Coerce reason from str to ActionReason [Milestone 7 Authoritative]
        reason = data.get("reason")
        if isinstance(reason, str):
            from src_legacy.core.models.reason_codes import ActionReason, ReasonCode
            
            # Known mapping for common legacy strings
            mapping = {
                "Occupied": ReasonCode.OCCUPANCY_VIOLATION,
                "Out of range": ReasonCode.OUT_OF_RANGE,
                "Low HP": ReasonCode.LOW_HP_RETREAT,
                "No target": ReasonCode.NO_TARGET,
                "Target reached": ReasonCode.TARGET_REACHED,
                "Target invalid": ReasonCode.TARGET_INVALID,
                "Exhaustion": ReasonCode.ACTION_EXHAUSTION,
            }
            code = mapping.get(reason, ReasonCode.LEGACY_FALLBACK)
            data["reason"] = ActionReason(
                code=code, 
                metadata={"detail": reason} if code == ReasonCode.LEGACY_FALLBACK else {},
                is_rejection=True # Legacy strings in proposals are usually rejections
            )
            
        # Coerce target from dict to Vector2 if needed
        target = data.get("target")
        if isinstance(target, dict) and "x" in target and "y" in target:
            from src_legacy.core.models.vectors import Vector2
            data["target"] = Vector2.model_validate(target)
            
        return data

    @property
    def reason_text(self) -> str:
        """Compatibility property for legacy code expecting a string."""
        return str(self.reason)

    def __repr__(self) -> str:
        count = len(self.updates)
        verb_name = self.verb.name if hasattr(self.verb, "name") else ActionType(self.verb).name
        return f"Proposal(entity={self.actor_id}, {verb_name} updates={count}, target={self.target}, reason={self.reason!r})"

class IntentUpdate(SimulationModel):
    """Base for all typed simulation side-effects."""
    TRIPWIRE_EXEMPT: typing.ClassVar[bool] = True
    actor_id: int = 0
    verb: ActionType = ActionType.REST
    target_id: int | None = None
    target: Vector2 | None = None # [AOA] Renamed from target_pos to target for consistency with Proposal
    reason: ActionReason = Field(default_factory=lambda: ActionReason(code=ReasonCode.ADVANCING)) # [Milestone 7] Strictly typed

    @property
    def target_pos(self) -> Vector2 | None:
        """Alias for compatibility."""
        return self.target

    @model_validator(mode='before')
    @classmethod
    def _coerce_intent_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        # Handle legacy target_pos
        if "target_pos" in data and "target" not in data:
            data["target"] = data.pop("target_pos")
            
        reason = data.get("reason")
        if isinstance(reason, str):
            from src_legacy.core.models.reason_codes import ActionReason, ReasonCode
            # Simple fallback for intent updates (rarely rejections)
            data["reason"] = ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": reason})
        return data

from pydantic import model_validator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src_legacy.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src_legacy.core.models.vectors import Vector2

class MindUpdate(IntentUpdate):
    """Updates to the entity's Decision, Perception, or Emotion state."""
    goal_scores: dict[GoalType, float] | None = None
    motives: list[PersonalMotive] | None = None # [PHASE 1]
    motive_utility_biases: dict[GoalType, float] | None = None # [PHASE 1]
    last_appraisal_tick: int | None = None        # [STAGE 1]
    last_goal: GoalType | None = None
    decision_drivers: list[str] | None = None      # [STAGE 1] Legacy prose
    driver_details: list[DecisionDriver] | None = None # [STAGE 1] Structured records
    goal_committed_at: int | None = None
    boredom_delta: dict[GoalType, float] | None = None
    new_ai_state: int | None = None
    consecutive_idle_ticks: int | None = None
    
    # Emotion
    emotion_delta: dict[EmotionType, float] | None = None
    emotion_set: dict[EmotionType, float] | None = None
    mood: float | None = None
    grudge_delta: dict[int, float] | None = None
    
    # Social Integration [STAGE 2]
    social_update: Any | None = None

class PerceptionUpdate(IntentUpdate):
    """Updates to sensory memory and spatial awareness. [AOA STABILIZATION]"""
    entity_memory: dict[int, MemoryRecord] | None = None
    memory_stale_delta: dict[int, int] | None = None
    memory_remove: list[int] | None = None
    attention_pool: list[int] | None = None
    terrain_memory: dict[tuple[int, int], int] | None = None
    
    # Narrative
    memory_log_add: list[MemoryLogEntry] | None = None
    turning_points_add: list[TurningPointRecord] | None = None
    memory_locations_set: dict[str, float] | None = None
    
    # Tactical
    threat_delta: dict[int, float] | None = None

    @model_validator(mode="after")
    def _coerce_memory(self) -> "PerceptionUpdate":
        if self.entity_memory:
            from src_legacy.core.aspects.mind import MemoryRecord
            for eid, rec in self.entity_memory.items():
                if isinstance(rec, dict):
                    self.entity_memory[eid] = MemoryRecord.model_validate(rec)
        
        if self.memory_log_add:
            from src_legacy.core.aspects.mind import MemoryLogEntry
            self.memory_log_add = [
                MemoryLogEntry.model_validate(m) if isinstance(m, dict) else m 
                for m in self.memory_log_add
            ]
            
        if self.turning_points_add:
            from src_legacy.core.models.life_events import TurningPointRecord
            self.turning_points_add = [
                TurningPointRecord.model_validate(t) if isinstance(t, dict) else t 
                for t in self.turning_points_add
            ]
            
        if isinstance(self.memory_locations_set, list):
            self.memory_locations_set = dict(self.memory_locations_set)
            
        return self

class NavigationUpdate(IntentUpdate):
    """Updates to pathfinding memory and history. [AOA STABILIZATION]"""
    pos_history: list[Vector2] | None = None
    cached_path: list[Vector2] | None = None
    chase_ticks: int | None = None
    engaged_ticks: int | None = None
    stalemate_counter: int | None = None
    last_ai_state: int | None = None
    last_target_id: int | None = None
    intention: MovementIntention | None = None
    blocked_ticks: int | None = None
    oscillation_counter: int | None = None
    last_route_hash: str | None = None
    @model_validator(mode="after")
    def _coerce_navigation(self) -> "NavigationUpdate":
        from src_legacy.core.models.vectors import Vector2
        if self.pos_history:
            self.pos_history = [
                Vector2.model_validate(p) if isinstance(p, dict) else p 
                for p in self.pos_history
            ]
        if self.cached_path:
            self.cached_path = [
                Vector2.model_validate(p) if isinstance(p, dict) else p 
                for p in self.cached_path
            ]
        return self

class ProgressionUpdate(IntentUpdate):
    """Updates to gold, stats, level, and skills."""
    gold_delta: int = 0
    xp_delta: int = 0
    age_ticks_delta: int = 0
    veterancy_points_delta: int = 0
    hp_delta: int = 0
    max_hp_delta: int = 0
    stamina_delta: int = 0
    combat_target_id: int | None = None
    
    inventory_add: list[str] = Field(default_factory=list)
    inventory_remove: list[str] = Field(default_factory=list)
    
    skills_add: list[SkillInstance] = Field(default_factory=list)
    skill_cooldowns: dict[str, int] | None = None
    attribute_cap_delta: dict[str, int] | None = None
    
    quest_add: list[Quest] = Field(default_factory=list)
    
    # [AOA STABILIZATION] Fame & Narrative Titles
    fame_delta: int = 0
    titles_add: list[str] = Field(default_factory=list)
    
    # Status Effects (CombatAspect)
    effects_add: list[StatusEffect] = Field(default_factory=list)
    effects_remove: list[str] = Field(default_factory=list) # by effect_id or source
    effects_expire_all: list[EffectType] = Field(default_factory=list)
    
    # Consequences (CombatAspect) [Milestone 5]
    consequences_add: list[Consequence] = Field(default_factory=list)
    consequences_remove: list[str] = Field(default_factory=list) # by id

    @model_validator(mode="after")
    def _coerce_progression(self) -> "ProgressionUpdate":
        # Pydantic dataclasses (SkillInstance, Quest, StatusEffect) 
        # might need coercion if they come from loose dicts (e.g. from workers)
        from src_legacy.core.gameplay.classes import SkillInstance
        from src_legacy.core.gameplay.quests import Quest
        from src_legacy.core.effects import StatusEffect
        from src_legacy.core.gameplay.effects import EffectType
        from src_legacy.core.gameplay.effects import EffectType
        
        if self.skills_add:
            self.skills_add = [
                SkillInstance(**s) if isinstance(s, dict) else s 
                for s in self.skills_add
            ]
        if self.quest_add:
            self.quest_add = [
                Quest(**q) if isinstance(q, dict) else q 
                for q in self.quest_add
            ]
        if self.effects_add:
            self.effects_add = [
                StatusEffect(**e) if isinstance(e, dict) else e 
                for e in self.effects_add
            ]
        if self.consequences_add:
            from src_legacy.core.models.consequence import Consequence
            self.consequences_add = [
                Consequence(**c) if isinstance(c, dict) else c 
                for c in self.consequences_add
            ]
        return self

class IdentityUpdate(IntentUpdate):
    """Updates to permanent traits and recipes."""
    recipes_learn: list[str] | None = None
    craft_target: str | None = None
    hero_class: int | None = None
    reputation_delta: float = 0.0

class RoutineUpdate(IntentUpdate):
    """Updates to biological needs and routine state. [STAGE 4]"""
    sleep_delta: float | None = None
    hunger_delta: float | None = None
    is_sleeping: bool | None = None

class InteractionUpdate(IntentUpdate):
    """Updates to temporary interaction state or storage."""
    loot_progress_delta: float = 0.0
    loot_progress_set: float | None = None
    
    home_storage_upgrade: bool = False
    home_storage_add: list[str] | None = None
    home_storage_remove: list[str] | None = None
    
    corpse_id_to_remove: int | None = None

class SpatialUpdate(IntentUpdate):
    """Updates to physical position and spatial index. [AOA STABILIZATION]"""
    new_pos: Vector2
    facing: Vector2 | None = None
    region_id: str | None = None
    moved_this_tick: bool | None = None

    @model_validator(mode="after")
    def _coerce_spatial(self) -> "SpatialUpdate":
        from src_legacy.core.models.vectors import Vector2
        if isinstance(self.new_pos, dict):
            self.new_pos = Vector2.model_validate(self.new_pos)
        if isinstance(self.facing, dict):
            self.facing = Vector2.model_validate(self.facing)
        return self

class BuildingUpdate(IntentUpdate):
    """Updates to building durability or state."""
    building_id: str
    repair_amount: float = 0.0
    damage_amount: float = 0.0
    is_destroyed: bool = False

class SocialUpdate(IntentUpdate):
    """Updates to systemic social bonds. [PHASE 1]"""
    source_id: int
    target_id: int
    trust_delta: float = 0.0
    fear_delta: float = 0.0
    rivalry_delta: float = 0.0
    familiarity_delta: float = 0.0
    loyalty_delta: float = 0.0
    resentment_delta: float = 0.0
    admiration_delta: float = 0.0
    debt_delta: float = 0.0

class SocialEventUpdate(IntentUpdate):
    """Update for pushing interpreted life events from the AI back to the system. [PHASE 3]"""
    events_add: list[InterpretedLifeEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coerce_social_events(self) -> "SocialEventUpdate":
        from src_legacy.core.models.life_events import InterpretedLifeEvent
        if self.events_add:
            self.events_add = [
                InterpretedLifeEvent(**e) if isinstance(e, dict) else e 
                for e in self.events_add
            ]
        return self

class ReputationUpdate(IntentUpdate):
    """Updates to an entity's public reputation profile. [PHASE 2]"""
    defender_delta: float = 0.0
    cowardice_delta: float = 0.0
    greed_delta: float = 0.0
    heroism_delta: float = 0.0
    threat_notoriety_delta: float = 0.0
    trustworthiness_delta: float = 0.0
    tags_add: list[str] = Field(default_factory=list)
    tags_remove: list[str] = Field(default_factory=list)

class StrategicUpdate(IntentUpdate):
    """Updates to the entity's Strategic stratum. [PHASE 1]"""
    directives_add: list[DirectiveRecord] = Field(default_factory=list)
    directives_remove: list[str] = Field(default_factory=list)
    
    blockers_add_or_update: list[BlockerRecord] = Field(default_factory=list)
    blockers_remove: list[str] = Field(default_factory=list)
    
    projects_add_or_update: list[ProjectRecord] = Field(default_factory=list)
    projects_remove: list[str] = Field(default_factory=list)
    
    concerns_add_or_update: list[ConcernRecord] = Field(default_factory=list)
    concerns_remove: list[str] = Field(default_factory=list)
    
    obligations_add_or_update: list[ObligationRecord] = Field(default_factory=list)
    obligations_remove: list[str] = Field(default_factory=list)
    
    contracts_add_or_update: list[SocialContractRecord] = Field(default_factory=list)
    contracts_remove: list[str] = Field(default_factory=list)
    
    offers_add_or_update: list[RecruitmentOfferRecord] = Field(default_factory=list)
    offers_remove: list[str] = Field(default_factory=list)
    
    leads_add_or_update: list[LeadRecord] = Field(default_factory=list)
    leads_remove: list[str] = Field(default_factory=list)
    
    # [phase_3_task_3]
    candidate_zones_add_or_update: list[CandidateZoneRecord] = Field(default_factory=list)
    candidate_zones_remove: list[str] = Field(default_factory=list)
    
    hypotheses_add_or_update: list[HypothesisRecord] = Field(default_factory=list)
    hypotheses_remove: list[str] = Field(default_factory=list)
    
    current_project_id: str | None = None
    current_objective_id: str | None = None
    interrupted_project_id: str | None = None
    project_lock_until: int | None = None
    engaged_ticks: int | None = None
    last_interpreted_event_tick: int | None = None
    tested_lead_ids: list[str] = Field(default_factory=list)
    source_trust_updates: dict[str, float] = Field(default_factory=dict)
    
    # Traceability [PHASE 2]
    strategic_drivers: list[DecisionDriver] = Field(default_factory=list)
    
    # Cognitive Bounding Metrics [phase_2_intel_capacity]
    last_capacity_profile: CognitionCapacityProfile | None = None
    active_slice_used: int | None = None
    active_concerns_used: int | None = None
    retained_leads_used: int | None = None
    candidate_zones_used: int | None = None
    ally_evaluations_used: int | None = None
    detour_depth_used: int | None = None
    dropped_candidates_count: int | None = None
    latent_concerns_count: int | None = None
    is_overloaded: bool | None = None
    overload_score: float | None = None
    primary_overload_source: str | None = None
    last_overload_tick: int | None = None

    @model_validator(mode="after")
    def _coerce_strategic(self) -> "StrategicUpdate":
        """Force coercion of strategic records if they came in as dicts."""
        from src_legacy.core.models.strategy import (
            DirectiveRecord, ProjectRecord, ConcernRecord, 
            ObligationRecord, SocialContractRecord, LeadRecord,
            CandidateZoneRecord, HypothesisRecord
        )
        if self.directives_add:
            self.directives_add = [DirectiveRecord.model_validate(d) if isinstance(d, dict) else d for d in self.directives_add]
        if self.projects_add_or_update:
            self.projects_add_or_update = [ProjectRecord.model_validate(p) if isinstance(p, dict) else p for p in self.projects_add_or_update]
        if self.concerns_add_or_update:
            self.concerns_add_or_update = [ConcernRecord.model_validate(c) if isinstance(c, dict) else c for c in self.concerns_add_or_update]
        if self.obligations_add_or_update:
            self.obligations_add_or_update = [ObligationRecord.model_validate(o) if isinstance(o, dict) else o for o in self.obligations_add_or_update]
        if self.contracts_add_or_update:
            self.contracts_add_or_update = [SocialContractRecord.model_validate(s) if isinstance(s, dict) else s for s in self.contracts_add_or_update]
        if self.offers_add_or_update:
            self.offers_add_or_update = [RecruitmentOfferRecord.model_validate(o) if isinstance(o, dict) else o for o in self.offers_add_or_update]
        if self.leads_add_or_update:
            self.leads_add_or_update = [LeadRecord.model_validate(l) if isinstance(l, dict) else l for l in self.leads_add_or_update]
        return self


class WorldUpdate(IntentUpdate):
    """Authoritative updates to global world state (Corpses, Idents, Spawns). [AOA STABILIZATION]"""
    # Pillar 1 fix: mutations must be authoritative.
    new_corpse: Any | None = None # Avoiding circular import with CorpseNode
    increment_corpse_id: bool = False
    new_entity: Any | None = None # Avoiding circular import with Entity

class CombatTraceUpdate(IntentUpdate):
    """Refined trace wrapper to provide a unified combat result to the engine. [AOA STABILIZATION]"""
    result: CombatTraceRecord = Field(default_factory=lambda: CombatTraceRecord(tick=0, attacker_id=0, defender_id=0, damage=0))

# --- AOA Stabilization: Deferred Model Rebuild for Circular Dependencies ---
# These types are needed at runtime for validation but cause circular imports 
# if imported at the top level.

def _rebuild_action_models():
    """Centrally orchestrate Pydantic model rebuilds to resolve circular dependencies."""
    # Domain Aspects & Models
    # Domain Aspects & Models
    from src_legacy.core.aspects.mind import (
        MemoryRecord, MemoryLogEntry, CombatNarrative, LootNarrative, 
        DiscoveryNarrative, PersonalMotive, DecisionDriver
    )
    from src_legacy.core.models.life_events import (
        TurningPointRecord, InterpretedLifeEvent
    )
    from src_legacy.core.aspects.combat import CombatAspect
    from src_legacy.core.models.combat import CombatTraceRecord, CombatTraceDetails
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.snapshot import Snapshot
    
    # Gameplay Components (needed for ProgressionUpdate)
    from src_legacy.core.gameplay.classes import SkillInstance
    from src_legacy.core.gameplay.quests import Quest
    from src_legacy.core.effects import StatusEffect
    from src_legacy.core.gameplay.effects import EffectType
    from src_legacy.core.models.consequence import Consequence
    
    # Strategic Components (needed for StrategicUpdate) [PHASE 1]
    from src_legacy.core.models.strategy import (
        DirectiveRecord, ProjectRecord, ConcernRecord, 
        ObligationRecord, SocialContractRecord, RecruitmentOfferRecord,
        ContractTermRecord, LeadRecord, CandidateZoneRecord, HypothesisRecord,
        BlockerRecord
    )
    
    # Create a unified namespace for Pydantic to resolve string forward references
    ns = locals().copy()
    # Also include the module's own globals for things like ActionProposal, etc.
    ns.update(globals())
    
    # 1. Rebuild Intent Update Models (AOA Stabilization)
    MindUpdate.model_rebuild(_types_namespace=ns)
    PerceptionUpdate.model_rebuild(_types_namespace=ns)
    NavigationUpdate.model_rebuild(_types_namespace=ns)
    ProgressionUpdate.model_rebuild(_types_namespace=ns)
    IdentityUpdate.model_rebuild(_types_namespace=ns)
    InteractionUpdate.model_rebuild(_types_namespace=ns)
    SpatialUpdate.model_rebuild(_types_namespace=ns)
    BuildingUpdate.model_rebuild(_types_namespace=ns)
    SocialUpdate.model_rebuild(_types_namespace=ns)
    ReputationUpdate.model_rebuild(_types_namespace=ns)
    RoutineUpdate.model_rebuild(_types_namespace=ns)
    SocialEventUpdate.model_rebuild(_types_namespace=ns)
    StrategicUpdate.model_rebuild(_types_namespace=ns)
    CombatTraceUpdate.model_rebuild(_types_namespace=ns)
    
    # 2. Finalize Aggregate Models
    from src_legacy.core.models.reason_codes import ActionReason
    ActionReason.model_rebuild(_types_namespace=ns)
    ActionProposal.model_rebuild(_types_namespace=ns)
    ActionBatch.model_rebuild(_types_namespace=ns)

try:
    _rebuild_action_models()
except Exception as e:
    # Fail loudly in development/test if rebuild fails
    import os, logging
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("CI"):
        raise e
    logging.getLogger(__name__).debug("Deferred model rebuild skipped: %s", e)

