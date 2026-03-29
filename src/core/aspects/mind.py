from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import AIState

class MindAspect(Aspect):
    """Aspect handling AI state, memory, goals, and threat/aggro."""
    ai_state: AIState = AIState.IDLE
    goals: list[str] = Field(default_factory=list)
    memory: dict[int, Any] = Field(default_factory=dict)
    threat_table: dict[int, float] = Field(default_factory=dict)
    last_reason: str = ""
    
    # Sensory Memory
    terrain_memory: dict[tuple[int, int], int] = Field(default_factory=dict)
    entity_memory: list[dict] = Field(default_factory=list)
    memory_log: list[dict[str, Any]] = Field(default_factory=list) # Narrative log: (tick, type, desc, impact)
    
    # Engagement and paths
    engaged_ticks: int = 0
    cached_path: list[Any] | None = Field(default=None, repr=False)
    cached_path_target: Any | None = Field(default=None, repr=False)
    
    consecutive_idle_ticks: int = 0
    chase_ticks: int = 0
    # Cognitive Pipeline: Selective Attention
    last_goal: str | None = None
    pos_history: list[Any] = Field(default_factory=list)
    attention_pool: list[int] = Field(default_factory=list)
    max_attention_slots: int = 5
    hero_familiarity: dict[int, float] = Field(default_factory=dict)
    
    # Emotional States & Personality (short-term & long-term)
    emotional_state: dict[str, float] = Field(default_factory=dict)
    mood: float = 0.5  # 0.0 (despair/fear) to 1.0 (confidence/fury)
    
    # Nemesis & Memory
    grudges: dict[int, float] = Field(default_factory=dict) # entity_id -> grudge level
    memory_locations: dict[str, float] = Field(default_factory=dict) # region_id -> sentiment (-1.0 to 1.0)
    region_fatigue: dict[str, float] = Field(default_factory=dict) # region_id -> fatigue penalty (0.0 to 1.0)
    
    # Ambition & Directives
    life_directive: str | None = None # e.g. "DRAGON_SLAYER", "CRAFTER"
    
    # Action Styles (Stances)
    action_style: str = "balanced"
    
    # Hysteresis & Loop Prevention
    boredom_multipliers: dict[str, float] = Field(default_factory=dict)
    goal_committed_at: int = 0  # tick when current goal was committed
    goal_cooldowns: dict[str, int] = Field(default_factory=dict)  # goal→expiry tick
    goal_switch_count: int = 0  # diagnostic counter
    bonuses: dict[str, Any] = Field(default_factory=dict)

    # --- Narrative Memory Helpers ---

    def total_glory(self) -> float:
        """Sum of all positive-impact memory entries."""
        return sum(
            e.get("impact", 0.0)
            for e in self.memory_log
            if e.get("impact", 0.0) > 0
        )

    def total_trauma(self) -> float:
        """Sum of all negative-impact memory entries (returns negative value)."""
        return sum(
            e.get("impact", 0.0)
            for e in self.memory_log
            if e.get("impact", 0.0) < 0
        )

    def prune_memories(self, max_entries: int = 50) -> None:
        """Keep only the top *max_entries* memories by absolute impact."""
        if len(self.memory_log) <= max_entries:
            return
        self.memory_log.sort(key=lambda e: abs(float(e.get("impact", 0.0))), reverse=True)
        self.memory_log = self.memory_log[:max_entries]

    def get_emotional_modifier(self, emotion: str) -> float:
        """Return a weight multiplier derived from internal emotional state.
        
        Default neutral is 1.0.
        """
        val = self.emotional_state.get(emotion, 0.0)
        # Hysteresis and mood influence
        if emotion == "panic":
            return 1.0 + (val * 1.5) # Up to 2.5x weight for Fleeing
        if emotion == "boredom":
            # Boredom is tracked per goal in boredom_multipliers, but this is a general factor
            return 1.0 - (val * 0.5)
        if emotion == "stuck":
            return val * 5.0 # Massive boost to "Get Unstuck" goals
        return 1.0
