import pytest
from unittest.mock import MagicMock
from src.engine.world_loop import WorldLoop
from src.core.models.world_state import WorldState
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.entities.entity import Entity
from src.core.aspects.mind import MindAspect
from src.core.models import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def basic_setup():
    config = SimulationConfig(max_ticks=10)
    rng = DeterministicRNG(seed=42)
    grid = Grid(100, 100)
    spatial_index = SpatialHash(cell_size=8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    
    # Create a dummy entity with high next_act_at
    entity = Entity(id=1, kind="hero")
    entity.spatial.pos = Vector2(0, 0)
    entity.next_act_at = 100.0 # Won't act for a long time
    
    # Initialize routine levels
    entity.mind.routine.hunger_level = 0.5
    entity.mind.routine.sleep_debt = 0.5
    
    world.add_entity(entity)
    return config, rng, world

def test_passive_progression_on_quiet_tick(basic_setup):
    """Verify that biological decay and lifecycle systems run even if entity doesn't act."""
    config, rng, world = basic_setup
    
    # Mock dependencies for WorldLoop
    worker_pool = MagicMock()
    conflict_resolver = MagicMock()
    generator = MagicMock()
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    
    # Initial state
    entity = world.get_entity(1)
    initial_hunger = entity.mind.routine.hunger_level
    initial_sleep = entity.mind.routine.sleep_debt
    initial_tick = world.tick
    
    # Run one tick
    loop.tick_once()
    
    # Verify tick advanced
    assert world.tick == initial_tick + 1
    
    # Verify hunger and sleep increased (Biological Decay)
    # config.hunger_decay_rate defaults to 0.001 usually (or similar)
    assert entity.mind.routine.hunger_level > initial_hunger
    assert entity.mind.routine.sleep_debt > initial_sleep
    
    # Verify entity did NOT act (last_applied should be empty)
    assert len(loop.last_applied) == 0

def test_hero_lifecycle_on_quiet_tick(basic_setup):
    """Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts."""
    config, rng, world = basic_setup
    
    # Add a second entity nearby
    h1 = world.get_entity(1)
    h2 = Entity(id=2, kind="hero")
    h2.spatial.pos = Vector2(1, 0) # Adjacent
    h2.next_act_at = 100.0
    world.add_entity(h2)
    
    # Mock dependencies for WorldLoop
    worker_pool = MagicMock()
    conflict_resolver = MagicMock()
    generator = MagicMock()
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    
    # Check initial familiarity (0.0)
    bond = world.social_registry.get_bond(1, 2)
    assert bond.familiarity == 0.0
    
    # Run one tick
    loop.tick_once()
    
    # Verify familiarity increased (Proximity Bonding)
    # Base gain 0.002 * interaction factor
    assert world.social_registry.get_bond(1, 2).familiarity > 0.0
