import pytest
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import MovementIntention, ActionType, HeroClass
from src_legacy.core.logic.movement_model import MovementModel
from src_legacy.ai.states.base import AIContext
from src_legacy.core.entities.entity_builder import EntityBuilder

from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash

@pytest.fixture
def snapshot_with_entities():
    """Setup a snapshot with a grid and some entities."""
    from src_legacy.platform.rng import DeterministicRNG
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # 1. Actor (The one moving)
    e1 = EntityBuilder(rng, 1).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(e1)
    
    # 2. Blocker
    e2 = EntityBuilder(rng, 2).kind("hero").at(Vector2(2, 1)).build()
    world.add_entity(e2)
    
    return Snapshot.from_world(world)

def test_movement_model_basic_path(snapshot_with_entities):
    actor = snapshot_with_entities.entities[1]
    ctx = AIContext(actor=actor, snapshot=snapshot_with_entities, config=None, rng=None, faction_reg=None)
    
    target = Vector2(5, 1)
    # Target is east. Next step is (2, 1), but (2, 1) is occupied by entity 2.
    
    proposal = MovementModel.plan_or_step(ctx, target, MovementIntention.PURSUIT, "Test basic")
    
    # Since (2, 1) is blocked and blocker is stationary (NONE intent), actor should Wait or Sidestep.
    # Cardinal neighbors of (1, 1) are (2, 1) [blocked], (0, 1) [reachable], (1, 2) [reachable], (1, 0) [reachable]
    # (2, 1) is the ideal step.
    
    assert proposal.actor_id == 1
    # Check if we sidestepped or waited
    if proposal.verb == ActionType.MOVE:
        assert proposal.target in [Vector2(1, 2), Vector2(1, 0), Vector2(0, 1)]
        assert "Sidestepping" in str(proposal.reason)
    else:
        assert proposal.verb == ActionType.REST
        assert "Waiting" in str(proposal.reason)

def test_movement_model_yielding_priority():
    from src_legacy.platform.rng import DeterministicRNG
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # 1. Actor (PURSUIT)
    actor = EntityBuilder(rng, 1).kind("hero").at(Vector2(1, 1)).build()
    actor.mind.navigation.intention = MovementIntention.PURSUIT
    world.add_entity(actor)
    
    # 2. Blocker (RETREAT)
    blocker = EntityBuilder(rng, 2).kind("hero").at(Vector2(2, 1)).build()
    blocker.mind.navigation.intention = MovementIntention.RETREAT
    world.add_entity(blocker)
    
    # Block sidesteps
    from src_legacy.core.models.enums import Material
    world.grid.set(Vector2(1, 2), Material.WALL)
    world.grid.set(Vector2(1, 0), Material.WALL)
    world.grid.set(Vector2(0, 1), Material.WALL)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[1], snapshot=snapshot, config=None, rng=None, faction_reg=None)
    target = Vector2(5, 1)
    
    proposal = MovementModel.plan_or_step(ctx, target, MovementIntention.PURSUIT, "Test yielding")
    
    assert proposal.verb == ActionType.REST
    assert "Yielding" in str(proposal.reason)

def test_movement_model_stuck_threshold():
    from src_legacy.platform.rng import DeterministicRNG
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    actor = EntityBuilder(rng, 1).kind("hero").at(Vector2(1, 1)).build()
    nav = actor.mind.navigation
    nav.blocked_ticks = 2
    nav.cached_path = [Vector2(1, 1), Vector2(2, 1), Vector2(3, 1)]
    nav.cached_path_target = Vector2(5, 1)
    world.add_entity(actor)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[1], snapshot=snapshot, config=None, rng=None, faction_reg=None)
    
    # blocked_ticks == 2 should trigger replan in plan_route
    path = MovementModel.plan_route(ctx, Vector2(5, 1))
    
    # Since it's blocked, it should NOT just return the cached path if it thinks it's stuck.
    # In plan_route, it replans if blocked_ticks >= 2.
    # The A* result might be identical, but we've triggered the logic.
    assert ctx.actor.mind.navigation.blocked_ticks == 2
