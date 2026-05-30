# tests/integration/scenarios/test_phase8_world_emergence_scenarios.py
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

def test_scenario_iron_scarcity_crafting():
    """Verify that resource depletion creates scarcity that exposes signals on entities."""
    regions = {"old_mine": RegionState(id="old_mine", name="Old Mine", bounds=(0, 0, 10, 10))}
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .navigation(region_id="old_mine")
              .build())
    
    state = AuthoritativeState(entities={1: entity}, regions=regions, tick=10, seed=0)
    
    events = [
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=5, region_id="old_mine", subject="iron_ore"),
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=8, region_id="old_mine", subject="iron_ore")
    ]
    
    update = StateUpdate()
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    
    # Assert scarcity was evaluated
    iron_scarcity = next(s for s in result.scarcity if s.resource_type == "iron_ore")
    assert iron_scarcity.scarcity_level >= 0.5
    
    # Assert service pressure generated for blacksmith
    bs_pressure = next(s for s in result.service_pressures if s.service_id == "blacksmith")
    assert bs_pressure.pressure_kind == "material_shortage"

def test_scenario_repeated_deaths_danger_reputation():
    """Verify repeated deaths accumulate danger pressure and expose warnings to nearby entities."""
    regions = {"north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10))}
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .navigation(region_id="north_ruin")
              .build())
    
    state = AuthoritativeState(entities={1: entity}, regions=regions, tick=10, seed=0)
    
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=5, region_id="north_ruin"),
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=8, region_id="north_ruin")
    ]
    
    update = StateUpdate()
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    
    danger = next(p for p in result.pressures if p.pressure_kind == "danger")
    assert danger.intensity > 0.2
    
    # Assert entity was exposed to signal and route reevaluation hint is enabled
    prop_up = res_upd.entity_updates[1].property_updates
    assert prop_up["force_route_reevaluation"] is True
