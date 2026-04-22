import pytest
import copy
from src_v2.core.state import AuthoritativeState, EntityState, IdentityComponent
from src_v2.engine.checkpoint import CanonicalStateHasher

def test_hash_stability_with_dict_order():
    """Verify that different dictionary insertion orders produce the same hash."""
    # State A: Insert 'wood' then 'gold'
    res_a = {"wood": 10, "gold": 100}
    state_a = AuthoritativeState(tick=1, seed=1, global_resources=res_a)
    
    # State B: Insert 'gold' then 'wood'
    res_b = {}
    res_b["gold"] = 100
    res_b["wood"] = 10
    state_b = AuthoritativeState(tick=1, seed=1, global_resources=res_b)
    
    hash_a = CanonicalStateHasher.get_hash(state_a)
    hash_b = CanonicalStateHasher.get_hash(state_b)
    
    assert hash_a == hash_b

def test_snapshot_immutability():
    """Verify that components are frozen and cannot be mutated."""
    ent = EntityState(id=1, kind="HERO", position=(0, 0))
    
    with pytest.raises(Exception): # Exact exception depends on dataclass implementation (FrozenInstanceError)
        ent.position = (1, 1)
    
    with pytest.raises(Exception):
        ent.identity.faction = 99

def test_deep_isolation_in_collections():
    """Verify that changing a collection in one generation doesn't affect another."""
    from src_v2.engine.apply import ApplyPath
    from src_v2.core.updates import StateUpdate, EntityUpdate, IdentityUpdate
    
    ent = EntityState(id=1, kind="HERO", position=(0, 0), identity=IdentityComponent(known_recipes={"a"}))
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent})
    
    # Update state: add recipe "b"
    upd = EntityUpdate(entity_id=1, identity=IdentityUpdate(recipes_learned=["b"]))
    state_upd = StateUpdate(entity_updates={1: upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd, 1, 1000)
    
    # Verify isolation
    assert state.entities[1].identity.known_recipes == {"a"}
    assert next_state.entities[1].identity.known_recipes == {"a", "b"}
    
    # Double check that the original set wasn't mutated in place
    assert id(state.entities[1].identity.known_recipes) != id(next_state.entities[1].identity.known_recipes)
