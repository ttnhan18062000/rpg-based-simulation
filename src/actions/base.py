from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from src.core.models.enums import ActionType, GoalType, EmotionType

if TYPE_CHECKING:
    from src.core.aspects.mind import MemoryRecord, MemoryLogEntry
    from src.core.aspects.combat import CombatTraceRecord


@dataclass(frozen=True, slots=True)
class ActionProposal:
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
    updates: list[IntentUpdate] = field(default_factory=list)
    
    # Legacy metadata bucket (to be deprecated)
    intent_metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        meta_count = len(self.intent_metadata) + len(self.updates)
        meta_str = f" meta={meta_count}" if meta_count else ""
        verb_name = self.verb.name if hasattr(self.verb, "name") else ActionType(self.verb).name
        return f"Proposal(entity={self.actor_id}, {verb_name}{meta_str}, target={self.target}, reason={self.reason!r})"

@dataclass(frozen=True, slots=True)
class IntentUpdate:
    """Base for all typed simulation side-effects."""
    pass

@dataclass(frozen=True, slots=True)
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
    emotion_delta: dict[EmotionType, float] | None = None # e.g. {EmotionType.PANIC: 0.1}
    emotion_set: dict[EmotionType, float] | None = None   # e.g. {EmotionType.STUCK: 1.0}
    mood: float | None = None
    grudge_delta: dict[int, float] | None = None

@dataclass(frozen=True, slots=True)
class PerceptionUpdate(IntentUpdate):
    """Updates to sensory memory and spatial awareness."""
    entity_memory: dict[int, MemoryRecord] | None = None
    memory_stale_delta: dict[int, int] | None = None
    memory_remove: list[int] | None = None
    attention_pool: list[int] | None = None
    terrain_memory: dict[tuple[int, int], int] | None = None
    
    # Narrative
    memory_log_add: list[MemoryLogEntry] | None = None
    
    # Tactical
    threat_table_delta: dict[int, float] | None = None

@dataclass(frozen=True, slots=True)
class NavigationUpdate(IntentUpdate):
    """Updates to pathfinding memory and history."""
    pos_history: list[Any] | None = None # list[Vector2]
    cached_path: list[Any] | None = None # list[Vector2]
    target_pos: Any | None = None # Vector2
    chase_ticks: int | None = None

@dataclass(frozen=True, slots=True)
class ProgressionUpdate(IntentUpdate):
    """Updates to gold, stats, level, and skills."""
    gold_delta: int = 0
    xp_delta: int = 0
    hp_delta: int = 0
    stamina_delta: int = 0
    
    inventory_add: list[str] = field(default_factory=list)
    inventory_remove: list[str] = field(default_factory=list)
    
    skills_add: list[Any] = field(default_factory=list) # list[SkillInstance or ID]
    attribute_cap_delta: dict[str, int] | None = None
    
    quest_add: list[Any] = field(default_factory=list)
    
    # Status Effects (CombatAspect)
    effects_add: list[Any] = field(default_factory=list)
    effects_remove: list[str] = field(default_factory=list) # by effect_id or source

@dataclass(frozen=True, slots=True)
class IdentityUpdate(IntentUpdate):
    """Updates to permanent traits and recipes."""
    recipes_learn: list[str] | None = None
    craft_target: str | None = None
    hero_class: int | None = None
    reputation_delta: float = 0.0

@dataclass(frozen=True, slots=True)
class InteractionUpdate(IntentUpdate):
    """Updates to temporary interaction state or storage."""
    loot_progress_delta: float = 0.0
    loot_progress_set: float | None = None
    
    home_storage_upgrade: bool = False
    home_storage_add: list[str] | None = None
    home_storage_remove: list[str] | None = None
    
    corpse_id_to_remove: int | None = None

@dataclass(frozen=True, slots=True)
class CombatTraceDetails:
    """Structured detail for combat exchanges. [AOA STABILIZATION]"""
    raw_damage: int = 0
    mitigated_damage: int = 0
    absorbed_damage: int = 0
    
    crit_multiplier: float = 1.0
    evasion_chance: float = 0.0
    
    effect_triggers: list[str] = field(default_factory=list)
    elemental_mult: float = 1.0

@dataclass(frozen=True, slots=True)
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
    details: CombatTraceDetails = field(default_factory=CombatTraceDetails)
