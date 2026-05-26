from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Protocol, Dict, Any, Optional
from src.core.state import EntityState, AuthoritativeState

from src.core.strategic import GoalKind

@dataclass(frozen=True)
class GoalScore:
    kind: GoalKind | str
    utility: float
    target_id: Optional[str] = None
    target_pos: Optional[tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

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

