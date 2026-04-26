import pytest
from src_legacy.core.state import AuthoritativeState, RegionState, BuildingState
from src_legacy.core.updates import StateUpdate
from src_legacy.systems.generator import EntityGenerator
from src_legacy.systems.spawn_system import SpawnSystem

def test_camp_spawning():
    """
    Phase 9: Verify that ambient spawning creates entities anchored to camps.
    """
    seed = 42
    generator = EntityGenerator(seed)
    
    # 1. Setup World with a camp
    camp_pos = (20.0, 20.0)
    regions = {
        "WILDERNESS": RegionState(
            id="WILDERNESS", name="Wilderness", 
            bounds=(0, 0, 128, 128), kind="FOREST", 
            hazard_level=0.1
        )
    }
    buildings = {
        1: BuildingState(id=1, kind="GOBLIN_CAMP", position=camp_pos)
    }
    
    # Empty world
    state = AuthoritativeState(
        tick=100, # Triggers spawn
        seed=seed,
        entities={},
        regions=regions,
        buildings=buildings
    )
    
    update = StateUpdate()
    
    # 2. Resolve ambient spawns
    refined_update = SpawnSystem.resolve_ambient_spawns(state, update, generator)
    
    # 3. Assert a monster spawned near the camp
    assert len(refined_update.entities_add) == 1
    new_ent = refined_update.entities_add[0]
    
    assert new_ent.kind == "monster"
    # Should be near the camp (within 10 units based on spawn system logic)
    assert 10.0 <= new_ent.position[0] <= 30.0
    assert 10.0 <= new_ent.position[1] <= 30.0
