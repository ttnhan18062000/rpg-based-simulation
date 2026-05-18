import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock
from src_legacy.ai.goals.base import GoalScore, GoalEvaluator, MotiveModifier
from src_legacy.core.models.enums import AIState, GoalType

def test_motive_modifier_biases_explore():
    # Setup: High Curiosity motive (using appraisal result)
    ctx = MagicMock()
    ctx.actor.mind.decision.motive_utility_biases = {GoalType.EXPLORE: 1.4}
    
    modifier = MotiveModifier()
    
    # Base explore score
    gs = GoalScore(GoalType.EXPLORE, 1.0, AIState.WANDER)
    modifier.modify(gs, ctx)
    
    # Should apply the pre-calculated bias
    assert gs.score == pytest.approx(1.4)

def test_motive_modifier_biases_rest():
    # Setup: High Rest motive
    ctx = MagicMock()
    ctx.actor.mind.decision.motive_utility_biases = {GoalType.REST: 1.4}
    
    modifier = MotiveModifier()
    
    # Base rest score
    gs = GoalScore(GoalType.REST, 1.0, AIState.RESTING_IN_TOWN)
    modifier.modify(gs, ctx)
    
    # Should apply the pre-calculated bias
    assert gs.score == pytest.approx(1.4)

def test_motive_modifier_biases_flee():
    # Setup: High Safety motive
    ctx = MagicMock()
    ctx.actor.mind.decision.motive_utility_biases = {GoalType.FLEE: 1.3}
    
    modifier = MotiveModifier()
    
    gs = GoalScore(GoalType.FLEE, 1.0, AIState.FLEE)
    modifier.modify(gs, ctx)
    
    assert gs.score == pytest.approx(1.3)
