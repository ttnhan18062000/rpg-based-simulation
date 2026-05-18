from __future__ import annotations
from typing import Dict
from src.core.state import LifeStage

class LifeStageService:
    """Provides utility multipliers based on life stage."""

    @staticmethod
    def get_goal_multipliers(stage: LifeStage) -> Dict[str, float]:
        """
        Returns a map of GoalKind -> multiplier.
        Base multiplier is 1.0.
        """
        multipliers = {
            LifeStage.CHILD: {
                "exploration": 1.5,
                "social": 1.2,
                "harvesting": 0.5, # Children don't like work
                "combat": 0.2,     # Children avoid combat
                "fatigue": 0.8     # High energy
            },
            LifeStage.ADULT: {
                # Neutral baseline
            },
            LifeStage.ELDER: {
                "fatigue": 1.5,    # Elders need more rest
                "combat": 0.5,     # Elders avoid physical combat
                "social": 1.3,     # Elders socialize more
                "harvesting": 0.7  # Elders work less
            }
        }
        return multipliers.get(stage, {})
