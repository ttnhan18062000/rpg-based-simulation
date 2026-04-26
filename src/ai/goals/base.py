from __future__ import annotations
from dataclasses import dataclass
from typing import List, Protocol, Dict, Any, Optional
from src.core.state import EntityState, AuthoritativeState

@dataclass(frozen=True)
class GoalScore:
    kind: str
    utility: float
    target_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class GoalScorer(Protocol):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        """Calculate the utility of a goal kind for the given entity."""
        ...

class GoalRegistry:
    _scorers: List[GoalScorer] = []

    @classmethod
    def register(cls, scorer: GoalScorer):
        cls._scorers.append(scorer)

    @classmethod
    def get_all_scores(cls, entity: EntityState, state: AuthoritativeState) -> List[GoalScore]:
        return [scorer.score(entity, state) for scorer in cls._scorers]
