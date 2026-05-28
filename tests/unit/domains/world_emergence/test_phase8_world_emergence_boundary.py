# tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py
import pytest
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

def test_world_emergence_service_does_not_mutate_state_directly():
    state = AuthoritativeState(entities={}, tick=10, seed=0)
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=5, region_id="north_ruin")
    ]
    
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    
    # State remains unmutated
    assert state.tick == 10
    assert len(state.entities) == 0

def test_world_emergence_consumes_recent_events():
    regions = {
        "north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10)),
        "old_mine": RegionState(id="old_mine", name="Old Mine", bounds=(0, 0, 10, 10))
    }
    state = AuthoritativeState(entities={}, regions=regions, tick=20, seed=0)
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=15, region_id="north_ruin"),
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=18, region_id="old_mine", subject="iron_ore")
    ]
    
    _, result = WorldEmergencePhase.execute(state, update, events)
    assert len(result.pressures) > 0
    assert len(result.scarcity) > 0

def test_world_emergence_is_deterministic():
    regions = {
        "north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10)),
        "old_mine": RegionState(id="old_mine", name="Old Mine", bounds=(0, 0, 10, 10))
    }
    state = AuthoritativeState(entities={}, regions=regions, tick=20, seed=0)
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=15, region_id="north_ruin"),
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=18, region_id="old_mine", subject="iron_ore")
    ]
    
    _, r1 = WorldEmergencePhase.execute(state, update, events)
    _, r2 = WorldEmergencePhase.execute(state, update, events)
    
    assert len(r1.pressures) == len(r2.pressures)
    assert r1.pressures[0].intensity == r2.pressures[0].intensity
