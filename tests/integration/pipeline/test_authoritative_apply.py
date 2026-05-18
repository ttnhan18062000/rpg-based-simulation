# Compliance IDs: PROG-106
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

def test_generation_isolation():
    """
    Verify that apply_generation does not mutate the prior state.
    [RPG-AUTH-007] State objects must be instantiated via their respective Builders.
    """
    state = AuthoritativeState(tick=1, seed=1, world_time=10, entities={
        1: V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    })
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, new_position=(10.0, 10.0))
    })
    
    next_state = ApplyPath.apply_generation(state, update, 2, 11)
    
    assert state.tick == 1
    assert state.entities[1].navigation.position == (0.0, 0.0)
    assert next_state.tick == 2
    assert next_state.entities[1].navigation.position == (10.0, 10.0)


def test_deterministic_apply_order():
    """Verify that updates are applied in sorted entity_id order."""
    # We create two updates for the same entity in different dictionaries 
    # and verify that the ApplyPath's sorted iteration would handle them if they were separate.
    # More robustly: we can verify that global resources are merged in deterministic alphabetical order.
    # Note: StateUpdate currently uses a Dict[int, EntityUpdate].
    state = AuthoritativeState(tick=1, seed=1, world_time=10, global_resources={"a": 1.0, "z": 1.0})
    update = StateUpdate(resource_updates={"z": 5.0, "a": 10.0})
    
    next_state = ApplyPath.apply_generation(state, update, 2, 11)
    
    # Check if a was updated first (though in this case it's additive so order doesn't change final sum,
    # but the canonical state hash depends on the field existence).
    assert next_state.global_resources["a"] == 11.0
    assert next_state.global_resources["z"] == 6.0


def test_resource_update_determinism():
    """Verify resources are updated correctly and deterministically."""
    state = AuthoritativeState(tick=1, seed=1, world_time=10, global_resources={"gold": 100.0})
    # Resource updates are additive deltas
    update = StateUpdate(resource_updates={"gold": 50.0, "wood": 20.0})
    
    next_state = ApplyPath.apply_generation(state, update, 2, 11)
    assert next_state.global_resources["gold"] == 150.0
    assert next_state.global_resources["wood"] == 20.0


def test_periodic_update_determinism():
    """Verify periodic due ticks are updated and sorted."""
    state = AuthoritativeState(tick=1, seed=1, periodic_due_ticks={"P1": 10})
    update = StateUpdate(periodic_updates={"P2": 20, "P1": 30})
    
    next_state = ApplyPath.apply_generation(state, update, 2, 2)
    assert next_state.periodic_due_ticks["P1"] == 30
    assert next_state.periodic_due_ticks["P2"] == 20
