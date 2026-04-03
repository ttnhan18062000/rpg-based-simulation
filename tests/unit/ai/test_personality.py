import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock
from src.ai.goals.base import GoalScore, GoalEvaluator
from src.core.models.enums import AIState

def test_personality_modifier_biases_explore():
    # We anticipate a PersonalityModifier class
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Openness
    ctx = MagicMock()
    ctx.actor.identity.openness = 0.9
    ctx.actor.identity.conscientiousness = 0.5
    
    modifier = PersonalityModifier()
    
    # Base explore score
    gs = GoalScore("explore", 1.0, AIState.WANDER)
    modifier.modify(gs, ctx)
    
    # High openness should boost explore (above 1.0)
    assert gs.score > 1.0

def test_personality_modifier_biases_rest():
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Conscientiousness
    ctx = MagicMock()
    ctx.actor.identity.openness = 0.5
    ctx.actor.identity.conscientiousness = 0.9
    
    modifier = PersonalityModifier()
    
    # Base rest score
    gs = GoalScore("rest", 1.0, AIState.RESTING_IN_TOWN)
    modifier.modify(gs, ctx)
    
    # High conscientiousness should boost rest/prep (above 1.0)
    assert gs.score > 1.0

def test_neuroticism_increases_flee_score():
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Neuroticism (Anxiety)
    ctx = MagicMock()
    ctx.actor.identity.neuroticism = 0.8
    
    modifier = PersonalityModifier()
    
    gs = GoalScore("flee", 1.0, AIState.FLEE)
    modifier.modify(gs, ctx)
    
    assert gs.score > 1.0
