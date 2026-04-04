import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src.engine.phases.context import EngineContext
from src.engine.phases.contract import PhaseContract, PhaseAccess
from src.engine.phase_guard import PhaseGuard

class MockContext:
    def __init__(self):
        self.world = "world_data"
        self.config = "config_data"
        self.other = "other_data"

@pytest.fixture
def engine_context():
    return MockContext()

def test_phase_guard_read_unauthorized(engine_context, caplog):
    contract = PhaseContract(
        name="TestRead",
        description="Testing unauthorized read access",
        permissions={
            "world": PhaseAccess.READ
        }
    )
    
    with PhaseGuard(engine_context, contract) as guarded:
        # Authorized READ
        assert guarded.world == "world_data"
        
        # Unauthorized READ (should log warning for now)
        data = guarded.config
        assert data == "config_data"
        assert "Phase 'TestRead' attempted to READ unauthorized field 'config'" in caplog.text

def test_phase_guard_mutate_unauthorized(engine_context):
    contract = PhaseContract(
        name="TestMutate",
        description="Testing unauthorized mutation",
        permissions={
            "world": PhaseAccess.READ
        }
    )
    
    with PhaseGuard(engine_context, contract) as guarded:
        # Unauthorized MUTATE (should raise RuntimeError)
        with pytest.raises(RuntimeError) as excinfo:
            guarded.world = "new_world"
        assert "Phase 'TestMutate' attempted to MUTATE unauthorized field 'world'" in str(excinfo.value)

def test_phase_guard_mutate_authorized(engine_context):
    contract = PhaseContract(
        name="TestMutateOK",
        description="Testing authorized mutation",
        permissions={
            "world": PhaseAccess.READ_WRITE
        }
    )
    
    with PhaseGuard(engine_context, contract) as guarded:
        # Authorized MUTATE
        guarded.world = "new_world"
        assert engine_context.world == "new_world"

def test_phase_guard_nested_access(engine_context):
    # Ensure the proxy doesn't block access to attributes of attributes
    # unless we specifically wanted deep-guarding (which we don't for now)
    engine_context.world = MockContext() # Nested
    engine_context.world.world = "inner_world"
    
    contract = PhaseContract(
        name="TestNested",
        description="Testing nested access",
        permissions={
            "world": PhaseAccess.READ
        }
    )
    
    with PhaseGuard(engine_context, contract) as guarded:
        # This is a READ on guarded.world (authorized)
        # The subsequent .world is on the UNGUARDED object returned by guarded.world
        assert guarded.world.world == "inner_world"
