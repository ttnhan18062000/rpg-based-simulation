# tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py
import pytest
from src.core.state import AuthoritativeState, RegionState
from src.domains.world_emergence.schema import WorldEventAggregate, WorldEventCategory
from src.domains.world_emergence.models import RegionalPressureModel

def test_repeated_deaths_increase_danger_pressure():
    # Setup mock RegionStates to avoid KeyErrors
    regions = {"north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10))}
    state = AuthoritativeState(entities={}, regions=regions, tick=0, seed=0)
    
    aggs = (
        WorldEventAggregate(
            region_id="north_ruin",
            category=WorldEventCategory.ENTITY_DEATH,
            subject=None,
            count=3,
            severity_sum=3.0,
            first_tick=5,
            last_tick=15
        ),
    )
    
    pressures = RegionalPressureModel.evaluate(state, aggs)
    danger = next(p for p in pressures if p.pressure_kind == "danger")
    assert danger.intensity > 0.4
    assert "3 entity deaths" in danger.reason
