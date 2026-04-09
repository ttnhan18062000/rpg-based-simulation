import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
import math
from unittest.mock import MagicMock
from src.ai.goals.base import GoalScore, GoalEvaluator
from src.core.models.enums import AIState

def test_softmax_distribution():
    # If Explore=10 and Combat=1, with low Temp, Explore should almost always win.
    gs1 = GoalScore("explore", 10.0, AIState.WANDER)
    gs2 = GoalScore("combat", 1.0, AIState.HUNT)
    scores = [gs1, gs2]
    
    # At low temp (0.1), 10.0 vs 1.0 is a huge difference
    # exp(10/.1) = exp(100) vs exp(1/.1) = exp(10)
    # The ratio is e^90 which is massive.
    
    # Test rng_value = 0.99 (high end)
    selected = GoalEvaluator.select(scores, 0.99, temperature=0.1)
    assert selected.goal == "explore"

def test_softmax_with_equal_scores():
    # If scores are equal, rng_value should split 50/50
    gs1 = GoalScore("e1", 5.0, AIState.WANDER)
    gs2 = GoalScore("e2", 5.0, AIState.WANDER)
    scores = [gs1, gs2]
    
    # rng < 0.5 -> picked e1
    assert GoalEvaluator.select(scores, 0.4, temperature=1.0).goal == "e1"
    # rng > 0.5 -> picked e2
    assert GoalEvaluator.select(scores, 0.6, temperature=1.0).goal == "e2"
