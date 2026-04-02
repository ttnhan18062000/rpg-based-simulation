from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, TypeVar, Generic

from pydantic import Field

from src.core.models.enums import ActionType, GoalType, EmotionType

if TYPE_CHECKING:
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src.core.aspects.combat import CombatTraceRecord
    from src.core.models.vectors import Vector2
    from src.core.gameplay.classes import SkillInstance
    from src.core.quests import Quest
    from src.core.effects import StatusEffect


from src.core.models.base import SimulationModel

class ActionProposal(SimulationModel):
    """An intent produced by a worker thread. [AOA STABILIZATION]
    
    The WorldLoop validates and applies (or rejects) each proposal.
    Pillar 3: Conflict Resolution & Authoritative Application.
    """

    actor_id: int
    verb: ActionType
    target: Any = None
    reason: str = ""
    new_ai_state: int | None = None
    
    # Typed updates for state synchronization (AOA Phase 5)
    updates: list[IntentUpdate] = Field(default_factory=list)
    
    # Legacy metadata bucket (DEPRECATED: Use typed 'updates' instead)
    intent_metadata: dict[str, Any] = Field(default_factory=dict)

    def __repr__(self) -> str:
        meta_count = len(self.intent_metadata) + len(self.updates)
        meta_str = f" meta={meta_count}" if meta_count else ""
        verb_name = self.verb.name if hasattr(self.verb, "name") else ActionType(self.verb).name
        return f"Proposal(entity={self.actor_id}, {verb_name}{meta_str}, target={self.target}, reason={self.reason!r})"

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
    
    # Tactical
    threat_table_delta: dict[int, float] | None = None

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
    target_pos: Any | None = None # Vector2
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
    hp_delta: int = 0
    stamina_delta: int = 0
    
    inventory_add: list[str] = Field(default_factory=list)
    inventory_remove: list[str] = Field(default_factory=list)
    
    skills_add: list[SkillInstance] = Field(default_factory=list)
    attribute_cap_delta: dict[str, int] | None = None
    
    quest_add: list[Quest] = Field(default_factory=list)
    
    # Status Effects (CombatAspect)
    effects_add: list[StatusEffect] = Field(default_factory=list)
    effects_remove: list[str] = Field(default_factory=list) # by effect_id or source

    @model_validator(mode="after")
    def _coerce_progression(self) -> "ProgressionUpdate":
        # Pydantic dataclasses (SkillInstance, Quest, StatusEffect) 
        # might need coercion if they come from loose dicts (e.g. from workers)
        from src.core.gameplay.classes import SkillInstance
        from src.core.quests import Quest
        from src.core.effects import StatusEffect
        
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

class CombatTraceDetails(SimulationModel):
    """Structured detail for combat exchanges. [AOA STABILIZATION]"""
    raw_damage: int = 0
    mitigated_damage: int = 0
    absorbed_damage: int = 0
    
    crit_multiplier: float = 1.0
    evasion_chance: float = 0.0
    
    effect_triggers: list[str] = Field(default_factory=list)
    elemental_mult: float = 1.0

class CombatTraceUpdate(IntentUpdate):
    """Rich trace data for introspection. [AOA STABILIZATION]
    
    Pillar 2: Introspection & Rendering. Traces provide the explainability
    needed for the frontend to render detailed combat logs.
    """
    tick: int
    attacker_id: int
    defender_id: int
    damage: int
    is_crit: bool
    is_evasion: bool
    skill_used: str = "attack"
    details: CombatTraceDetails = Field(default_factory=CombatTraceDetails)

# --- AOA Stabilization: Deferred Model Rebuild for Circular Dependencies ---
# These types are needed at runtime for validation but cause circular imports 
# if imported at the top level.

def _rebuild_action_models():
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src.core.models.vectors import Vector2
    from src.core.gameplay.classes import SkillInstance
    from src.core.quests import Quest
    from src.core.effects import StatusEffect

    # Rebuild all update models to pick up the actual types
    ActionProposal.model_rebuild()
    MindUpdate.model_rebuild()
    PerceptionUpdate.model_rebuild()
    NavigationUpdate.model_rebuild()
    ProgressionUpdate.model_rebuild()
    IdentityUpdate.model_rebuild()
    InteractionUpdate.model_rebuild()
    CombatTraceUpdate.model_rebuild()

try:
    _rebuild_action_models()
except (ImportError, NameError):
    # This might happen during initial bootstrap, the orchestrator 
    # will call it again if needed.
    pass
