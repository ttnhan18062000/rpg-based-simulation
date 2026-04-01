from typing import Any, TYPE_CHECKING, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from src.core.models.base import Aspect, SimulationModel
from src.core.models.enums import AIState, GoalType, EmotionType
from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class DecisionState(SimulationModel):
    """Internal state for AI goal selection and commitment."""
    model_config = ConfigDict(extra='forbid', use_enum_values=True)
    
    ai_state: AIState = AIState.IDLE
    goals: list[str] = Field(default_factory=list)
    last_reason: str = ""
    last_goal: GoalType | None = None
    goal_committed_at: int = 0
    goal_switch_count: int = 0
    goal_cooldowns: dict[GoalType, int] = Field(default_factory=dict)
    goal_scores: dict[GoalType, float] = Field(default_factory=dict)
    boredom_multipliers: dict[GoalType, float] = Field(default_factory=dict)
    consecutive_idle_ticks: int = 0

class MemoryRecord(SimulationModel):
    """A single record of a seen entity or landmark."""
    model_config = ConfigDict(extra='forbid', arbitrary_types_allowed=True)
    
    entity_id: int
    pos: Vector2
    kind: str = ""
    faction: str = ""
    last_seen_tick: int = 0
    threat_level: float = 0.0

class PerceptionMemory(SimulationModel):
    """Short-term sensory memory and threat tracking."""
    model_config = ConfigDict(extra='forbid')
    
    threat_table: dict[int, float] = Field(default_factory=dict)
    terrain_memory: dict[tuple[int, int], int] = Field(default_factory=dict)
    entity_memory: dict[int, MemoryRecord] = Field(default_factory=dict)
    memory_stale_ticks: dict[int, int] = Field(default_factory=dict)
    attention_pool: list[int] = Field(default_factory=list)
    max_attention_slots: int = 5
    hero_familiarity: dict[int, float] = Field(default_factory=dict)

class EmotionState(SimulationModel):
    """Short-term emotional spikes and long-term mood."""
    model_config = ConfigDict(extra='forbid', use_enum_values=True)
    
    # Emotional dimensions (AOA Pillar 2: Phased Appraisal)
    panic: float = Field(default=0.0, ge=0.0, le=1.0)
    stuck: float = Field(default=0.0, ge=0.0, le=1.0)
    bravery: float = Field(default=0.5, ge=0.0, le=1.0)
    
    mood: float = Field(default=0.5, ge=0.0, le=1.0)
    grudges: dict[int, float] = Field(default_factory=dict)

class NavigationState(SimulationModel):
    """Pathfinding and movement history."""
    model_config = ConfigDict(extra='forbid', arbitrary_types_allowed=True)
    
    cached_path: list[Vector2] | None = Field(default=None, repr=False)
    cached_path_target: Vector2 | None = Field(default=None, repr=False)
    pos_history: list[Vector2] = Field(default_factory=list)
    chase_ticks: int = 0
    engaged_ticks: int = 0


class NarrativeDetail(SimulationModel):
    """Base for all typed narrative event details. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')

class CombatNarrative(NarrativeDetail):
    """Details for combat-related narrative events (kills, deaths)."""
    type: Literal["combat"] = "combat"
    target_id: int
    target_kind: str
    damage_dealt: int = 0
    was_fatal: bool = False

class LootNarrative(NarrativeDetail):
    """Details for inventory/gold acquisition narrative events."""
    type: Literal["loot"] = "loot"
    item_id: str | None = None
    gold_amount: int = 0
    source: str = "" # e.g. "chest", "corpse", "node"

class DiscoveryNarrative(NarrativeDetail):
    """Details for world exploration events."""
    type: Literal["discovery"] = "discovery"
    location_id: str
    location_name: str
    rarity: str = "common"

class MemoryLogEntry(SimulationModel):
    """A single entry in the narrative memory log. [AOA STABILIZATION]
    
    Pillar 2: Rendering & Explainability. All entries must use typed details
    to ensure the API layer can reliably shape results for the UI.
    """
    model_config = ConfigDict(extra='forbid')
    
    tick: int
    type: str # e.g. "glory", "trauma", "discovery"
    impact: float = 0.0
    details: Union[CombatNarrative, LootNarrative, DiscoveryNarrative, dict[str, Any]] = Field(default_factory=dict)

class NarrativeMemory(SimulationModel):
    """Long-term history and narrative directives. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')
    
    memory_log: list[MemoryLogEntry] = Field(default_factory=list)
    life_directive: str | None = None
    memory_locations: dict[str, float] = Field(default_factory=dict)
    region_fatigue: dict[str, float] = Field(default_factory=dict)

class MindAspect(Aspect):
    """Decomposed Mind Aspect using specialized sub-models. [AOA STABILIZATION]
    
    Pillar 1: Domain-Driven Separation. Logic is split across Decision,
    Perception, Emotion, Navigation, and Narrative domains to maintain
    clear ownership lines.
    """
    model_config = ConfigDict(extra='forbid')
    
    decision: DecisionState = Field(default_factory=DecisionState)
    perception: PerceptionMemory = Field(default_factory=PerceptionMemory)
    emotion: EmotionState = Field(default_factory=EmotionState)
    navigation: NavigationState = Field(default_factory=NavigationState)
    narrative: NarrativeMemory = Field(default_factory=NarrativeMemory)
    
    bonuses: dict[str, Any] = Field(default_factory=dict)

    def total_glory(self) -> float:
        return sum(
            (e.impact if hasattr(e, "impact") else e.get("impact", 0.0))
            for e in self.narrative.memory_log
            if e.type == "glory"
        )

    def total_trauma(self) -> float:
        return sum(
            (e.impact if hasattr(e, "impact") else e.get("impact", 0.0))
            for e in self.narrative.memory_log
            if e.type == "trauma"
        )
