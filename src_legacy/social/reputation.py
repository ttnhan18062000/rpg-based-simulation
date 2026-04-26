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
