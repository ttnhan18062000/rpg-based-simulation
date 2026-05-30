# tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import RegionalPressure, ResourceScarcitySignal
from src.domains.world_emergence.services import RumorSeedService

def test_danger_pressure_generates_low_certainty_rumor():
    state = AuthoritativeState(entities={}, tick=10, seed=0)
    pressures = (
        RegionalPressure(region_id="north_ruin", pressure_kind="danger", intensity=0.8, confidence=0.9, source_aggregates=(), reason="deaths reported"),
    )
    scarcity = ()
    
    seeds = RumorSeedService.generate(pressures, scarcity, state)
    assert len(seeds) == 1
    assert seeds[0].subject == "regional_danger"
    assert seeds[0].certainty == 0.5
