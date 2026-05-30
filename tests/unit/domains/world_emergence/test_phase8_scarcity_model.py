# tests/unit/domains/world_emergence/test_phase8_scarcity_model.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import WorldEventAggregate, WorldEventCategory
from src.domains.world_emergence.models import ScarcityModel

def test_repeated_iron_depletion_increases_old_mine_scarcity():
    state = AuthoritativeState(entities={}, tick=0, seed=0)
    aggs = (
        WorldEventAggregate(
            region_id="old_mine",
            category=WorldEventCategory.RESOURCE_DEPLETED,
            subject="iron_ore",
            count=2,
            severity_sum=2.0,
            first_tick=5,
            last_tick=15
        ),
    )
    
    signals = ScarcityModel.evaluate(state, aggs)
    iron = next(s for s in signals if s.resource_type == "iron_ore")
    assert iron.scarcity_level >= 0.5
    assert iron.availability <= 0.5
    assert iron.trend == "INCREASING"
