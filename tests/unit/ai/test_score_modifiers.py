import pytest
from unittest.mock import MagicMock
from src.ai.goals.base import GoalScore, GoalEvaluator
from src.core.models.enums import AIState

# We anticipate these will be imported from src.ai.goals.base or similar
# For the RED phase, they will fail to import if we try to import them now.
# So I'll write the tests against the expected API.

def test_boredom_modifier_applies_multipliers():
    from src.ai.goals.base import BoredomModifier
    
    # Setup
    actor = MagicMock()
    actor.boredom_multipliers = {"combat": 0.5, "explore": 1.2}
    ctx = MagicMock()
    ctx.actor = actor
    
    modifier = BoredomModifier()
    
    # Test combat goal
    gs_combat = GoalScore("combat", 1.0, AIState.HUNT)
    modifier.modify(gs_combat, ctx)
    assert gs_combat.score == 0.5
    
    # Test explore goal
    gs_explore = GoalScore("explore", 1.0, AIState.WANDER)
    modifier.modify(gs_explore, ctx)
    assert gs_explore.score == 1.2
    
    # Test unknown goal (should remain 1.0)
    gs_rest = GoalScore("rest", 1.0, AIState.RESTING_IN_TOWN)
    modifier.modify(gs_rest, ctx)
    assert gs_rest.score == 1.0

def test_life_stage_modifier_early_bracket():
    from src.ai.goals.base import LifeStageModifier
    
    # Setup: Level 5 (Early stage <= 10)
    ctx = MagicMock()
    ctx.actor.progression.progression.level = 5
    
    modifier = LifeStageModifier()
    
    # Explore/Rest should be boosted (1.3)
    gs_explore = GoalScore("explore", 1.0, AIState.WANDER)
    modifier.modify(gs_explore, ctx)
    assert gs_explore.score == pytest.approx(1.3)
    
    # Trade/Combat should be reduced (0.8)
    gs_combat = GoalScore("combat", 1.0, AIState.HUNT)
    modifier.modify(gs_combat, ctx)
    assert gs_combat.score == pytest.approx(0.8)

def test_goal_evaluator_uses_modifiers():
    # This test verifies that GoalEvaluator.evaluate() correctly
    # applies a list of modifiers.
    
    from src.ai.goals.base import ScoreModifier
    
    class MockModifier(ScoreModifier):
        def modify(self, score: GoalScore, ctx):
            score.score *= 2.0
            
    evaluator = GoalEvaluator()
    evaluator.modifiers = [MockModifier()]
    
    # Mock context and registry
    ctx = MagicMock()
    ctx.actor.progression.progression.level = 10
    ctx.actor.boredom_multipliers = {}
    
    from src.ai.goals import base
    from src.ai.goals.base import GoalScorer
    
    class SimpleScorer(GoalScorer):
        @property
        def name(self): return "test"
        @property
        def target_state(self): return AIState.IDLE
        def score(self, ctx): return 1.0
        
    # Isolation: Temporarily replace the global registry
    original_registry = base.GOAL_REGISTRY
    base.GOAL_REGISTRY = [SimpleScorer()]
    
    try:
        results = evaluator.evaluate(ctx)
        # 1.0 (base) * 2.0 (modifier) = 2.0
        assert results[0].score == 2.0
    finally:
        base.GOAL_REGISTRY = original_registry
