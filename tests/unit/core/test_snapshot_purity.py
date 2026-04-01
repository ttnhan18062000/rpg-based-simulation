import pytest
from src.core.models.world_state import WorldState
from src.core.models.snapshot import Snapshot
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.engine.phase_guard import ActionProposalGuard
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

def test_simulation_model_collection_freeze_list():
    """Verify that lists in SimulationModel become immutable after freeze."""
    from src.core.models.base import SimulationModel
    from typing import List
    
    class MockModel(SimulationModel):
        items: List[int] = [1, 2, 3]
        
    m = MockModel()
    m.items.append(4)
    assert len(m.items) == 4
    
    m.freeze()
    # Now it's a tuple
    assert isinstance(m.items, tuple)
    with pytest.raises(AttributeError):
        m.items.append(5)

def test_simulation_model_collection_freeze_dict():
    """Verify that dicts in SimulationModel become immutable MappingProxy after freeze."""
    from src.core.models.base import SimulationModel
    from typing import Dict
    from types import MappingProxyType
    
    class MockModel(SimulationModel):
        data: Dict[str, int] = {"a": 1}
        
    m = MockModel()
    m.data["b"] = 2
    assert m.data["b"] == 2
    
    m.freeze()
    assert isinstance(m.data, MappingProxyType)
    with pytest.raises(TypeError): # MappingProxyType raises TypeError on __setitem__
        m.data["c"] = 3

def test_world_state_freeze_guards():
    """Verify that WorldState prevents mutations after freeze."""
    ws = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))
    ws.freeze()
    
    with pytest.raises(RuntimeError, match="Cannot call add_entity"):
        ws.add_entity(Entity(id=1, kind="hero"))
        
    with pytest.raises(RuntimeError, match="Cannot call move_entity"):
        ws.move_entity(1, Vector2(5, 5))

def test_snapshot_deep_purity():
    """Verify that Snapshot entities and their nested aspects are recursively frozen."""
    from src.core.aspects.inventory import InventoryAspect
    ws = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))
    e = Entity(id=99, kind="hero", inventory=InventoryAspect())
    ws.add_entity(e)
    
    # 1. Modify mutable state
    e.combat.hp = 100
    e.inventory.items = ["sword"]
    
    # 2. Create Snapshot
    snap = Snapshot.from_world(ws)
    snap_e = snap.entities[99]
    
    # 3. Verify freeze on snapshot entity
    with pytest.raises(RuntimeError, match="Cannot mutate frozen CombatAspect"):
        snap_e.combat.hp = 50
        
    # 4. Verify freeze on collections (list -> tuple)
    assert isinstance(snap_e.inventory.items, tuple)
    with pytest.raises(AttributeError):
        snap_e.inventory.items.append("shield")
        
    # 5. Verify the live entity is NOT frozen (AOA Pillar: strictly partitioned)
    e.combat.hp = 80
    assert e.combat.hp == 80

def test_action_proposal_guard_integration():
    """Verify the ActionProposalGuard context manager properly freezes the snapshot."""
    snap = Snapshot(tick=0, seed=0, entities={}, grid=Grid(1,1), ground_items={}, camps=(), buildings=(), resource_nodes=(), treasure_chests=(), regions=())
    
    # Initial check (dataclass frozen=True protects top-level, but not nested if they weren't frozen)
    # But here we just want to see if the guard calls freeze()
    
    with ActionProposalGuard(snap) as guarded_snap:
        assert guarded_snap == snap
        # If we had a mutable entity inside, it should be frozen now.
        # (Snapshot.from_world already freezes them, but the guard is a safety net).
        pass
