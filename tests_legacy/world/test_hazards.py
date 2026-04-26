import pytest
from src_legacy.core.state import AuthoritativeState, RegionState
from src_legacy.core.updates import StateUpdate, WorldUpdate
from src_legacy.engine.apply import ApplyPath

def test_region_state_expansion():
    region = RegionState(
        id="reg_1",
        name="Test Region",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        hazard_level=0.1
    )
    state = AuthoritativeState(tick=0, seed=1, regions={"reg_1": region})
    
    # Update kind, weather, and modifiers
    world_upd = WorldUpdate(
        region_id="reg_1",
        kind_set="BURNT_FOREST",
        weather_set="STORM",
        modifiers_add=["MIASMA"]
    )
    state_upd = StateUpdate(world_updates={"reg_1": world_upd})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    new_region = new_state.regions["reg_1"]
    
    assert new_region.kind == "BURNT_FOREST"
    assert new_region.weather == "STORM"
    assert "MIASMA" in new_region.active_modifiers
    assert new_region.hazard_level == 0.1

def test_modifier_removal():
    region = RegionState(
        id="reg_1",
        name="Test Region",
        bounds=(0, 0, 100, 100),
        active_modifiers=["MIASMA", "FROST"]
    )
    state = AuthoritativeState(tick=0, seed=1, regions={"reg_1": region})
    
    world_upd = WorldUpdate(
        region_id="reg_1",
        modifiers_remove=["MIASMA"]
    )
    state_upd = StateUpdate(world_updates={"reg_1": world_upd})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    new_region = new_state.regions["reg_1"]
    
    assert "FROST" in new_region.active_modifiers
    assert "MIASMA" not in new_region.active_modifiers
