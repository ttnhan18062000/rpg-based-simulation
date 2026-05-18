import os
import sys
from unittest.mock import MagicMock
import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src_legacy.ai.brain import AIBrain, AIContext
from src_legacy.ai.goals.base import (
    GoalScorer, GoalScore, GoalEvaluator, GOAL_REGISTRY, register_goal,
)
from src_legacy.ai.goals.scorers import (
    CombatGoal, FleeGoal, ExploreGoal, LootGoal,
    TradeGoal, RestGoal, CraftGoal, SocialGoal, GuardGoal,
)
from src_legacy.core.entities.entity import Entity, Vector2
from src_legacy.core.models.enums import AIState, GoalType, Faction
from src_legacy.core.gameplay.faction import FactionRelation, FactionRegistry


# ---------------------------------------------------------------------------
# GoalRegistry and Model tests
# ---------------------------------------------------------------------------

class TestGoalRegistry:
    """Test the global goal registry and core models."""

    def test_registry_has_expected_count(self):
        # Phase 3: Added SLEEP, EAT, INVESTIGATE (10 -> 13)
        assert len(GOAL_REGISTRY) == 13

    def test_registry_names_unique(self):
        names = [g.name for g in GOAL_REGISTRY]
        assert len(names) == len(set(names))

    def test_registry_contains_all_expected_goals(self):
        names = {g.name for g in GOAL_REGISTRY}
        expected = {
            GoalType.COMBAT, GoalType.FLEE, GoalType.EXPLORE, GoalType.LOOT, 
            GoalType.TRADE, GoalType.REST, GoalType.CRAFT, GoalType.SOCIAL, 
            GoalType.GUARD, GoalType.CORPSE_RUN, GoalType.SLEEP, GoalType.EAT,
            GoalType.INVESTIGATE
        }
        assert names == expected

    def test_all_goals_have_valid_target_states(self):
        for scorer in GOAL_REGISTRY:
            assert isinstance(scorer.target_state, int)  # AIState is IntEnum


class TestGoalScoreModel:
    """Test the GoalScore dataclass."""

    def test_goal_score_creation(self):
        gs = GoalScore(goal=GoalType.COMBAT, score=0.8, target_state=AIState.HUNT)
        assert gs.goal == GoalType.COMBAT
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
# Goal Scorer Properties
# ---------------------------------------------------------------------------

class TestGoalScorerSubclasses:
    """Test that all built-in GoalScorer subclasses have correct properties."""

    def test_combat_goal_properties(self):
        g = CombatGoal()
        assert g.name == GoalType.COMBAT
        assert g.target_state == AIState.HUNT

    def test_flee_goal_properties(self):
        g = FleeGoal()
        assert g.name == GoalType.FLEE
        assert g.target_state == AIState.FLEE

    def test_explore_goal_properties(self):
        g = ExploreGoal()
        assert g.name == GoalType.EXPLORE
        assert g.target_state == AIState.WANDER

    def test_all_scorers_are_goal_scorer_subclasses(self):
        for scorer in GOAL_REGISTRY:
            assert isinstance(scorer, GoalScorer)


# ---------------------------------------------------------------------------
# Goal Evaluation logic
# ---------------------------------------------------------------------------

class TestGoalEvaluation:
    """Test individual goal scoring logic."""

    @pytest.fixture
    def setup_context(self):
        config = MagicMock()
        config.flee_hp_threshold = 0.3
        config.flee_exit_threshold = 0.5
        rng = MagicMock()
        brain = AIBrain(config, rng)
        
        actor = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
        actor.combat.hp = 100
        actor.combat.max_hp = 100
        
        snapshot = MagicMock()
        snapshot.tick = 100
        
        return AIContext(
            actor=actor,
            snapshot=snapshot,
            config=config,
            rng=rng,
            faction_reg=brain._faction_reg,
            _visible_override=[]
        )

    def test_combat_goal_scoring(self, setup_context):
        ctx = setup_context
        # Near enemy -> should be high score
        enemy = Entity(id=2, kind="mob", faction=Faction.GOBLIN_HORDE)
        enemy.spatial.pos = Vector2(2, 1)
        ctx._visible_override = [enemy]
        
        goal = CombatGoal()
        # [AOA STABILIZATION] Explicitly register hostile faction for reliable test mocking
        ctx.faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
        
        score = goal.score(ctx)
        assert score > 0.5

    def test_flee_goal_triggers_on_low_hp(self, setup_context):
        setup_context.actor.combat.hp = 20 # 20% hp
        scorer = FleeGoal()
        score = scorer.score(setup_context)
        assert score > 0.7

    def test_explore_goal_baseline(self, setup_context):
        scorer = ExploreGoal()
        score = scorer.score(setup_context)
        assert 0.3 <= score <= 0.5


# ---------------------------------------------------------------------------
# GoalEvaluator logic
# ---------------------------------------------------------------------------

class TestGoalEvaluator:
    """Test the weighted random goal selection and locking."""

    def test_select_returns_none_on_empty(self):
        result = GoalEvaluator.select([], rng_value=0.5)
        assert result is None

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

    def test_neuroticism_overrides_lock(self):
        config = MagicMock()
        rng = MagicMock()
        brain = AIBrain(config, rng)
        
        actor = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
        actor.combat.max_hp = 100
        actor.combat.hp = 10  # Low HP ratio (0.1 < 0.5) to trigger neuroticism override
        # Neuroticism >= 0.8 allows breaking locks
        actor.mind.decision.personality.neuroticism = 0.9
        
        snapshot = MagicMock()
        snapshot.tick = 100
        
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=config,
            rng=rng,
            faction_reg=brain._faction_reg,
            _visible_override=[]
        )
        
        evaluator = GoalEvaluator(config)
        
        # Manually lock a goal
        actor.mind.decision.goal_committed_at = 95
        config.min_commitment_ticks = 10 # Should be locked until 105
        
        # High neuroticism allows override
        assert evaluator.is_goal_locked(ctx) is False


# ---------------------------------------------------------------------------
# Backward compatibility shim tests
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """Test that the old goal_evaluator.py shim re-exports correctly."""

    def test_shim_exports_goal_score(self):
        from src_legacy.ai.goal_evaluator import GoalScore as LegacyGoalScore
        assert LegacyGoalScore is GoalScore

    def test_shim_exports_goal_evaluator(self):
        from src_legacy.ai.goal_evaluator import GoalEvaluator as LegacyEvaluator
        assert LegacyEvaluator is GoalEvaluator

    def test_shim_exports_registry(self):
        from src_legacy.ai.goal_evaluator import GOAL_REGISTRY as LegacyRegistry
        assert LegacyRegistry is GOAL_REGISTRY
