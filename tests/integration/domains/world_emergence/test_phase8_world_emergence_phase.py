# tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

def test_phase_respects_feature_flag():
    # Use AuthoritativeState params or periodic_due_ticks representation for feature disabling to avoid direct mutations
    state = AuthoritativeState(entities={}, tick=0, seed=0, periodic_due_ticks={"world_emergence_disabled"})
    
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=5, region_id="north_ruin")
    ]
    
    # We must adjust WorldEmergencePhase to look at periodic_due_ticks or state parameters carefully
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    assert len(result.pressures) == 0

def test_phase_outputs_world_signals_not_direct_entity_action():
    regions = {"north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10))}
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .navigation(region_id="north_ruin")
              .build())
    state = AuthoritativeState(entities={1: entity}, regions=regions, tick=10, seed=0)
    
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=5, region_id="north_ruin", severity=2.0)
    ]
    
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    
    # Assert signals are exposed subjectively on entities updates property updates, instead of raw mutations
    assert 1 in res_upd.entity_updates
    prop_up = res_upd.entity_updates[1].property_updates
    assert "exposed_world_signals" in prop_up
    assert prop_up["exposed_world_signals"][0]["signal_type"] == "danger_pressure"
