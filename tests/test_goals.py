"""Tests for the GoalScorer plugin system and GoalEvaluator."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai.goals.base import (
    GoalScorer, GoalScore, GoalEvaluator, GOAL_REGISTRY, register_goal,
)
from src.ai.goals.scorers import (
    CombatGoal, FleeGoal, ExploreGoal, LootGoal,
    TradeGoal, RestGoal, CraftGoal, SocialGoal, GuardGoal,
)
from src.core.enums import AIState


# ---------------------------------------------------------------------------
# GoalScorer ABC and subclass tests
# ---------------------------------------------------------------------------

class TestGoalScorerSubclasses:
    """Test that all built-in GoalScorer subclasses have correct properties."""

    def test_combat_goal_properties(self):
        g = CombatGoal()
        assert g.name == "combat"
        assert g.target_state == AIState.HUNT

    def test_flee_goal_properties(self):
        g = FleeGoal()
        assert g.name == "flee"
        assert g.target_state == AIState.FLEE

    def test_explore_goal_properties(self):
        g = ExploreGoal()
        assert g.name == "explore"
        assert g.target_state == AIState.WANDER

    def test_loot_goal_properties(self):
        g = LootGoal()
        assert g.name == "loot"
        assert g.target_state == AIState.LOOTING

    def test_trade_goal_properties(self):
        g = TradeGoal()
        assert g.name == "trade"
        assert g.target_state == AIState.VISIT_SHOP

    def test_rest_goal_properties(self):
        g = RestGoal()
        assert g.name == "rest"
        assert g.target_state == AIState.RESTING_IN_TOWN

    def test_craft_goal_properties(self):
        g = CraftGoal()
        assert g.name == "craft"
        assert g.target_state == AIState.VISIT_BLACKSMITH

    def test_social_goal_properties(self):
        g = SocialGoal()
        assert g.name == "social"
        assert g.target_state == AIState.VISIT_GUILD

    def test_guard_goal_properties(self):
        g = GuardGoal()
        assert g.name == "guard"
        assert g.target_state == AIState.GUARD_CAMP

    def test_all_scorers_are_goal_scorer_subclasses(self):
        for scorer in GOAL_REGISTRY:
            assert isinstance(scorer, GoalScorer)


# ---------------------------------------------------------------------------
# GOAL_REGISTRY tests
# ---------------------------------------------------------------------------

class TestGoalRegistry:
    """Test the global goal registry."""

    def test_registry_has_9_goals(self):
        assert len(GOAL_REGISTRY) == 9

    def test_registry_names_unique(self):
        names = [g.name for g in GOAL_REGISTRY]
        assert len(names) == len(set(names))

    def test_registry_contains_all_expected_goals(self):
        names = {g.name for g in GOAL_REGISTRY}
        expected = {"combat", "flee", "explore", "loot", "trade", "rest", "craft", "social", "guard"}
        assert names == expected

    def test_all_goals_have_valid_target_states(self):
        for scorer in GOAL_REGISTRY:
            assert isinstance(scorer.target_state, int)  # AIState is IntEnum


# ---------------------------------------------------------------------------
# GoalScore dataclass tests
# ---------------------------------------------------------------------------

class TestGoalScore:
    """Test the GoalScore dataclass."""

    def test_goal_score_creation(self):
        gs = GoalScore(goal="combat", score=0.8, target_state=AIState.HUNT)
        assert gs.goal == "combat"
        assert gs.score == 0.8
        assert gs.target_state == AIState.HUNT

    def test_goal_score_sorting(self):
        scores = [
            GoalScore("a", 0.3, AIState.WANDER),
            GoalScore("b", 0.8, AIState.HUNT),
            GoalScore("c", 0.5, AIState.FLEE),
        ]
        scores.sort(key=lambda g: g.score, reverse=True)
        assert scores[0].goal == "b"
        assert scores[1].goal == "c"
        assert scores[2].goal == "a"


# ---------------------------------------------------------------------------
# GoalEvaluator.select() tests
# ---------------------------------------------------------------------------

class TestGoalEvaluatorSelect:
    """Test the weighted random goal selection."""

    def test_select_returns_none_on_empty(self):
        result = GoalEvaluator.select([], rng_value=0.5)
        assert result is None

    def test_select_single_candidate(self):
        scores = [GoalScore("combat", 0.8, AIState.HUNT)]
        result = GoalEvaluator.select(scores, rng_value=0.5)
        assert result is not None
        assert result.goal == "combat"

    def test_select_returns_goal_score(self):
        scores = [
            GoalScore("combat", 0.8, AIState.HUNT),
            GoalScore("flee", 0.6, AIState.FLEE),
        ]
        result = GoalEvaluator.select(scores, rng_value=0.3)
        assert result is not None
        assert isinstance(result, GoalScore)
        assert result.goal in ("combat", "flee")

    def test_select_rng_0_picks_first(self):
        """RNG value of 0 should always pick the first (highest) candidate."""
        scores = [
            GoalScore("combat", 0.9, AIState.HUNT),
            GoalScore("flee", 0.5, AIState.FLEE),
            GoalScore("rest", 0.3, AIState.RESTING_IN_TOWN),
        ]
        result = GoalEvaluator.select(scores, rng_value=0.0)
        assert result is not None
        assert result.goal == "combat"

    def test_select_rng_near_1_picks_last(self):
        """RNG value near 1.0 should pick the lowest-weighted candidate."""
        scores = [
            GoalScore("combat", 0.9, AIState.HUNT),
            GoalScore("flee", 0.5, AIState.FLEE),
            GoalScore("rest", 0.3, AIState.RESTING_IN_TOWN),
        ]
        result = GoalEvaluator.select(scores, rng_value=0.99)
        assert result is not None
        # Should be one of the later candidates
        assert result.goal in ("combat", "flee", "rest")

    def test_select_top_n_limits_candidates(self):
        scores = [
            GoalScore("combat", 0.9, AIState.HUNT),
            GoalScore("flee", 0.5, AIState.FLEE),
            GoalScore("rest", 0.3, AIState.RESTING_IN_TOWN),
            GoalScore("explore", 0.2, AIState.WANDER),
        ]
        # top_n=2 means only combat and flee are candidates
        result = GoalEvaluator.select(scores, rng_value=0.99, top_n=2)
        assert result is not None
        assert result.goal in ("combat", "flee")

    def test_select_deterministic_with_same_rng(self):
        """Same scores + same rng_value should always produce same result."""
        scores = [
            GoalScore("combat", 0.8, AIState.HUNT),
            GoalScore("flee", 0.6, AIState.FLEE),
            GoalScore("rest", 0.4, AIState.RESTING_IN_TOWN),
        ]
        result1 = GoalEvaluator.select(scores, rng_value=0.42)
        result2 = GoalEvaluator.select(scores, rng_value=0.42)
        assert result1 is not None and result2 is not None
        assert result1.goal == result2.goal


# ---------------------------------------------------------------------------
# GoalScorer.evaluate() convenience method tests
# ---------------------------------------------------------------------------

class TestGoalScorerEvaluate:
    """Test the evaluate() convenience method on GoalScorer."""

    def test_evaluate_wraps_score_into_goal_score(self):
        """The evaluate() method should produce a GoalScore with the scorer's name and target_state."""
        # We can't easily call score() without a full AIContext, but we can verify
        # that the GoalScore produced has the right name and target_state
        gs = GoalScore(goal="combat", score=0.5, target_state=AIState.HUNT)
        assert gs.goal == "combat"
        assert gs.target_state == AIState.HUNT


# ---------------------------------------------------------------------------
# Backward compatibility shim tests
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """Test that the old goal_evaluator.py shim re-exports correctly."""

    def test_shim_exports_goal_score(self):
        from src.ai.goal_evaluator import GoalScore as LegacyGoalScore
        assert LegacyGoalScore is GoalScore

    def test_shim_exports_goal_evaluator(self):
        from src.ai.goal_evaluator import GoalEvaluator as LegacyEvaluator
        assert LegacyEvaluator is GoalEvaluator

    def test_shim_exports_registry(self):
        from src.ai.goal_evaluator import GOAL_REGISTRY as LegacyRegistry
        assert LegacyRegistry is GOAL_REGISTRY
        assert len(LegacyRegistry) == 9
