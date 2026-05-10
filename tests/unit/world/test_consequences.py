import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState, LocalScarState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath

def test_scar_addition_and_recovery():
    # Initial state with one region and no scars
    region = RegionState(id="forest", name="Whispering Woods", bounds=(0, 0, 100, 100), trauma_score=1.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region},
        local_scars={}
    )
    
    # 1. Add a scar via update
    scar = LocalScarState(id=1, position=(50, 50), kind="BATTLE_FIELD", severity=1.0, created_tick=100)
    update = StateUpdate(scars_add_or_update=[scar])
    
    state_v2 = ApplyPath.apply_generation(state, update, next_tick=101)
    
    # In state_v2:
    # - LocalScar 1 is added AFTER recovery process, so severity is 1.0
    # - Region "forest" was in prior_state, so it recovered once: 1.0 -> 0.9995
    assert 1 in state_v2.local_scars
    assert state_v2.local_scars[1].severity == 1.0
    assert state_v2.regions["forest"].trauma_score == pytest.approx(0.9995)
    
    # 2. Advance one tick with no updates -> Scar and Region should recover
    state_v3 = ApplyPath.apply_generation(state_v2, StateUpdate(), next_tick=102)
    
    # In state_v3:
    # - LocalScar 1 recovers once: 1.0 -> 0.9995
    # - Region "forest" recovers again: 0.9995 -> 0.9990
    assert state_v3.local_scars[1].severity == pytest.approx(0.9995)
    assert state_v3.regions["forest"].trauma_score == pytest.approx(0.9990)

def test_scar_removal_on_full_recovery():
    # Scar with very low severity
    # It will recover to 0.0099 (which is < 0.01 threshold for removal)
    scar = LocalScarState(id=1, position=(50, 50), kind="BATTLE_FIELD", severity=0.0104, created_tick=100)
    state = AuthoritativeState(
        tick=101,
        seed=42,
        regions={"forest": RegionState(id="forest", name="Woods", bounds=(0,0,10,10))},
        local_scars={1: scar}
    )
    
    # One tick recovery (0.0005) -> severity 0.0099 (< 0.01)
    state_v2 = ApplyPath.apply_generation(state, StateUpdate(), next_tick=102)
    
    # Scar should be removed
    assert 1 not in state_v2.local_scars

def test_regional_stability_recovery():
    region = RegionState(id="town", name="Town", bounds=(0, 0, 10, 10), stability=0.5)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"town": region}
    )
    
    # Advance tick -> stability should increase (0.0001)
    state_v2 = ApplyPath.apply_generation(state, StateUpdate(), next_tick=101)
    assert state_v2.regions["town"].stability == pytest.approx(0.5001)
