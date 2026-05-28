# tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py
import pytest
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import RegionalPressure, ResourceScarcitySignal
from src.domains.world_emergence.models import ServiceStatePressureModel

def test_iron_scarcity_creates_blacksmith_material_pressure():
    state = AuthoritativeState(entities={}, tick=0, seed=0)
    pressures = ()
    scarcity = (
        ResourceScarcitySignal(region_id="old_mine", resource_type="iron_ore", availability=0.1, scarcity_level=0.9, trend="STABLE", confidence=0.9, reason=""),
    )
    
    services = ServiceStatePressureModel.evaluate(pressures, scarcity, state)
    bs = next(s for s in services if s.service_id == "blacksmith")
    assert bs.pressure_kind == "material_shortage"
    assert bs.intensity >= 0.7
