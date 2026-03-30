"""Base action proposal — the universal currency between AI and World."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.models.enums import ActionType


@dataclass(frozen=True, slots=True)
class ActionProposal:
    """An intent produced by a worker thread.

    The WorldLoop validates and applies (or rejects) each proposal.
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
        return f"Proposal(entity={self.actor_id}, {self.verb.name}{meta_str}, target={self.target}, reason={self.reason!r})"

@dataclass(frozen=True, slots=True)
class IntentUpdate:
    """Base for all typed simulation side-effects."""
    pass

@dataclass(frozen=True, slots=True)
class MindUpdate(IntentUpdate):
    """Updates to the entity's Decision, Perception, or Emotion state."""
    goal_scores: dict[str, float] | None = None
    last_goal: str | None = None
    boredom_delta: dict[str, float] | None = None
    new_ai_state: int | None = None

@dataclass(frozen=True, slots=True)
class NavigationUpdate(IntentUpdate):
    """Updates to pathfinding memory and history."""
    pos_history: list[tuple[int, int]] | None = None
    cached_path: list[tuple[int, int]] | None = None
    target_pos: Any | None = None # Vector2

@dataclass(frozen=True, slots=True)
class CombatTraceUpdate(IntentUpdate):
    """Rich trace data for introspection."""
    tick: int
    attacker_id: int
    defender_id: int
    damage: int
    is_crit: bool
    is_evasion: bool
    skill_used: str = "attack"
    details: dict[str, Any] = field(default_factory=dict)
