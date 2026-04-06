from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, TypeVar, Generic, Union

from pydantic import Field

from src.core.models.enums import ActionType, GoalType, EmotionType

from src.core.models.vectors import Vector2
if TYPE_CHECKING:
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src.core.aspects.combat import CombatTraceRecord
    from src.core.gameplay.classes import SkillInstance
    from src.core.quests import Quest
    from src.core.effects import StatusEffect
    from src.core.gameplay.effects import EffectType


from pydantic import Field, model_validator
from src.core.models.base import SimulationModel
from src.core.models.types import TargetUnion, BuildingTarget
from src.core.models.combat import CombatTraceRecord, CombatTraceDetails

class ActionBatch(SimulationModel):
    """A batch of action proposals for a specific tick, used for Kafka/Persistence."""
    tick: int
    proposals: list[ActionProposal] = Field(default_factory=list)

class ActionProposal(SimulationModel):
    """An intent produced by a worker thread. [AOA STABILIZATION]
    
    The WorldLoop validates and applies (or rejects) each proposal.
    Pillar 3: Conflict Resolution & Authoritative Application.
    """

    actor_id: int
    verb: ActionType
    target: TargetUnion = None
    reason: str = ""
    new_ai_state: int | None = None
    
    # Typed updates for state synchronization (AOA Phase 5)
    updates: list[IntentUpdate] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='before')
    @classmethod
    def _validate_target(cls, data: Any) -> Any:
        """AOA Stabilization: Ensure target is correctly coerced from dict to Vector2."""
        if not isinstance(data, dict):
            return data
        target = data.get("target")
        if isinstance(target, dict) and "x" in target and "y" in target:
            # Import Vector2 here to avoid circular dependencies
            from src.core.models.vectors import Vector2
            data["target"] = Vector2.model_validate(target)
        return data

    def __repr__(self) -> str:
        count = len(self.updates)
        verb_name = self.verb.name if hasattr(self.verb, "name") else ActionType(self.verb).name
        return f"Proposal(entity={self.actor_id}, {verb_name} updates={count}, target={self.target}, reason={self.reason!r})"

class IntentUpdate(SimulationModel):
    """Base for all typed simulation side-effects."""
    pass

from pydantic import model_validator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src.core.models.vectors import Vector2

class MindUpdate(IntentUpdate):
    """Updates to the entity's Decision, Perception, or Emotion state."""
    goal_scores: dict[GoalType, float] | None = None
    last_goal: GoalType | None = None
    goal_committed_at: int | None = None
    boredom_delta: dict[GoalType, float] | None = None
    new_ai_state: int | None = None
    consecutive_idle_ticks: int | None = None
    
    # AI Goals
    goals_add: list[str] | None = None
    goals_remove: list[str] | None = None
    
    # Emotion
    emotion_delta: dict[EmotionType, float] | None = None
    emotion_set: dict[EmotionType, float] | None = None
    mood: float | None = None
    grudge_delta: dict[int, float] | None = None

class PerceptionUpdate(IntentUpdate):
    """Updates to sensory memory and spatial awareness. [AOA STABILIZATION]"""
    entity_memory: dict[int, MemoryRecord] | None = None
    memory_stale_delta: dict[int, int] | None = None
    memory_remove: list[int] | None = None
    attention_pool: list[int] | None = None
    terrain_memory: dict[tuple[int, int], int] | None = None
    
    # Narrative
    memory_log_add: list[MemoryLogEntry] | None = None
    memory_locations_set: dict[str, float] | None = None
    
    # Tactical
    threat_delta: dict[int, float] | None = None

    @model_validator(mode="after")
    def _coerce_memory(self) -> "PerceptionUpdate":
        if self.entity_memory:
            from src.core.aspects.mind import MemoryRecord
            for eid, rec in self.entity_memory.items():
                if isinstance(rec, dict):
                    self.entity_memory[eid] = MemoryRecord.model_validate(rec)
        
        if self.memory_log_add:
            from src.core.aspects.mind import MemoryLogEntry
            self.memory_log_add = [
                MemoryLogEntry.model_validate(m) if isinstance(m, dict) else m 
                for m in self.memory_log_add
            ]
        return self

class NavigationUpdate(IntentUpdate):
    """Updates to pathfinding memory and history. [AOA STABILIZATION]"""
    pos_history: list[Vector2] | None = None
    cached_path: list[Vector2] | None = None
    target_pos: Vector2 | None = None
    chase_ticks: int | None = None

    @model_validator(mode="after")
    def _coerce_navigation(self) -> "NavigationUpdate":
        from src.core.models.vectors import Vector2
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
        if isinstance(self.target_pos, dict):
            self.target_pos = Vector2.model_validate(self.target_pos)
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

    @model_validator(mode="after")
    def _coerce_progression(self) -> "ProgressionUpdate":
        # Pydantic dataclasses (SkillInstance, Quest, StatusEffect) 
        # might need coercion if they come from loose dicts (e.g. from workers)
        from src.core.gameplay.classes import SkillInstance
        from src.core.quests import Quest
        from src.core.effects import StatusEffect
        from src.core.gameplay.effects import EffectType
        from src.core.gameplay.effects import EffectType
        
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
        return self

class IdentityUpdate(IntentUpdate):
    """Updates to permanent traits and recipes."""
    recipes_learn: list[str] | None = None
    craft_target: str | None = None
    hero_class: int | None = None
    reputation_delta: float = 0.0

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

    @model_validator(mode="after")
    def _coerce_spatial(self) -> "SpatialUpdate":
        from src.core.models.vectors import Vector2
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
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry, CombatNarrative, LootNarrative, DiscoveryNarrative
    from src.core.aspects.combat import CombatAspect
    from src.core.models.combat import CombatTraceRecord, CombatTraceDetails
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    
    # Gameplay Components (needed for ProgressionUpdate)
    from src.core.gameplay.classes import SkillInstance
    from src.core.quests import Quest
    from src.core.effects import StatusEffect
    from src.core.gameplay.effects import EffectType
    
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
    CombatTraceUpdate.model_rebuild(_types_namespace=ns)
    
    # 2. Finalize Aggregate Models
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
