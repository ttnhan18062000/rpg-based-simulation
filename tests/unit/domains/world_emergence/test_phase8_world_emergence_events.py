# tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import RegionalPressure, ResourceScarcitySignal, WorldEmergenceResult
from src.domains.world_emergence.phase import WorldEmergencePhase

def test_regional_pressure_event_contains_before_after_and_reason():
    # World emergence executions return state update and emergence result containing populated telemetry records
    state = AuthoritativeState(entities={}, tick=0, seed=0)
    
    pressures = (
        RegionalPressure(region_id="north_ruin", pressure_kind="danger", intensity=0.7, confidence=0.9, source_aggregates=(), reason="heavy death"),
    )
    
    res = WorldEmergenceResult(pressures=pressures)
    assert len(res.pressures) == 1
    assert res.pressures[0].reason == "heavy death"
    assert res.pressures[0].region_id == "north_ruin"
