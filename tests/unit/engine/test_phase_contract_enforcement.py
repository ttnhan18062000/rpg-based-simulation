import pytest
from unittest.mock import MagicMock
from src.engine.phases.base import EnginePhase
from src.engine.phases.context import EngineContext
from src.engine.phases.contract import PhaseContract, PhaseAccess
from src.engine.phase_guard import PhaseGuard

class ViolationPhase(EnginePhase):
    """A malicious phase that tries to break its contract."""
    def __init__(self, permissions, allow_emit=True):
        self._permissions = permissions
        self._allow_emit = allow_emit
        
    @property
    def contract(self) -> PhaseContract:
        return PhaseContract(
            name="Violation",
            description="Testing contract enforcement.",
            permissions=self._permissions,
            allow_emit=self._allow_emit
        )

    def execute(self, ctx: EngineContext):
        # We'll use this phase to attempt various operations
        pass

@pytest.fixture
def base_ctx():
    return EngineContext(
        config=MagicMock(),
        world=MagicMock(),
        action_queue=MagicMock(),
        worker_pool=MagicMock(),
        conflict_resolver=MagicMock(),
        generator=MagicMock(),
        rng=MagicMock(),
        faction_reg=MagicMock(),
        system_manager=MagicMock(),
        action_system=MagicMock(),
        hero_lifecycle=MagicMock(),
        social_registry=MagicMock(),
        emit=MagicMock()
    )

def test_unauthorized_read_raises(base_ctx):
    # Phase only has permission for 'config'
    phase = ViolationPhase(permissions={"config": PhaseAccess.READ})
    
    with PhaseGuard(base_ctx, phase.contract) as guarded_ctx:
        # Valid read
        assert guarded_ctx.config is not None
        
        # Unauthorized read (world)
        with pytest.raises(RuntimeError) as excinfo:
            _ = guarded_ctx.world
        assert "attempted to READ unauthorized field 'world'" in str(excinfo.value)

def test_unauthorized_mutate_raises(base_ctx):
    # Phase has READ for world, but not MUTATE
    phase = ViolationPhase(permissions={"world": PhaseAccess.READ})
    
    with PhaseGuard(base_ctx, phase.contract) as guarded_ctx:
        # Unauthorized mutate
        with pytest.raises(RuntimeError) as excinfo:
            guarded_ctx.world = MagicMock()
        assert "attempted to MUTATE unauthorized field 'world'" in str(excinfo.value)

def test_unauthorized_emit_raises(base_ctx):
    # Phase has allow_emit=False
    phase = ViolationPhase(permissions={}, allow_emit=False)
    
    with PhaseGuard(base_ctx, phase.contract) as guarded_ctx:
        with pytest.raises(RuntimeError) as excinfo:
            guarded_ctx.emit("test", "category", (1,), {})
        assert "attempted to EMIT but 'allow_emit' is False" in str(excinfo.value)

def test_valid_mutate_works(base_ctx):
    phase = ViolationPhase(permissions={"tick_ready_entities": PhaseAccess.READ_WRITE})
    
    with PhaseGuard(base_ctx, phase.contract) as guarded_ctx:
        # Read-Write should work
        guarded_ctx.tick_ready_entities = [1, 2, 3]
        assert guarded_ctx.tick_ready_entities == [1, 2, 3]

def test_internal_field_access(base_ctx):
    # Proxy should allow access to internal fields starting with _ (for infrastructure)
    phase = ViolationPhase(permissions={})
    with PhaseGuard(base_ctx, phase.contract) as guarded_ctx:
        # Assuming we eventually add some _ fields to context
        # For now, proxy allows it by default if they exist in ctx
        base_ctx._test = "internal"
        assert guarded_ctx._test == "internal"
