import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock
from src.ai.goals.base import GoalScore, GoalEvaluator
from src.core.models.enums import AIState, GoalType

def test_personality_modifier_biases_explore():
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Openness
    ctx = MagicMock()
    ctx.actor.identity.openness = 0.9
    ctx.actor.identity.conscientiousness = 0.5
    
    modifier = PersonalityModifier()
    
    # Base explore score
    gs = GoalScore(GoalType.EXPLORE, 1.0, AIState.WANDER)
    modifier.modify(gs, ctx)
    
    # High openness should boost explore (above 1.0)
    # 0.5 + 0.9 = 1.4
    assert gs.score == pytest.approx(1.4)

def test_personality_modifier_biases_rest():
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Conscientiousness
    ctx = MagicMock()
    ctx.actor.identity.openness = 0.5
    ctx.actor.identity.conscientiousness = 0.9
    
    modifier = PersonalityModifier()
    
    # Base rest score
    gs = GoalScore(GoalType.REST, 1.0, AIState.RESTING_IN_TOWN)
    modifier.modify(gs, ctx)
    
    # High conscientiousness should boost rest/prep (above 1.0)
    # 0.5 + 0.9 = 1.4
    assert gs.score == pytest.approx(1.4)

def test_neuroticism_increases_flee_score():
    from src.ai.goals.base import PersonalityModifier
    
    # Setup: High Neuroticism (Anxiety)
    ctx = MagicMock()
    ctx.actor.identity.neuroticism = 0.8
    
    modifier = PersonalityModifier()
    
    gs = GoalScore(GoalType.FLEE, 1.0, AIState.FLEE)
    modifier.modify(gs, ctx)
    
    # 0.5 + 0.8 = 1.3
    assert gs.score == pytest.approx(1.3)
