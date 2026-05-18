import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.systems.world.generator import EntityGenerator
from src_legacy.config import SimulationConfig
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import AIState, GoalType, LifeRole, Faction, ActionType
from src_legacy.core.world.grid import Grid
from src_legacy.ai.states import AIContext
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.actions.base import MindUpdate

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    from src_legacy.systems.spatial_hash import SpatialHash
    spatial = SpatialHash(10)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def ctx(mock_world):
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    from src_legacy.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry()
    
    # Needs a real actor to test AIBrain
    from src_legacy.core.entities.entity_builder import EntityBuilder
    builder = EntityBuilder(rng, 100)
    actor = builder.kind("hero").at(Vector2(50, 50)).build()
    
    # Force tick ahead so appraisal runs
    mock_world.tick = 20
    snapshot = Snapshot.from_world(mock_world)
    return AIContext(actor=actor, snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)

def test_routine_goal_priority(mock_world, ctx):
    """Verify that an entity with a 'Sleep' routine at hour 22 selects SLEEP goal more often."""
    from src_legacy.ai.brain import AIBrain
    brain = AIBrain(ctx.config, ctx.rng, ctx.faction_reg)
    
    # 1. Set time to day (12:00)
    mock_world.tick = 50 
    ctx.snapshot = Snapshot.from_world(mock_world)
    ctx.actor.mind.routine.sleep_debt = 0.4
    
    _, proposal_day = brain.decide(ctx.actor, ctx.snapshot)
    mind_update_day = next(u for u in proposal_day.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None)
    sleep_bias_day = mind_update_day.motive_utility_biases.get(GoalType.SLEEP, 1.0)
    
    # 2. Set time to night (22:00)
    mock_world.tick = 92 # 22:00
    ctx.snapshot = Snapshot.from_world(mock_world)
    _, proposal_night = brain.decide(ctx.actor, ctx.snapshot)
    mind_update_night = next(u for u in proposal_night.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None)
    sleep_bias_night = mind_update_night.motive_utility_biases.get(GoalType.SLEEP, 1.0)
    
    assert sleep_bias_night > sleep_bias_day + 0.5

def test_place_attachment_navigation(ctx):
    """Verify that choice of SLEEP leads to moving toward HOME attachment."""
    from src_legacy.ai.states.routine import SleepingHandler
    handler = SleepingHandler()
    
    ctx.actor.spatial.pos = Vector2(50, 50)
    ctx.actor.spatial.home_pos = Vector2(10, 10)
    ctx.actor.mind.routine.sleep_debt = 0.8
    ctx.actor.mind.routine.is_sleeping = False
    
    next_state, action = handler.handle(ctx)
    assert next_state == AIState.SLEEPING
    assert action.verb == ActionType.MOVE
    assert "Heading home to sleep" in action.reason

def test_place_attachment_home_navigation(ctx):
    """Verify navigation via PlaceAttachment when home_pos is None."""
    from src_legacy.ai.states.routine import SleepingHandler
    from src_legacy.core.aspects.mind import PlaceAttachment
    from src_legacy.core.models.enums import AttachmentKind
    from src_legacy.core.gameplay.buildings import Building
    handler = SleepingHandler()
    
    ctx.actor.spatial.pos = Vector2(50, 50)
    ctx.actor.spatial.home_pos = None
    ctx.actor.mind.place_attachments = [
        PlaceAttachment(location_pos=Vector2(10, 10), kind=AttachmentKind.HOME, importance=1.0)
    ]
    
    # Mock building in snapshot
    home_building = Building(
        building_id="home_1", 
        name="test home", 
        pos=Vector2(10, 10), 
        building_type="home",
        durability=100.0,
        max_durability=100.0,
        is_functional=True
    )
    ctx.snapshot = ctx.snapshot.model_copy(update={"buildings": (home_building,)})
    
    ctx.actor.mind.routine.sleep_debt = 0.8
    ctx.actor.mind.routine.is_sleeping = False
    
    next_state, action = handler.handle(ctx)
    assert next_state == AIState.SLEEPING
    assert action.verb == ActionType.MOVE
    assert "Heading home to sleep" in action.reason

def test_routine_disruption_panic(mock_world, ctx):
    """Verify that routines are suppressed during high panic."""
    from src_legacy.core.logic.routine_service import RoutineService
    service = RoutineService()
    
    mock_world.tick = 92
    hour = (mock_world.tick % 100) * 24 // 100
    
    biases_calm = service.calculate_routine_biases(ctx.actor, hour, mock_world.tick)
    assert biases_calm.get(GoalType.SLEEP, 0) > 1.0
    
    ctx.actor.mind.emotion.panic = 0.5
    biases_panic = service.calculate_routine_biases(ctx.actor, hour, mock_world.tick)
    assert biases_panic.get(GoalType.SLEEP, 1.0) == 1.0

def test_cluster_social_coordination(ctx, mock_world):
    """Verify that nearby allies in the same cluster increase goal consensus."""
    from src_legacy.ai.brain import AIBrain
    brain = AIBrain(ctx.config, ctx.rng, ctx.faction_reg)
    
    # 1. Setup actor with cluster
    ctx.actor.identity.cluster_id = "test_cluster_1"
    ctx.actor.spatial.vision_range = 20
    
    # 2. Setup ally in the same cluster nearby
    from src_legacy.core.entities.entity_builder import EntityBuilder
    builder = EntityBuilder(DeterministicRNG(1), 101)
    ally = builder.kind("hero").at(Vector2(51, 51)).build()
    ally.identity.cluster_id = "test_cluster_1"
    ally.mind.decision.last_goal = GoalType.COMBAT
    
    # Register ally in world/spatial
    mock_world.entities[ally.id] = ally
    mock_world.spatial_index.insert(ally.id, ally.spatial.pos)
    
    # Force tick ahead for appraisal
    mock_world.tick = 30
    ctx.snapshot = Snapshot.from_world(mock_world)
    
    # VERIFY VISIBILITY IN TEST
    from src_legacy.ai.perception import Perception
    visible = Perception.visible_entities(ctx.actor, ctx.snapshot, ctx.actor.spatial.vision_range)
    assert any(e.id == 101 for e in visible), "Ally 101 should be visible"
    
    _, proposal = brain.decide(ctx.actor, ctx.snapshot)
    mind_update = next(u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None)
    biases = mind_update.motive_utility_biases
    
    # Consensus bias (0.15) should be applied to COMBAT goal
    # 1.0 (base) * 1.15 (social) = 1.15
    assert biases.get(GoalType.COMBAT, 0.0) > 1.05
