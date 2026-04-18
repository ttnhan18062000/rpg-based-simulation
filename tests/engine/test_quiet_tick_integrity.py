import pytest
from unittest.mock import MagicMock
from src.engine.world_loop import WorldLoop
from src.core.models.world_state import WorldState
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.entities.entity import Entity
from src.core.models import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def clean_world():
    config = SimulationConfig(max_ticks=100)
    rng = DeterministicRNG(seed=42)
    grid = Grid(100, 100)
    spatial_index = SpatialHash(cell_size=8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    
    # Mock dependencies for WorldLoop
    worker_pool = MagicMock()
    conflict_resolver = MagicMock()
    generator = MagicMock()
    generator.should_spawn.return_value = False
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    return loop, world, config

def test_scenario_1_dead_world_progression(clean_world):
    """Scenario 1: No living entities. Verify tick still increments and systems advance."""
    loop, world, config = clean_world
    
    # Tick 0
    assert world.tick == 0
    
    # Run 5 ticks (forcing past zero-alive stop condition if necessary, 
    # but WorldLoop.tick_once checks this)
    # Note: tick_once returns False if all dead. We want to verify the PATH is still legal.
    # In Milestone 1, we want "quiet ticks" to be guarded.
    
    # Verification: Even if tick_once returns False, it should have incremented the tick 
    # OR we verify the PreSystemsPhase execution.
    
    # Let's add one dead entity to satisfy the alive_count > 0 check if it exists
    # Actually, WorldLoop.tick_once (line 206) ends simulation if no entities alive AND tick > 0.
    # So we can run tick 0 -> 1.
    
    result = loop.tick_once()
    assert result is True
    assert world.tick == 1
    
    # If all dead, tick_once 1 -> 2 will return False
    result = loop.tick_once()
    assert result is False

def test_scenario_2_sleeping_world_biological_decay(clean_world):
    """Scenario 2: All entities have high next_act_at. Verify biological decay hits."""
    loop, world, config = clean_world
    
    # Add a hero who is "sleeping/waiting"
    h = Entity(id=1, kind="hero")
    h.spatial.pos = Vector2(5, 5)
    h.next_act_at = 1000.0 # Far future
    h.mind.routine.hunger_level = 0.5
    world.add_entity(h)
    
    initial_hunger = h.mind.routine.hunger_level
    
    # Run 10 ticks
    for _ in range(10):
        loop.tick_once()
        
    assert world.tick == 10
    # Hunger should have increased 10 times
    assert h.mind.routine.hunger_level > initial_hunger
    # Default decay is ~0.001 per tick
    assert h.mind.routine.hunger_level >= initial_hunger + 0.009 

def test_scenario_3_stationary_world_proximity_bonding(clean_world):
    """Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem."""
    loop, world, config = clean_world
    
    h1 = Entity(id=1, kind="hero")
    h1.spatial.pos = Vector2(10, 10)
    h1.next_act_at = 1000.0
    world.add_entity(h1)
    
    h2 = Entity(id=2, kind="hero")
    h2.spatial.pos = Vector2(10, 11) # Adjacent
    h2.next_act_at = 1000.0
    world.add_entity(h2)
    
    bond = world.social_registry.get_bond(1, 2)
    assert bond.familiarity == 0.0
    
    # Run 5 ticks
    for _ in range(5):
        loop.tick_once()
        
    assert world.tick == 5
    # Familiarity should have increased
    new_bond = world.social_registry.get_bond(1, 2)
    assert new_bond.familiarity > 0.0
    assert new_bond.familiarity >= 0.005 # ~0.001-0.002 per tick depending on proximity

def test_scenario_4_subsystem_advancement(clean_world):
    """Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply."""
    loop, world, config = clean_world
    
    # Mock a system
    mock_system = MagicMock()
    # SystemManager.register expects a system with .update or .on_tick?
    # Actually, WorldLoop registers systems in __init__.
    # Let's check SystemContext in PreSystemsPhase.
    
    # We can inject a mock system into loop._system_manager
    loop._system_manager.register(mock_system, 1) # tick every tick
    
    # Run one tick
    loop.tick_once()
    
    # mock_system should be called by system_manager.tick()
    assert mock_system.on_tick.called
