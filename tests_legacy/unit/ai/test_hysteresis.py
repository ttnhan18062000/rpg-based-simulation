import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for Goal Hysteresis & Anti-Oscillation (TCK-20260326-HYSTERESIS).

Verifies the 3-layer anti-oscillation system:
  Layer 1: Goal Lock — minimum commitment duration before re-evaluation.
  Layer 2: Cooldown Penalty — recently abandoned goals get score penalty.
  Layer 3: Threshold Deadband — flee enters at 30%, exits at 50%.
"""

from src_legacy.ai.goals.base import (
    GoalEvaluator, GoalScore, HysteresisModifier, CooldownModifier,
    GOAL_REGISTRY,
)
from src_legacy.ai.goals.scorers import FleeGoal, CombatGoal
from src_legacy.ai.states import AIContext
from src_legacy.config import SimulationConfig
from src_legacy.core.models.enums import AIState, ActionType
from src_legacy.core.gameplay.faction import Faction, FactionRegistry
from src_legacy.core.world.grid import Grid
from src_legacy.core.aspects.inventory import InventoryAspect
from src_legacy.core.entities.entity import Entity, Vector2
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.world_state import WorldState
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.platform.spatial_hash import SpatialHash


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_world(tick: int = 100) -> WorldState:
    grid = Grid(32, 32)
    spatial = SpatialHash(8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.tick = tick
    return world


def _make_hero(
    eid: int = 1,
    hp: int = 50,
    max_hp: int = 100,
    ai_state: AIState = AIState.IDLE,
    last_goal: str | None = None,
    goal_committed_at: int = 0,
) -> Entity:
    hero = Entity(id=eid, kind="hero")
    hero.spatial.pos = Vector2(5, 5)
    hero.identity.faction = Faction.HERO_GUILD
    hero.combat.hp = hp
    hero.combat.max_hp = max_hp
    hero.combat.atk_base = 10
    hero.combat.def_base = 5
    hero.combat.spd_base = 10
    
    hero.inventory = InventoryAspect(items=[], max_slots=12, max_weight=100.0)
    
    hero.mind.decision.ai_state = ai_state
    hero.mind.decision.last_goal = last_goal
    hero.mind.decision.goal_committed_at = goal_committed_at
    return hero


def _make_ctx(
    entity: Entity,
    world: WorldState,
    config: SimulationConfig | None = None,
) -> AIContext:
    cfg = config or SimulationConfig()
    rng = DeterministicRNG(42)
    faction_reg = FactionRegistry.default()
    snapshot = Snapshot.from_world(world)
    return AIContext(
        actor=snapshot.entities[entity.id],
        snapshot=snapshot,
        config=cfg,
        rng=rng,
        faction_reg=faction_reg,
    )


# ===========================================================================
# Layer 1: Goal Lock (Minimum Commitment)
# ===========================================================================

class TestGoalLock:
    """Layer 1: Entities must hold a goal for min_commitment_ticks."""

    def test_goal_lock_prevents_switch_within_commitment(self):
        """Entity should NOT re-evaluate goals before commitment expires."""
        cfg = SimulationConfig(min_commitment_ticks=3)
        world = _make_world(tick=10)
        hero = _make_hero(
            ai_state=AIState.WANDER,
            last_goal="explore",
            goal_committed_at=9,  # committed at tick 9 → locked until tick 12
        )
        world.add_entity(hero)
        ctx = _make_ctx(hero, world, config=cfg)

        evaluator = GoalEvaluator()
        assert evaluator.is_goal_locked(ctx), (
            "Entity should be locked for 3 ticks after commitment"
        )

    def test_goal_lock_allows_switch_after_commitment(self):
        """Entity should re-evaluate freely after commitment period."""
        cfg = SimulationConfig(min_commitment_ticks=3)
        world = _make_world(tick=15)
        hero = _make_hero(
            ai_state=AIState.WANDER,
            last_goal="explore",
            goal_committed_at=10,  # committed at tick 10 → unlocked at tick 13
        )
        world.add_entity(hero)
        ctx = _make_ctx(hero, world, config=cfg)

        evaluator = GoalEvaluator()
        assert not evaluator.is_goal_locked(ctx), (
            "Entity should be free to re-evaluate after commitment expired"
        )

    def test_critical_override_breaks_lock(self):
        """HP < 15% should override goal lock (emergency flee)."""
        cfg = SimulationConfig(min_commitment_ticks=10)
        world = _make_world(tick=5)
        hero = _make_hero(
            hp=10, max_hp=100,  # 10% HP — critical
            ai_state=AIState.HUNT,
            last_goal="combat",
            goal_committed_at=4,  # Just committed, locked until tick 14
        )
        world.add_entity(hero)
        ctx = _make_ctx(hero, world, config=cfg)

        evaluator = GoalEvaluator()
        assert not evaluator.is_goal_locked(ctx), (
            "Critical HP (<15%) should override goal lock"
        )


# ===========================================================================
# Layer 2: Cooldown Penalty
# ===========================================================================

class TestCooldownPenalty:
    """Layer 2: Recently abandoned goals receive a score penalty."""

    def test_cooldown_penalty_applied_to_abandoned_goal(self):
        """A goal that was recently abandoned should have its score halved."""
        world = _make_world(tick=20)
        hero = _make_hero(last_goal="explore")
        hero.mind.decision.goal_cooldowns = {"combat": 25}  # cooldown until tick 25
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = CooldownModifier()
        score = GoalScore(goal="combat", score=1.0, target_state=AIState.HUNT)
        modifier.modify(score, ctx)

        assert score.score < 1.0, (
            f"Cooldown penalty should reduce score, got {score.score}"
        )
        assert abs(score.score - 0.5) < 0.01, (
            f"Default cooldown penalty should halve the score, got {score.score}"
        )

    def test_cooldown_does_not_affect_non_cooled_goals(self):
        """Goals not on cooldown should be unaffected."""
        world = _make_world(tick=20)
        hero = _make_hero()
        hero.mind.decision.goal_cooldowns = {"combat": 25}
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = CooldownModifier()
        score = GoalScore(goal="explore", score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)

        assert score.score == 1.0, (
            f"Non-cooled goal should be unaffected, got {score.score}"
        )

    def test_cooldown_expires_after_duration(self):
        """Cooldown should have no effect after expiry tick."""
        world = _make_world(tick=30)  # tick 30 > cooldown expiry 25
        hero = _make_hero()
        hero.mind.decision.goal_cooldowns = {"combat": 25}
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = CooldownModifier()
        score = GoalScore(goal="combat", score=1.0, target_state=AIState.HUNT)
        modifier.modify(score, ctx)

        assert score.score == 1.0, (
            f"Expired cooldown should not penalize, got {score.score}"
        )


# ===========================================================================
# Layer 3: Threshold Deadband (Flee Enter/Exit)
# ===========================================================================

class TestFleeDeadband:
    """Layer 3: Flee uses different thresholds for entering vs exiting."""

    def test_flee_enters_at_threshold(self):
        """Flee score should be high when HP < flee_hp_threshold (30%)."""
        world = _make_world()
        hero = _make_hero(hp=25, max_hp=100, ai_state=AIState.WANDER)
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        scorer = FleeGoal()
        score = scorer.score(ctx)
        assert score > 0.5, f"HP at 25% should trigger strong flee, got {score}"

    def test_flee_continues_until_exit_threshold(self):
        """Entity currently fleeing should NOT stop until HP > flee_exit_threshold."""
        cfg = SimulationConfig(flee_exit_threshold=0.5)
        world = _make_world()
        # HP at 40% — above enter threshold (30%) but below exit threshold (50%)
        hero = _make_hero(hp=40, max_hp=100, ai_state=AIState.FLEE)
        hero.mind.decision.last_goal = "flee"
        world.add_entity(hero)
        ctx = _make_ctx(hero, world, config=cfg)

        scorer = FleeGoal()
        score = scorer.score(ctx)
        assert score > 0.5, (
            f"Currently fleeing at 40% HP (below exit 50%) should keep fleeing, got {score}"
        )

    def test_flee_stops_above_exit_threshold(self):
        """Entity currently fleeing should stop when HP > flee_exit_threshold."""
        cfg = SimulationConfig(flee_exit_threshold=0.5)
        world = _make_world()
        hero = _make_hero(hp=55, max_hp=100, ai_state=AIState.FLEE)
        hero.mind.decision.last_goal = "flee"
        world.add_entity(hero)
        ctx = _make_ctx(hero, world, config=cfg)

        scorer = FleeGoal()
        score = scorer.score(ctx)
        assert score < 0.3, (
            f"HP at 55% (above exit 50%) should stop fleeing, got {score}"
        )


# ===========================================================================
# Enhanced HysteresisModifier (Duration Scaling)
# ===========================================================================

class TestHysteresisBoostScaling:
    """HysteresisModifier should scale boost with commitment duration."""

    def test_short_hold_gives_base_boost(self):
        """Just-committed goal gets base 1.25x boost."""
        world = _make_world(tick=12)
        hero = _make_hero(last_goal="explore", goal_committed_at=11)
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = HysteresisModifier()
        score = GoalScore(goal="explore", score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)

        assert 1.2 <= score.score <= 1.35, (
            f"Short hold should give ~1.25x boost, got {score.score}"
        )

    def test_long_hold_gives_stronger_boost(self):
        """Goal held for 10+ ticks should get up to 1.75x boost."""
        world = _make_world(tick=20)
        hero = _make_hero(last_goal="explore", goal_committed_at=5)
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = HysteresisModifier()
        score = GoalScore(goal="explore", score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)

        assert score.score > 1.5, (
            f"Long hold (15 ticks) should give strong boost, got {score.score}"
        )

    def test_different_goal_gets_no_boost(self):
        """A goal that is NOT the current goal gets no hysteresis boost."""
        world = _make_world(tick=20)
        hero = _make_hero(last_goal="combat", goal_committed_at=5)
        world.add_entity(hero)
        ctx = _make_ctx(hero, world)

        modifier = HysteresisModifier()
        score = GoalScore(goal="explore", score=1.0, target_state=AIState.WANDER)
        modifier.modify(score, ctx)

        assert score.score == 1.0, (
            f"Non-current goal should get no boost, got {score.score}"
        )
