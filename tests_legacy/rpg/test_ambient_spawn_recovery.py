import pytest
from src_legacy.core.state import AuthoritativeState, RegionState, EntityState
from src_legacy.systems.spawn_system import SpawnSystem
from src_legacy.systems.generator import EntityGenerator
from src_legacy.core.updates import StateUpdate

def test_ambient_spawning_wilderness():
    """
    Law: Entities must spawn in wilderness regions to maintain a base population.
    """
    # 1. Setup: Forest region with 0 entities
    forest = RegionState(
        id="forest_1", name="Dark Forest",
        bounds=(-50, -50, 50, 50), kind="FOREST"
    )
    
    # Tick is multiple of SPAWN_INTERVAL (100)
    state = AuthoritativeState(tick=100, seed=1, entities={}, regions={"forest_1": forest})
    generator = EntityGenerator(1)
    
    # 2. Process spawns
    upd = SpawnSystem.resolve_ambient_spawns(state, StateUpdate(), generator)
    
    # Verify one entity added
    assert len(upd.entities_add) == 1
    new_ent = upd.entities_add[0]
    assert new_ent.kind in ["monster", "goblin"] # Forest spawns monsters
    assert forest.bounds[0] <= new_ent.position[0] <= forest.bounds[2]

def test_spawning_respects_cap():
    """
    Law: Spawning must respect regional population caps.
    """
    forest = RegionState(
        id="forest_1", name="Dark Forest",
        bounds=(-50, -50, 50, 50), kind="FOREST"
    )
    
    # Pre-fill with many entities (more than target cap which is ~5 for forest)
    entities = {i: EntityState(id=i, kind="monster", position=(0,0)) for i in range(10)}
    
    state = AuthoritativeState(tick=100, seed=1, entities=entities, regions={"forest_1": forest})
    generator = EntityGenerator(1)
    
    # 2. Process spawns
    upd = SpawnSystem.resolve_ambient_spawns(state, StateUpdate(), generator)
    
    # Verify NO entities added
    assert len(upd.entities_add) == 0

def test_spawn_interval():
    """
    Law: Spawning only occurs at specific intervals.
    """
    forest = RegionState(
        id="forest_1", name="Dark Forest",
        bounds=(-50, -50, 50, 50), kind="FOREST"
    )
    
    # Tick 101 is NOT multiple of 100
    state = AuthoritativeState(tick=101, seed=1, entities={}, regions={"forest_1": forest})
    generator = EntityGenerator(1)
    
    upd = SpawnSystem.resolve_ambient_spawns(state, StateUpdate(), generator)
    assert len(upd.entities_add) == 0
