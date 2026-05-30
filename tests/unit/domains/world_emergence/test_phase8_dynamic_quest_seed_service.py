# tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import WorldOpportunityPressure
from src.domains.world_emergence.services import DynamicQuestSeedService

def test_danger_pressure_generates_clear_threat_seed():
    state = AuthoritativeState(entities={}, tick=10, seed=0)
    opps = (
        WorldOpportunityPressure(
            id="opp_danger_north_ruin",
            kind="clear_threat",
            region_id="north_ruin",
            subject=None,
            urgency=0.8,
            suggested_opportunity_kinds=(),
            reason=""
        ),
    )
    
    seeds = DynamicQuestSeedService.generate(opps, state)
    assert len(seeds) == 1
    assert seeds[0].kind == "clear_threat"
    assert seeds[0].difficulty_hint >= 4
    assert seeds[0].reward_hint > 300
