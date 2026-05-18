import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, ResourceNodeState
from src.core.dirty import DirtySet, DirtySetLeakError
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL as SimulationProfile
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, ResourceNodeUpdate
from src.engine.apply import ApplyPath

@pytest.fixture
def base_state():
    return AuthoritativeState(tick=0, seed=42)

@pytest.fixture
def kernel_with_audit(base_state):
    rng = DeterministicRNG(42)
    return Kernel(SimulationProfile, base_state, rng, flags={"audit_dirty_set": True})

def add_entity(state, entity):
    new_ents = dict(state.entities)
    new_ents[entity.id] = entity
    return replace(state, entities=new_ents)

def test_dirty_set_exhaustive_movement(kernel_with_audit):
    """Verify that entity movement is correctly tracked in DirtySet."""
    state = kernel_with_audit._state
    ent = V2EntityBuilder(1).location(10, 10).build()
    state = add_entity(state, ent)
    kernel_with_audit._state = state
    
    # 1. Create a movement update
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(11, 11))})
    
    # 2. Derive DirtySet
    update = replace(update, dirty_set=DirtySet.from_update(state, update))
    
    # 3. Apply and verify no leak error
    new_state = ApplyPath.apply_generation(state, update, audit_dirty_set=True)
    assert 1 in update.dirty_set.movement_entities
    assert 1 in update.dirty_set.all_dirty_entities

def test_dirty_set_catch_shadow_mutation(base_state):
    """Verify that a mutation NOT in DirtySet triggers DirtySetLeakError."""
    ent = V2EntityBuilder(1).location(10, 10).build()
    state = add_entity(base_state, ent)
    
    # 1. Create an update that mutates the entity but does NOT set the dirty flag
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(11, 11))})
    
    # Manually create a leaking dirty set (missing entity 1)
    leaking_dirty = DirtySet()
    
    with pytest.raises(DirtySetLeakError) as excinfo:
        ApplyPath.apply_generation(state, replace(update, dirty_set=leaking_dirty), audit_dirty_set=True)
    
    assert "Entity 1 changed but not in DirtySet" in str(excinfo.value)
    assert "navigation" in str(excinfo.value)

def test_dirty_set_incremental_merge():
    """Verify that multiple refreshes correctly merge sets."""
    state = AuthoritativeState(tick=0, seed=42)
    ent = V2EntityBuilder(1).location(10, 10).build()
    state = add_entity(state, ent)
    
    # Phase 1: Combat change
    u1 = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-10))})
    d1 = DirtySet.from_update(state, u1)
    assert 1 in d1.combat_entities
    assert 1 not in d1.movement_entities
    
    # Phase 2: Movement change
    u2 = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(12, 12))})
    d2 = DirtySet.from_update(state, u2)
    assert 1 in d2.movement_entities
    
    # Merge
    merged = d1.merge(d2)
    assert 1 in merged.combat_entities
    assert 1 in merged.movement_entities
    assert 1 in merged.all_dirty_entities

def test_dirty_set_exhaustive_world_objects(base_state):
    """Verify that resource nodes and other world objects are tracked."""
    node = ResourceNodeState(
        id=1, kind="WOOD", position=(5, 5), 
        yields_item="wood_log", remaining_charges=10, 
        max_charges=10, required_ticks=5
    )
    new_nodes = dict(base_state.resource_nodes)
    new_nodes[node.id] = node
    state = replace(base_state, resource_nodes=new_nodes)
    
    update = StateUpdate(node_updates={1: ResourceNodeUpdate(node_id=1, charges_delta=-1)})
    
    dirty = DirtySet.from_update(state, update)
    assert 1 in dirty.resource_node_ids
    
    # Should pass audit
    ApplyPath.apply_generation(state, replace(update, dirty_set=dirty), audit_dirty_set=True)
    
    # Leak test
    with pytest.raises(DirtySetLeakError):
        ApplyPath.apply_generation(state, replace(update, dirty_set=DirtySet()), audit_dirty_set=True)
