import pytest
from src_v2.core.state import EntityState, RegionState, AuthoritativeState
from src_v2.core.strategic import StrategicComponent
from src_v2.core.updates import StateUpdate
from src_v2.engine.pipeline import AuthoritativeApplyPipeline

def test_anchored_world_persistence():
    """Verify that anchored entities return to their home region when idle."""
    # Home region at (0,0) to (2,2)
    home = RegionState(id="home", name="Home", bounds=(0, 0, 2, 2))
    # Away region at (10,10) to (12,12)
    away = RegionState(id="away", name="Away", bounds=(10, 10, 12, 12))
    
    # Entity at (11,11) but home is "home"
    hero = EntityState(id=1, kind="HERO", position=(11.0, 11.0),
                       strategic=StrategicComponent(home_region_id="home"))
    
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"home": home, "away": away},
                               entities={1: hero})
    
    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should generate a return-home concern
    ent_upd = refined.entity_updates[1]
    assert ent_upd.strategic is not None
    assert any(c.id == "concern_return_home" for c in ent_upd.strategic.concerns_add_or_update)
