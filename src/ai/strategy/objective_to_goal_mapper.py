from __future__ import annotations
from typing import TYPE_CHECKING

from src.core.models.enums import GoalType
from src.core.models.strategy import ObjectiveKind

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

class ObjectiveToGoalMapper:
    """Translates strategic objectives into tactical utility biases.
    
    This implements phase_2_stage_6. It ensures the tactical GoalEvaluator
    is 'bossed' by the strategic layer's current commitments.
    """

    def get_tactical_biases(self, ctx: AIContext, objective_override: ObjectiveRecord | None = None) -> dict[GoalType, float]:
        """Calculates utility multipliers for goal types based on strategic intent."""
        biases = {gt: 1.0 for gt in GoalType}

        obj = objective_override or ctx.current_objective
        if not obj:
            # No objective? No strategic bias.
            return biases

        # Apply biases based on ObjectiveKind
        if obj.kind == ObjectiveKind.VISIT:
            # We want to get to a location. Boost related goals.
            biases[GoalType.REST] = 0.5      # Don't rest unless critical
            biases[GoalType.EXPLORE] = 2.5   # Strong boost to exploration [phase_2_stage_6]
            
        elif obj.kind == ObjectiveKind.KILL:
            # Combat focus
            biases[GoalType.COMBAT] = 2.0
            biases[GoalType.HUNT] = 2.0
            biases[GoalType.FLEE] = 0.8      # Slightly more aggressive
            
        elif obj.kind == ObjectiveKind.COLLECT or obj.kind == ObjectiveKind.INVESTIGATE:
            # Retrieval or analysis
            biases[GoalType.LOOT] = 1.8
            biases[GoalType.INVESTIGATE] = 2.0
            
        elif obj.kind == ObjectiveKind.INTERACT:
            # Social or town focus
            biases[GoalType.SOCIAL] = 2.0
            biases[GoalType.REST] = 1.2      # Towns are good for resting
            
            # [phase_2_stage_6] If this is a biological need objective, boost EAT/SLEEP
            if "needs" in obj.objective_id or "survival" in obj.project_id:
                biases[GoalType.EAT] = 5.0
                biases[GoalType.SLEEP] = 5.0
                biases[GoalType.REST] = 5.0  # Safe resting
            
        return biases
