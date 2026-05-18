"""Personality Logic Service — Biases AI utility scores based on traits. [PHASE 1]

This service bridges the gap between the static PersonalityProfile (MindAspect)
and the dynamic Utility AI (GoalScorers).
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from src_legacy.core.models.enums import GoalType

if TYPE_CHECKING:
    from src_legacy.core.aspects.identity import IdentityAspect
    from src_legacy.core.entities.entity import Entity


class PersonalityLogic:
    """Service that applies personality-driven biases to goal utility."""

    @staticmethod
    def apply_motive_biases(goal_type: GoalType, base_utility: float, identity: IdentityAspect) -> float:
        """Applies multipliers to base utility based on the entity's personality profile."""
        
        # Identity no longer holds the personality fields directly; they are in MindAspect.
        # But for backward compatibility with tests/specs, we'll try to find them.
        # REGRESSION NOTE: We now expect MindAspect to be the source of truth.
        # If identity is passed, we check if it's actually an entity or has a mind reference.
        
        personality = None
        if hasattr(identity, 'personality'): # Legacy/Shim
            personality = identity.personality
        elif hasattr(identity, '_entity') and identity._entity and hasattr(identity._entity, 'mind'):
            personality = identity._entity.mind.decision.personality
        
        # If we can't find it, return base
        if not personality:
            return base_utility

        multiplier = 1.0
        
        if goal_type == GoalType.EXPLORE:
            # Curiosity biases exploration (Multiplier: 0.5)
            multiplier += personality.curiosity * 0.5
            
        elif goal_type == GoalType.COMBAT:
            # Aggression biases combat (Multiplier: 0.5)
            multiplier += personality.aggression * 0.5
            
        elif goal_type == GoalType.LOOT:
            # Greed biases looting (Multiplier: 0.5)
            multiplier += personality.greed * 0.5
            
        elif goal_type == GoalType.FLEE:
            # Neuroticism biases fleeing (Multiplier: 0.7)
            multiplier += personality.neuroticism * 0.7
            
        elif goal_type == GoalType.REST:
            # Caution biases resting (Multiplier: 0.4)
            multiplier += personality.caution * 0.4
            
        elif goal_type == GoalType.SOCIAL:
            # Loyalty biases social interaction (Multiplier: 0.4)
            multiplier += personality.loyalty * 0.4
            
        return base_utility * multiplier
