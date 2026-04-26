import pytest
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.updates import StateUpdate
import dataclasses

def test_readonly_state_immutability():
    """
    Z12: Phase guard prevents decision logic from mutating authoritative state.
    """
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: EntityState(id=1, kind="hero", position=(0,0))
    })
    
    # AI or Worker requests a read-only view
    ro_state = state.readonly_view()
    
    # Attempting to modify a top-level dictionary should fail due to mappingproxy
    with pytest.raises((TypeError, AttributeError)):
        ro_state.entities[2] = EntityState(id=2, kind="monster", position=(1,1))
        
    # Attempting to clear it should fail
    with pytest.raises((TypeError, AttributeError)):
        ro_state.entities.clear()

def test_unauthorized_write_fails():
    """
    Z12: Direct writes to the state bypass the ApplyPath and must be prevented.
    """
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: EntityState(id=1, kind="hero", position=(0,0))
    })
    
    # The state object itself uses frozen dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.tick = 2
        
    entity = state.entities[1]
    with pytest.raises(dataclasses.FrozenInstanceError):
        entity.position = (5, 5)
        
    with pytest.raises(dataclasses.FrozenInstanceError):
        entity.combat.hp = 999
