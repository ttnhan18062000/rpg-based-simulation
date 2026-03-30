from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import BaseModel, Field
from src.core.models.base import Aspect
from src.core.models.enums import AIState

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class DecisionState(BaseModel):
    """Internal state for AI goal selection and commitment."""
    ai_state: AIState = AIState.IDLE
    goals: list[str] = Field(default_factory=list)
    last_reason: str = ""
    last_goal: str | None = None
    goal_committed_at: int = 0
    goal_switch_count: int = 0
    goal_cooldowns: dict[str, int] = Field(default_factory=dict)
    goal_scores: dict[str, float] = Field(default_factory=dict)
    boredom_multipliers: dict[str, float] = Field(default_factory=dict)
    consecutive_idle_ticks: int = 0

class PerceptionMemory(BaseModel):
    """Short-term sensory memory and threat tracking."""
    threat_table: dict[int, float] = Field(default_factory=dict)
    terrain_memory: dict[tuple[int, int], int] = Field(default_factory=dict)
    # Refactored: dict for faster lookups (entity_id -> Vector2 or detail dict)
    entity_memory: dict[int, Any] = Field(default_factory=dict)
    memory_stale_ticks: dict[int, int] = Field(default_factory=dict)
    attention_pool: list[int] = Field(default_factory=list)
    max_attention_slots: int = 5
    hero_familiarity: dict[int, float] = Field(default_factory=dict)

class EmotionState(BaseModel):
    """Short-term emotional spikes and long-term mood."""
    emotional_state: dict[str, float] = Field(default_factory=dict)
    mood: float = 0.5
    grudges: dict[int, float] = Field(default_factory=dict)

class NavigationState(BaseModel):
    """Pathfinding and movement history."""
    cached_path: list[Any] | None = Field(default=None, repr=False)
    cached_path_target: Any | None = Field(default=None, repr=False)
    pos_history: list[Any] = Field(default_factory=list)
    chase_ticks: int = 0
    engaged_ticks: int = 0

class NarrativeMemory(BaseModel):
    """Long-term history and narrative directives."""
    memory_log: list[dict[str, Any]] = Field(default_factory=list)
    life_directive: str | None = None
    memory_locations: dict[str, float] = Field(default_factory=dict)
    region_fatigue: dict[str, float] = Field(default_factory=dict)

class MindAspect(Aspect):
    """Decomposed Mind Aspect using specialized sub-models."""
    
    decision: DecisionState = Field(default_factory=DecisionState)
    perception: PerceptionMemory = Field(default_factory=PerceptionMemory)
    emotion: EmotionState = Field(default_factory=EmotionState)
    navigation: NavigationState = Field(default_factory=NavigationState)
    narrative: NarrativeMemory = Field(default_factory=NarrativeMemory)
    
    bonuses: dict[str, Any] = Field(default_factory=dict)

    def total_glory(self) -> float:
        return sum(e.get("impact", 0.0) for e in self.narrative.memory_log if e.get("impact", 0.0) > 0)

    def total_trauma(self) -> float:
        return sum(e.get("impact", 0.0) for e in self.narrative.memory_log if e.get("impact", 0.0) < 0)

    def prune_memories(self, max_entries: int = 50) -> None:
        log = self.narrative.memory_log
        if len(log) <= max_entries:
            return
        log.sort(key=lambda e: abs(float(e.get("impact", 0.0))), reverse=True)
        self.narrative.memory_log = log[:max_entries]
