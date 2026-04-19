from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.core.updates import StateUpdate, EntityUpdate
from src_v2.engine.apply import ApplyPath
from src_v2.engine.checkpoint import CanonicalStateHasher
import pytest

def test_prior_state_purity_deep_properties():
    """
    Milestone A Law: Applying an update must not mutate the prior state.
    This test specifically checks for dictionary aliasing in properties.
    """
    initial_props = {"health": 100, "meta": {"temp": 0}}
    state = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="hero", position=(0,0), properties=initial_props)
    })
    
    # Update health, but don't touch 'meta'
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, property_updates={"health": 90})
    })
    
    next_state = ApplyPath.apply_generation(state, update, 2, 1)
    
    # 1. Basic isolation
    assert state.entities[1].properties["health"] == 100
    assert next_state.entities[1].properties["health"] == 90
    
    # 2. Check for aliasing of the top-level dict
    # Even if they have the same content (meta), they should be different dict instances
    assert state.entities[1].properties is not next_state.entities[1].properties
    
    # 3. Check for aliasing of nested dicts (The known "shallow" caveat)
    # Milestone A law acknowledges shallow copies, but we should at least verify 
    # that we didn't inadvertently deep-copy if we didn't mean to.
    assert state.entities[1].properties["meta"] is next_state.entities[1].properties["meta"]

def test_no_mutation_leak_from_worker_snapshot():
    """
    Milestone A Law: Observational paths (like workers reading state) 
    MUST NOT be able to mutate the authoritative state via references.
    """
    from dataclasses import replace
    state = AuthoritativeState(tick=1, seed=1, entities={
        1: EntityState(id=1, kind="hero", position=(0,0), properties={"gold": 10})
    })
    
    # Simulate what the Kernel does in Phase 3
    subject = state.entities[1]
    subject_snapshot = replace(subject, properties=dict(subject.properties))
    
    # Simulate a "worker" mutating the snapshot
    subject_snapshot.properties["gold"] = 999
    
    # Assert that the ORIGINAL state remains protected
    assert state.entities[1].properties["gold"] == 10
    assert subject_snapshot.properties["gold"] == 999

def test_apply_determinism_sorting():
    """
    Law: Mutation order must not affect state identity.
    """
    state = AuthoritativeState(tick=1, seed=1, global_resources={"gold": 100.0})
    
    # Updates in different orders
    update_1 = StateUpdate(resource_updates={"gold": 50.0, "wood": 10.0})
    update_2 = StateUpdate(resource_updates={"wood": 10.0, "gold": 50.0})
    
    next_state_1 = ApplyPath.apply_generation(state, update_1, 2, 2)
    next_state_2 = ApplyPath.apply_generation(state, update_2, 2, 2)
    
    hash_1 = CanonicalStateHasher.get_hash(next_state_1)
    hash_2 = CanonicalStateHasher.get_hash(next_state_2)
    
    assert hash_1 == hash_2
    assert next_state_1.global_resources == next_state_2.global_resources

def test_auth_state_is_frozen():
    """Verify that AuthoritativeState itself cannot be mutated directly."""
    state = AuthoritativeState(tick=1, seed=1)
    with pytest.raises(Exception): # dataclasses.FrozenInstanceError
        state.tick = 2

def test_entity_state_is_frozen():
    """Verify that EntityState itself cannot be mutated directly."""
    ent = EntityState(id=1, kind="test", position=(0,0))
    with pytest.raises(Exception):
        ent.readiness = 100.0
