from __future__ import annotations
from typing import Dict, Any

class ReputationService:
    """
    Handles public standing and witnessed behavior consequences.
    """
    
    IMPACTS = {
        "THEFT": -0.2,
        "MURDER": -1.0,
        "BETRAYAL": -0.5,
        "HEROISM": 0.2,
        "GENEROSITY": 0.1,
    }

    @staticmethod
    def get_impact(action_kind: str) -> float:
        return ReputationService.IMPACTS.get(action_kind, 0.0)

    @staticmethod
    def calculate_caution_modifier(reputation: float) -> float:
        """
        Low reputation increases caution in others (defensive posture).
        Formula: 1.0 + max(0, (1.0 - reputation) * 0.5)
        Rep 1.0 -> 1.0
        Rep 0.0 -> 1.5 (50% more cautious)
        """
        return 1.0 + max(0.0, (1.0 - reputation) * 0.5)

    @staticmethod
    def combine_public_reputation(parent_a: float, parent_b: float) -> float:
        """
        Idea 53 birth-seed: a newborn's public_reputation starts as a "starting echo" of
        its parents' averaged standing -- not a full inheritance -- which is then swamped
        by the child's own subsequent heroism_delta/notoriety_delta play. Simple arithmetic
        mean, clamped to public_reputation's authoritative [0.0, 2.0] range (matching
        RelationshipService.process_update()'s own clamp) as defense-in-depth.
        """
        return max(0.0, min(2.0, (parent_a + parent_b) / 2.0))
