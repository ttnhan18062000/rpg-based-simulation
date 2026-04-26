"""
Narrative Memory System.

Persists turning points and biases future behavior.

Covers:
- LEG-RPG-151: Narrative memory logging
- Part 1 §Social: Turning points feed future strategic and social behavior
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from src.core.state import EntityState
from src.systems.social import TurningPoint


@dataclass(frozen=True, slots=True)
class NarrativeMemory:
    """Persistent collection of turning points for an entity."""
    turning_points: List[TurningPoint] = field(default_factory=list)
    trauma_score: float = 0.0   # Accumulated trauma
    confidence: float = 0.5     # From victories and successes


class NarrativeMemorySystem:
    """
    Pure decision logic for narrative memory management.
    Does NOT mutate state directly.
    """

    @staticmethod
    def record_turning_point(
        memory: NarrativeMemory,
        turning_point: TurningPoint
    ) -> NarrativeMemory:
        """
        LEG-RPG-151: Turning points persist in narrative memory.
        """
        new_points = list(memory.turning_points) + [turning_point]

        # Update aggregate scores
        new_trauma = memory.trauma_score
        new_confidence = memory.confidence

        if turning_point.kind in ("betrayal", "near_death", "loss"):
            new_trauma = min(1.0, new_trauma + turning_point.salience * 0.2)
        elif turning_point.kind in ("great_victory", "first_kill"):
            new_confidence = min(1.0, new_confidence + turning_point.salience * 0.15)

        return NarrativeMemory(
            turning_points=new_points,
            trauma_score=new_trauma,
            confidence=new_confidence
        )

    @staticmethod
    def compute_utility_bias(
        memory: NarrativeMemory,
        goal_kind: str
    ) -> float:
        """
        LEG-RPG-151: Narrative memory biases future utility scoring.

        Returns a multiplier for a given goal type.
        Trauma increases FLEE bias, decreases EXPLORE bias.
        Confidence increases ATTACK bias, decreases REST bias.
        """
        bias = 1.0

        if goal_kind == "FLEE":
            bias += memory.trauma_score * 0.5
        elif goal_kind == "EXPLORE":
            bias -= memory.trauma_score * 0.3
        elif goal_kind == "ATTACK":
            bias += memory.confidence * 0.3
        elif goal_kind == "REST":
            bias -= memory.confidence * 0.2

        return max(0.1, bias)

    @staticmethod
    def has_trauma_with(memory: NarrativeMemory, subject_id: int) -> bool:
        """Check if entity has betrayal/negative turning point with a specific subject."""
        for tp in memory.turning_points:
            if tp.subject_id == subject_id and tp.kind in ("betrayal", "loss"):
                return True
        return False

    @staticmethod
    def get_region_trauma(memory: NarrativeMemory, region_id: str) -> float:
        """Aggregate trauma from turning points in a specific region."""
        score = 0.0
        for tp in memory.turning_points:
            # Use subject_id as string for region tracking
            if str(tp.subject_id) == region_id and tp.kind in ("near_death", "loss"):
                score += tp.salience * 0.1
        return min(1.0, score)
