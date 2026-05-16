import pytest
from src.core.state import AuthoritativeState, EntityState, NavigationComponent
from src.core.builder import V2EntityBuilder
from src.engine.apply import ApplyPath
from src.engine.legality import LegalityServiceV2
from src.core.updates import StateUpdate, EntityUpdate

def test_entity_identity_preservation_passive():
    """Verify that entity objects are reused if no passive changes occur."""
    e1 = V2EntityBuilder(1).location(10, 10).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    
    # Tick with NO changes (using high cadence to avoid staggered updates)
    from src.engine.cadence import SystemCadence
    high_cadence = SystemCadence(biological=100, lifecycle=100, strategic_intelligence=100)
    new_state = ApplyPath.apply_passive(state, cadence=high_cadence)
    
    assert new_state.entities[1] is e1, "Entity identity should be preserved when no changes occur"

def test_authoritative_state_readonly_cache_reuse():
    """Verify that to_readonly() reuses the cache if state is already readonly."""
    e1 = V2EntityBuilder(1).location(10, 10).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    
    view1 = state.to_readonly()
    view2 = view1.to_readonly()
    
    assert view1 is view2, "to_readonly() should be idempotent and reuse cache"

def test_navigation_region_id_caching():
    """Verify that region_id is cached and updated correctly in NavigationComponent."""
    # This test will fail until we implement the caching logic
    from src.core.state import RegionState
    r1 = RegionState(id="r1", name="R1", bounds=(0, 0, 10, 10))
    r2 = RegionState(id="r2", name="R2", bounds=(10.1, 0, 20, 10))
    
    e1 = V2EntityBuilder(1).location(5, 5).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1}, regions={"r1": r1, "r2": r2})
    
    # 1. Initial passive pass should set the region_id
    state_p1 = ApplyPath.apply_passive(state)
    assert state_p1.entities[1].navigation.region_id == "r1"
    
    # 2. Move entity to r2
    e1_moved = (V2EntityBuilder(1)
                .location(15, 5)
                .build())
    state2 = AuthoritativeState(tick=2, seed=42, entities={1: e1_moved}, regions={"r1": r1, "r2": r2})
    
    state_p2 = ApplyPath.apply_passive(state2)
    assert state_p2.entities[1].navigation.region_id == "r2"

def test_has_line_of_sight_parity():
    """Verify that LoS parity is maintained between O(N) and O(1) implementations."""
    from src.core.state import BuildingState
    b1 = BuildingState(id=101, position=(5.0, 5.0), kind="wall")
    state = AuthoritativeState(
        tick=1, seed=42, 
        buildings={101: b1},
        building_tiles={(5, 5): "wall"}
    )
    
    # LoS blocked by building at (5,5)
    # Path: (0,5) to (10,5) passes through (5,5)
    assert not LegalityServiceV2.has_line_of_sight((0.0, 5.0), (10.0, 5.0), state)
    
    # LoS clear
    assert LegalityServiceV2.has_line_of_sight((0.0, 0.0), (10.0, 0.0), state)

def test_apply_partial_lazy_dict_parity():
    """Verify that apply_partial behaves identically with lazy dict optimization."""
    e1 = V2EntityBuilder(1).location(10, 10).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    
    # 1. No updates
    upd_empty = StateUpdate()
    state_no_upd = ApplyPath.apply_partial(state, upd_empty)
    assert state_no_upd.entities is state.entities
    
    # 2. Real update
    upd_real = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=(11, 11))})
    state_upd = ApplyPath.apply_partial(state, upd_real)
    assert state_upd.entities is not state.entities
    assert state_upd.entities[1].navigation.position == (11, 11)
