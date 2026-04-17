import pytest
from unittest.mock import MagicMock
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.enums import Archetype, Faction, ActionType, GoalType, AIState
from src.actions.base import ActionProposal
from src.systems.gameplay.action_system import ActionSystem
from src.ai.goals.base import GoalEvaluator
from src.ai.states.base import AIContext
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def world():
    return WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))

@pytest.fixture
def hero(world):
    e = Entity(id=world.allocate_entity_id(), kind="hero")
    e.identity.faction = 0
    world.add_entity(e)
    return e

@pytest.fixture
def ctx(world, hero):
    # Mocking dependencies for AIContext
    snapshot = MagicMock()
    snapshot.tick = world.tick
    snapshot.grid = world.grid
    snapshot.entities = world.entities
    
    config = MagicMock()
    config.flee_hp_threshold = 0.2
    
    rng = MagicMock()
    rng.next_float.return_value = 0.5
    
    faction_reg = MagicMock()
    faction_reg.is_hostile.return_value = False
    
    ctx = AIContext(
        actor=hero,
        snapshot=snapshot,
        config=config,
        rng=rng,
        faction_reg=faction_reg
    )
    snapshot.hour = 12
    hero.mind.routine.disrupted_until_tick = 0
    hero.mind.emotion.panic = 0.0
    hero.mind.routine_profiles = []
    hero.mind.place_attachments = []
    return ctx

def test_biological_decay_authoritative(world, hero):
    # 1. Initial state
    assert hero.mind.routine.sleep_debt == 0.0
    
    # 2. Advance time (Biological Decay)
    from src.config import SimulationConfig
    ActionSystem._apply_biological_decay(world, SimulationConfig())
    
    # 3. Verify decay
    assert hero.mind.routine.sleep_debt > 0.0
    assert hero.mind.routine.hunger_level > 0.0

def test_sleep_goal_utility_at_night(ctx):
    evaluator = GoalEvaluator()
    
    # 1. Day Time (Tick 100 = Hour 10)
    ctx.snapshot.tick = 100
    ctx.actor.mind.routine.sleep_debt = 0.5
    scores_day = evaluator.evaluate(ctx)
    score_day = next(s.score for s in scores_day if s.goal == GoalType.SLEEP)
    
    # 2. Night Time (Tick 220 = Hour 22)
    ctx.snapshot.tick = 220
    ctx.snapshot.hour = 22
    scores_night = evaluator.evaluate(ctx)
    score_night = next(s.score for s in scores_night if s.goal == GoalType.SLEEP)
    
    # Utility should be significantly higher at night (+1.0 bonus)
    assert score_night > score_day + 0.5

def test_nocturnal_predator_bonus(ctx):
    ctx.actor.identity.archetype = Archetype.BLOODTHIRSTY_SLAYER
    evaluator = GoalEvaluator()
    
    # 1. Day Time (Tick 100 = Hour 10)
    ctx.snapshot.tick = 100
    scores_day = evaluator.evaluate(ctx)
    combat_day = next(s.score for s in scores_day if s.goal == GoalType.COMBAT)
    
    # 2. Night Time (Tick 220 = Hour 22)
    ctx.snapshot.tick = 220
    ctx.snapshot.hour = 22
    scores_night = evaluator.evaluate(ctx)
    combat_night = next(s.score for s in scores_night if s.goal == GoalType.COMBAT)
    
    # Bloodthirsty Slayers get 1.5x combat bonus at night
    assert combat_night > combat_day * 1.4
    
    # They should also resist Sleep more than average
    ctx.actor.mind.routine.sleep_debt = 0.8
    scores_night_slayer = evaluator.evaluate(ctx)
    utility_night_slayer = next(s.score for s in scores_night_slayer if s.goal == GoalType.SLEEP)
    
    # Normal hero (Balanced)
    ctx.actor.identity.archetype = Archetype.BALANCED
    scores_night_balanced = evaluator.evaluate(ctx)
    utility_night_balanced = next(s.score for s in scores_night_balanced if s.goal == GoalType.SLEEP)
    
    assert utility_night_slayer < utility_night_balanced
