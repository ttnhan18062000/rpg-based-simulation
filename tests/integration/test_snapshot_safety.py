import pytest
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.core.aspects.mind import MindAspect

def test_entity_deep_copy_isolation():
    """Verify that Entity.copy() provides absolute isolation for nested mutable structures."""
    # 1. Setup entity with a mutable list in MindAspect
    ent = Entity(id=1, kind="hero")
    ent.mind.navigation.pos_history = [(10, 10), (11, 11)]
    
    # 2. Perform deep copy
    ent_copy = ent.copy()
    
    # 3. Mutate the copy's list
    ent_copy.mind.navigation.pos_history.append((12, 12))
    
    # 4. Assert isolation
    assert len(ent.mind.navigation.pos_history) == 2, "Original entity's list was mutated via the copy!"
    assert len(ent_copy.mind.navigation.pos_history) == 3
    assert ent.mind.navigation.pos_history is not ent_copy.mind.navigation.pos_history

def test_snapshot_actor_isolation():
    """Verify that resolving an actor from a Snapshot ensures mutation safety."""
    from src.platform.spatial_hash import SpatialHash
    grid = Grid(100, 100)
    spatial = SpatialHash(16)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    ent = Entity(id=1, kind="hero")
    ent.mind.navigation.pos_history = [(0, 0)]
    world.entities[1] = ent
    
    # Create snapshot
    snapshot = Snapshot.from_world(world)
    
    # Resolve actor from snapshot
    snapshot_actor = snapshot.entities.get(1)
    
    # Mutate snapshot actor
    snapshot_actor.mind.navigation.pos_history.append((1, 1))
    
    # Verify live entity is untouched
    assert len(world.entities[1].mind.navigation.pos_history) == 1, "Live world entity was mutated via the snapshot actor!"
    assert len(snapshot_actor.mind.navigation.pos_history) == 2

def test_aspect_model_rebuild_integrity():
    """Ensure that deep copies correctly initialize models and don't lose data."""
    ent = Entity(id=5, kind="monster")
    ent.combat.combat.hp = 50
    ent.combat.combat.max_hp = 100
    
    ent_copy = ent.copy()
    
    assert ent_copy.id == 5
    assert ent_copy.kind == "monster"
    assert ent_copy.combat.combat.hp == 50
    assert ent_copy.combat.combat.max_hp == 100
    
    # Modify copy
    ent_copy.combat.combat.hp = 20
    assert ent.combat.combat.hp == 50, "Direct attribute mutation leaked!"
