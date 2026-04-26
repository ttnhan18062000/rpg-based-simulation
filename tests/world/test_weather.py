import pytest
from src.core.state import RegionState, EntityState
from src.world.environment import EnvironmentService
from src.core.builder import V2EntityBuilder

def test_weather_modifiers():
    region = RegionState(
        id="reg_1", name="R1", bounds=(0,0,10,10),
        weather="STORM"
    )
    mods = EnvironmentService.get_weather_modifiers(region)
    
    assert mods["perception"] == 0.7
    assert mods["evasion"] == 0.8

def test_hazard_drain_scaling():
    region = RegionState(
        id="reg_1", name="R1", bounds=(0,0,10,10),
        hazard_level=0.5,
        calamity_intensity=1.0 # 2x multiplier
    )
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    
    drain = EnvironmentService.calculate_hazard_drain(region, entity)
    # 0.5 * (1 + 1) = 1.0
    assert drain == 1.0

def test_miasma_effect():
    region = RegionState(
        id="reg_1", name="R1", bounds=(0,0,10,10),
        hazard_level=0.2,
        active_modifiers=["MIASMA"]
    )
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    
    drain = EnvironmentService.calculate_hazard_drain(region, entity)
    # 0.2 * 1.5 = 0.3
    assert pytest.approx(drain) == 0.3
