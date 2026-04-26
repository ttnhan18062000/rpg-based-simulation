import pytest
from src.core.state import AuthoritativeState, EntityState, RegionState, LocalScarState
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, StrategicUpdate
from src.core.state import ItemStack
from src.engine.apply import ApplyPath

def test_fingerprint_captures_inventory_changes():
    """Verify that adding items to an entity changes the state fingerprint."""
    e1 = EntityState(id=1, kind="H", position=(0, 0))
    state = AuthoritativeState(tick=100, seed=42, entities={1: e1})
    
    fp1 = state.fingerprint()["state_hash"]
    
    # Update: add 10 gold
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, inventory=InventoryUpdate(gold_delta=10))}
    )
    new_state = ApplyPath.apply_generation(state, upd)
    
    fp2 = new_state.fingerprint()["state_hash"]
    assert fp1 != fp2
    assert new_state.entities[1].inventory.gold == 10

def test_fingerprint_captures_strategic_changes():
    """Verify that adding strategic projects changes the state fingerprint."""
    from src.core.strategic import ProjectState
    e1 = EntityState(id=1, kind="H", position=(0, 0))
    state = AuthoritativeState(tick=100, seed=42, entities={1: e1})
    
    fp1 = state.fingerprint()["state_hash"]
    
    project = ProjectState(id="p1", kind="quest")
    upd = StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate(projects_add_or_update=[project]))}
    )
    new_state = ApplyPath.apply_generation(state, upd)
    
    fp2 = new_state.fingerprint()["state_hash"]
    assert fp1 != fp2
    assert "p1" in new_state.entities[1].strategic.projects

def test_fingerprint_captures_world_dynamics():
    """Verify that regional influence changes the state fingerprint."""
    r1 = RegionState(id="forest", name="Forest", bounds=(0,0,10,10))
    state = AuthoritativeState(tick=100, seed=42, regions={"forest": r1})
    
    fp1 = state.fingerprint()["state_hash"]
    
    from src.core.updates import WorldUpdate
    upd = StateUpdate(
        world_updates={"forest": WorldUpdate(region_id="forest", influence_delta=10.0)}
    )
    new_state = ApplyPath.apply_generation(state, upd)
    
    fp2 = new_state.fingerprint()["state_hash"]
    assert fp1 != fp2
    assert new_state.regions["forest"].influence == 10.0

def test_determinism_same_seed_same_hash():
    """Verify that two identical states produce the same hash via CanonicalStateHasher."""
    from src.engine.checkpoint import CanonicalStateHasher
    
    e1 = EntityState(id=1, kind="H", position=(5, 5))
    r1 = RegionState(id="town", name="Town", bounds=(0,0,20,20), influence=50.0)
    
    state_a = AuthoritativeState(tick=100, seed=42, entities={1: e1}, regions={"town": r1})
    state_b = AuthoritativeState(tick=100, seed=42, entities={1: e1}, regions={"town": r1})
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b
    
    # Change something minor
    state_c = AuthoritativeState(tick=100, seed=42, entities={1: e1}, regions={"town": replace(r1, influence=50.1)})
    hash_c = CanonicalStateHasher.get_hash(state_c)
    assert hash_a != hash_c

from dataclasses import replace
