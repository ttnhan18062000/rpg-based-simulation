from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Protocol, Dict, Any, Optional
from src.core.state import EntityState, AuthoritativeState

from src.core.strategic import GoalKind

class NeedAccess(str, Enum):
    """Whether a need goal has a way to be met within reach (SURV-06). A typed state, so the funnel counts it and no meaning sits in a reason string.

    Per-subject and per-evaluation: it says nothing about the world (the per-kind SURV-06 need-path integrity check is separate)."""

    WAY_WITHIN_REACH = "way_within_reach"
    NO_WAY_WITHIN_REACH = "no_way_within_reach"  # nothing in the world to meet the need with (e.g. no inn)
    NO_AFFORDABLE_WAY = "no_affordable_way"  # a way exists but the subject cannot pay for it (AGENCY-03: not an actionable affordance)


@dataclass(frozen=True)
class GoalScore:
    kind: GoalKind | str
    utility: float
    target_id: Optional[str] = None
    target_pos: Optional[tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Set only by a scorer whose goal is about a specific moving entity; copied into
    # ObjectiveState.target_entity_id at objective creation.
    target_entity_id: Optional[int] = None
    # Set by need goals (hunger): whether a way to meet the need is within reach for this subject.
    need_access: Optional[NeedAccess] = None

class GoalScorer(Protocol):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        """Calculate the utility of a goal kind for the given entity."""
        ...

class GoalRegistry:
    _scorers: Dict[str, GoalScorer] = {}
    _sorted_keys: Optional[List[str]] = None

    @classmethod
    def register(cls, kind: GoalKind | str, scorer: GoalScorer):
        """
        Registers a scorer for a specific goal kind.
        Logic ID: RPG-GOAL-001
        """
        # Validate that the kind is a valid GoalKind
        try:
            valid_kind = GoalKind(kind)
        except ValueError:
            raise ValueError(f"Invalid goal kind '{kind}'. Must be a valid GoalKind enum or value.")

        if valid_kind in cls._scorers:
            existing = cls._scorers[valid_kind]
            if existing.__class__ != scorer.__class__:
                raise ValueError(f"GoalRegistry conflict: kind '{valid_kind}' already registered to {existing.__class__}")
            return
        cls._scorers[valid_kind] = scorer
        cls._sorted_keys = None

    @classmethod
    def get_all_scores(cls, entity: EntityState, state: AuthoritativeState) -> List[GoalScore]:
        # Return sorted by key to ensure deterministic order across ticks
        if cls._sorted_keys is None or len(cls._sorted_keys) != len(cls._scorers) or any(k not in cls._scorers for k in cls._sorted_keys):
            cls._sorted_keys = sorted(cls._scorers.keys())
        return [cls._scorers[k].score(entity, state) for k in cls._sorted_keys]

