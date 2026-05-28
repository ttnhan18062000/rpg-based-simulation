# tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import RegionalPressure, ResourceScarcitySignal
from src.domains.world_emergence.services import WorldOpportunityPressureService

def test_danger_pressure_creates_clear_threat_opportunity():
    state = AuthoritativeState(entities={}, tick=0, seed=0)
    pressures = (
        RegionalPressure(region_id="north_ruin", pressure_kind="danger", intensity=0.7, confidence=0.9, source_aggregates=(), reason=""),
    )
    scarcity = ()
    
    opps = WorldOpportunityPressureService.evaluate(pressures, scarcity, state)
    
    assert len(opps) == 1
    assert opps[0].kind == "clear_threat"
    assert opps[0].urgency == 0.7
