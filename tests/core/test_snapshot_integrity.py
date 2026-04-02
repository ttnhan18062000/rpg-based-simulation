import pytest
from src.core.models.snapshot import Snapshot
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

def test_snapshot_immutability_enforced():
    # Setup world
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # Create snapshot
    snapshot = Snapshot.from_world(world)
    
    # 1. Attempt to mutate entities dict
    with pytest.raises(TypeError):
        snapshot.entities[999] = None
        
    # 2. Attempt to mutate ground_items dict
    with pytest.raises(TypeError):
        snapshot.ground_items[(0, 0)] = ["test"]
        
    # 3. Attempt to mutate faction_aggression
    with pytest.raises(TypeError):
        snapshot.faction_aggression[1] = 1.0

def test_snapshot_entities_are_deep_copied():
    from src.core.entities.entity_builder import EntityBuilder
    from src.platform.rng import DeterministicRNG
    
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    hero = EntityBuilder(rng, 1).kind("hero").build()
    hero.combat.combat.hp = 100
    hero.combat.combat.max_hp = 100
    world.add_entity(hero)
    
    snapshot = Snapshot.from_world(world)
    snap_hero = snapshot.entities[1]
    
    # Mutate world hero AFTER snapshot
    hero.combat.combat.hp = 1
    
    # Snapshot hero should be unchanged
    assert snap_hero.combat.combat.hp == 100
    assert snap_hero is not hero # Reference check

def test_snapshot_entities_are_frozen():
    from src.core.entities.entity_builder import EntityBuilder
    from src.platform.rng import DeterministicRNG
    
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    hero = EntityBuilder(rng, 1).kind("hero").build()
    world.add_entity(hero)
    
    snapshot = Snapshot.from_world(world)
    snap_hero = snapshot.entities[1]
    
    # 1. Attempt to mutate snap_hero direct attribute (Entity level)
    with pytest.raises(RuntimeError, match="Cannot mutate frozen Entity"):
        snap_hero.id = 999
        
    # 2. Attempt to mutate snap_hero aspect attribute (Aspect level)
    # This should trigger RuntimeError from SimulationModel.__setattr__
    with pytest.raises(RuntimeError, match="Cannot mutate frozen CombatAspect"):
        snap_hero.combat.combat.hp = 50
        
    # 3. Attempt to mutate nested mind state
    with pytest.raises(RuntimeError, match="Cannot mutate frozen DecisionState"):
        snap_hero.mind.decision.ai_state = 99
