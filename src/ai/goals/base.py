"""Base classes for the Goal scoring plugin system.

GoalScorer   — Abstract base class; subclass and implement `score()`.
GoalScore    — A (goal_name, score, target_state) tuple for selection.
GoalEvaluator— Iterates registered scorers, filters, sorts, selects.
GOAL_REGISTRY— Module-level list where scorers are registered.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.enums import AIState

if TYPE_CHECKING:
    from src.ai.states import AIContext


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class GoalScore:
    """A scored goal ready for selection."""
    goal: str
    score: float
    target_state: AIState


# ---------------------------------------------------------------------------
# Abstract scorer
# ---------------------------------------------------------------------------

class GoalScorer(ABC):
    """Base class for all goal scorers.

    Subclass this and implement:
      - name:         unique goal identifier string
      - target_state: AIState the entity transitions to if this goal wins
      - score(ctx):   return a float utility score (<=0 means non-viable)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique goal identifier (e.g. 'combat', 'flee')."""

    @property
    @abstractmethod
    def target_state(self) -> AIState:
        """AIState to transition to when this goal is selected."""

    @abstractmethod
    def score(self, ctx: AIContext) -> float:
        """Score this goal for the given entity context.

        Returns a float where higher = more desirable.
        Scores <= 0.0 are filtered out as non-viable.
        """

    def evaluate(self, ctx: AIContext) -> GoalScore:
        """Convenience: score and wrap into GoalScore."""
        return GoalScore(
            goal=self.name,
            score=self.score(ctx),
            target_state=self.target_state,
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GOAL_REGISTRY: list[GoalScorer] = []


def register_goal(scorer: GoalScorer) -> GoalScorer:
    """Register a GoalScorer instance in the global registry."""
    GOAL_REGISTRY.append(scorer)
    return scorer


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class GoalEvaluator:
    """Scores all registered goals and selects one via weighted random.

    Usage::

        evaluator = GoalEvaluator()
        scores = evaluator.evaluate(ctx)
        goal = evaluator.select(scores, rng_value)
    """

    def evaluate(self, ctx: AIContext) -> list[GoalScore]:
        """Score all registered goals, filter non-viable, sort descending."""
        scores = [scorer.evaluate(ctx) for scorer in GOAL_REGISTRY]
        scores = [s for s in scores if s.score > 0.0]
        scores.sort(key=lambda g: g.score, reverse=True)
        return scores

    @staticmethod
    def select(
        scores: list[GoalScore],
        rng_value: float,
        top_n: int = 3,
    ) -> GoalScore | None:
        """Select a goal via weighted random from top N candidates.

        Args:
            scores: Sorted list of GoalScore (descending).
            rng_value: Random float [0, 1) for selection.
            top_n: How many top goals to consider.

        Returns:
            Selected GoalScore, or None if no viable goals.
        """
        if not scores:
            return None

        candidates = scores[:top_n]

        # Normalize scores to weights (shift so minimum is 0.1)
        min_score = min(c.score for c in candidates)
        weights = [max(c.score - min_score + 0.1, 0.1) for c in candidates]
        total = sum(weights)

        # Weighted selection
        target = rng_value * total
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if target <= cumulative:
                return candidates[i]

        return candidates[-1]
