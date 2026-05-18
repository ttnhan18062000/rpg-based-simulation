from __future__ import annotations
from typing import List
from src_legacy.ai.goals.base import GoalScore
from src_legacy.core.state import EntityState, AuthoritativeState
from src_legacy.ai.personality import PersonalityService
from src_legacy.ai.life_stage import LifeStageService

class ScoreModifierSystem:
    """Orchestrates all goal utility modifiers."""

    @staticmethod
    def apply_modifiers(
        entity: EntityState, 
        state: AuthoritativeState, 
        scores: List[GoalScore]
    ) -> List[GoalScore]:
        """
        Applies personality, life stage, and boredom modifiers to goal scores.
        """
        modified_scores = []
        
        # 1. Get modifiers from services
        personality_mods = PersonalityService.get_goal_modifiers(entity.identity.personality)
        life_stage_mults = LifeStageService.get_goal_multipliers(entity.identity.life_stage)
        boredom = entity.strategic.boredom
        
        for score in scores:
            utility = score.utility
            
            # 1. Personality Bias: base * (1.0 + bias)
            bias = personality_mods.get(score.kind, 0.0)
            utility *= (1.0 + bias)
            
            # 2. Life Stage Multiplier
            mult = life_stage_mults.get(score.kind, 1.0)
            utility *= mult
            
            # 3. Boredom Tax: utility - boredom
            # Boredom value is accumulated score of repeated activity
            # Penalty weight: 0.5 per boredom unit
            boredom_score = boredom.get(score.kind, 0.0)
            utility -= (boredom_score * 0.5)
            
            # Ensure utility doesn't go below absolute minimum for critical needs
            if score.kind in ("fatigue", "hunger"):
                 utility = max(utility, score.utility * 0.2) # Needs always have some floor
            else:
                 utility = max(0.0, utility)
            
            from dataclasses import replace
            modified_scores.append(replace(score, utility=utility))
            
        return modified_scores
