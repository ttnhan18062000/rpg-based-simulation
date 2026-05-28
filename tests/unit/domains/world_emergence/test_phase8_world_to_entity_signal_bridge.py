# tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.domains.world_emergence.schema import RegionalPressure, WorldEmergenceResult
from src.domains.world_emergence.services import WorldToEntitySignalBridge

def test_local_region_danger_exposes_warning_to_entity_in_region():
    # Setup regions structure
    regions = {"north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10))}
    
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .navigation(region_id="north_ruin")
              .build())
    
    state = AuthoritativeState(entities={1: entity}, regions=regions, tick=10, seed=0)
    
    signals = WorldEmergenceResult(
        pressures=(
            RegionalPressure(region_id="north_ruin", pressure_kind="danger", intensity=0.8, confidence=0.9, source_aggregates=(), reason=""),
        )
    )
    
    exposures = WorldToEntitySignalBridge.expose(entity, state, signals)
    assert len(exposures) == 1
    assert exposures[0]["signal_type"] == "danger_pressure"
    assert exposures[0]["channel"] == "direct_observation"
    assert exposures[0]["certainty"] == 0.9
