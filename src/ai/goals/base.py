from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Protocol, Dict, Any, Optional
from src.core.state import EntityState, AuthoritativeState

@dataclass(frozen=True)
class GoalScore:
    kind: str
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

    @classmethod
    def register(cls, kind: str, scorer: GoalScorer):
        """
        Registers a scorer for a specific goal kind.
        Logic ID: RPG-GOAL-001
        """
        if kind in cls._scorers:
            existing = cls._scorers[kind]
            if existing.__class__ != scorer.__class__:
                raise ValueError(f"GoalRegistry conflict: kind '{kind}' already registered to {existing.__class__}")
            return
        cls._scorers[kind] = scorer

    @classmethod
    def get_all_scores(cls, entity: EntityState, state: AuthoritativeState) -> List[GoalScore]:
        # Return sorted by key to ensure deterministic order across ticks
        sorted_keys = sorted(cls._scorers.keys())
        return [cls._scorers[k].score(entity, state) for k in sorted_keys]
