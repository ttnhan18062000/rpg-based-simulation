"""
src/domains/perception/salience.py
───────────────────────────────────────────────────────────────────────────────
Phase 12 — SignalSalienceEvaluator

Ranks world signals by dynamic relevance, distance penalty, and emotional weights.
"""

from __future__ import annotations
import math
from typing import Dict, Any, Tuple
from src.core.state import EntityState

class WorldSignal:
    """Represents a candidate raw signal emitted by a world object."""
    def __init__(
        self,
        signal_id: str,
        kind: str,
        position: Tuple[float, float],
        base_relevance: float,
        danger_level: float = 0.0,
        is_novel: bool = False
    ) -> None:
        self.signal_id = signal_id
        self.kind = kind
        self.position = position
        self.base_relevance = base_relevance
        self.danger_level = danger_level
        self.is_novel = is_novel


class SignalSalienceEvaluator:
    """Calculates dynamic subjective salience for a candidate signal."""

    @staticmethod
    def evaluate(entity: EntityState, signal: WorldSignal, attention_focus: Tuple[str, ...]) -> float:
        # 1. Base relevance
        salience = signal.base_relevance

        # 2. Attention Focus bonus (+0.3 if the signal kind matches one of the attention tags)
        if signal.kind in attention_focus:
            salience += 0.3

        # 3. Danger level scaling (fear boosts threat salience)
        if signal.danger_level > 0.0:
            fear = entity.cognition.subjective.emotion.fear
            salience += signal.danger_level * (1.0 + fear)

        # 4. Curiosity bonus for novel signals
        if signal.is_novel:
            curiosity = entity.cognition.subjective.emotion.curiosity
            salience += 0.2 * (1.0 + curiosity)

        # 5. Distance penalty
        entity_pos = entity.navigation.position
        dx = signal.position[0] - entity_pos[0]
        dy = signal.position[1] - entity_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Penalize salience by distance (0.01 per distance unit)
        salience -= dist * 0.01

        # Clamping salience to non-negative range
        return max(0.0, salience)
