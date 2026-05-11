# Compliance IDs: COMB-093, COMB-094, COMB-095, COMB-096, COMB-097, COMB-098, COMB-099
from __future__ import annotations
from typing import List
from src.ai.goals.base import GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.ai.personality import PersonalityService
from src.ai.life_stage import LifeStageService

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
        
        from src.systems.learning import StrategicLearningService
        tp_biases = StrategicLearningService.get_goal_biases(entity.strategic.turning_points)
        
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
            
            # 4. Strategic Learning Bias: utility + tp_bias
            tp_bias = tp_biases.get(score.kind, 0.0)
            utility += tp_bias
            
            # 5. Blocker Suppression (Phase 6)
            # If any blocker exists for this goal kind, apply heavy penalty
            for blocker in entity.strategic.blockers.values():
                 if not blocker.resolved and blocker.subject == score.kind:
                      utility *= (1.0 - blocker.severity)
                 elif not blocker.resolved and blocker.kind == "access" and score.target_id == blocker.subject:
                      # If target ID is specifically blocked
                      utility *= 0.1
            
            # Ensure utility doesn't go below absolute minimum for critical needs
            if score.kind in ("fatigue", "hunger"):
                 utility = max(utility, score.utility * 0.2) # Needs always have some floor
            else:
                 utility = max(0.0, utility)
            
            from dataclasses import replace
            modified_scores.append(replace(score, utility=utility))
            
        return modified_scores
