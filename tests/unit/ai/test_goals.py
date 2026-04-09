import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock
from src.ai.brain import AIBrain, AIContext
from src.ai.goals.base import GOAL_REGISTRY, GoalType, GoalScore
from src.ai.goals.scorers import CombatGoal, FleeGoal, ExploreGoal
from src.core.entities.entity import Entity, Vector2
from src.core.gameplay.faction import FactionRelation


class TestGoalRegistry:
    """Test the global goal registry."""

    def test_registry_has_10_goals(self):
        # Increased to 12 in Phase 1 (Stage 4 baseline)
        assert len(GOAL_REGISTRY) == 12

    def test_registry_names_unique(self):
        names = [g.name for g in GOAL_REGISTRY]
        assert len(names) == len(set(names))

    def test_registry_contains_core_goals(self):
        names = {g.name for g in GOAL_REGISTRY}
        expected = {
            GoalType.COMBAT, GoalType.FLEE, GoalType.EXPLORE, GoalType.LOOT, 
            GoalType.TRADE, GoalType.REST, GoalType.CRAFT, GoalType.SOCIAL, 
            GoalType.GUARD, GoalType.CORPSE_RUN, GoalType.SLEEP, GoalType.EAT
        }
        assert names == expected


class TestGoalEvaluation:
    """Test individual goal scoring logic."""

    @pytest.fixture
    def setup_context(self):
        config = MagicMock()
        config.flee_hp_threshold = 0.3
        config.flee_exit_threshold = 0.5
        rng = MagicMock()
        brain = AIBrain(config, rng)
        
        actor = Entity(id=1, kind="hero", faction="player")
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
        enemy = Entity(id=2, kind="mob", faction="global_hostile")
        enemy.spatial.pos = Vector2(2, 1)
        ctx._visible_override = [enemy]
        
        goal = CombatGoal()
        # [AOA STABILIZATION] Explicitly register hostile faction for reliable test mocking
        ctx.faction_reg.set_relation("player", "global_hostile", FactionRelation.HOSTILE)
        
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
        assert 0.1 <= score <= 0.3


class TestGoalLocking:
    """Test goal commitment and overrides."""

    def test_neuroticism_overrides_lock(self):
        config = MagicMock()
        rng = MagicMock()
        brain = AIBrain(config, rng)
        
        actor = Entity(id=1, kind="hero", faction="player")
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
        
        from src.ai.goal_evaluator import GoalEvaluator
        evaluator = GoalEvaluator(config)
        
        # Manually lock a goal
        actor.mind.decision.goal_committed_at = 95
        config.min_commitment_ticks = 10 # Should be locked until 105
        
        # High neuroticism allows override
        assert evaluator.is_goal_locked(ctx) is False


class TestAIBrainShim:
    """Test legacy shims for backward compatibility."""

    def test_shim_exports_registry(self):
        from src.ai.goal_evaluator import GOAL_REGISTRY as LegacyRegistry
        assert LegacyRegistry is GOAL_REGISTRY
        assert len(LegacyRegistry) == 12
