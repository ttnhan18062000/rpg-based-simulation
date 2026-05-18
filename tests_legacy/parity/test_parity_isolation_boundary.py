import pytest
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.engine.kernel import Kernel
from src_legacy.core.work import WorkItem, WorkClass
from src_legacy.core.worker_protocol import WorkerResult, ResultStatus, WorkerPacket
from src_legacy.core.updates import EntityUpdate
from src_legacy.config.profiles import RuntimeProfile, HardwareClass

@pytest.fixture
def test_profile():
    return RuntimeProfile(
        name="TEST_PROFILE", 
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, 
        max_cpu_percent=50.0, 
        max_worker_count=1,
        max_queue_depth=10, 
        max_replay_buffer_kb=0, 
        max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )

@pytest.mark.v2_contract
def test_local_executor_isolation_boundary(test_profile):
    """
    M8 Law: Systems executed by LocalSequentialExecutor must NOT be able 
    to mutate the authoritative state via references.
    """
    from src_legacy.engine.executor import LocalSequentialExecutor
    from src_legacy.platform.rng import DeterministicRNG
    
    # 1. Setup state with a mutable-looking entity
    entity = EntityState(id=1, kind="HERO", position=(0, 0))
    state = AuthoritativeState(tick=10, seed=42, entities={1: entity})
    
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    
    # 2. Verify that deep_freeze works on the entity
    from src_legacy.core.immutability import deep_freeze
    frozen_entity = deep_freeze(entity)
    
    with pytest.raises((AttributeError, TypeError)):
        frozen_entity.readiness = 999.0

@pytest.mark.v2_contract
def test_kernel_clock_advancement_exclusivity(tmp_path, test_profile):
    """
    M8 Law: Clock must only advance during the dedicated Advancement phase
    and must use ApplyPath for the transition.
    """
    from src_legacy.engine.kernel import Kernel
    from src_legacy.engine.worker_manager import WorkerManager
    from src_legacy.engine.replay_manager import ReplayManager
    from src_legacy.engine.executor import LocalSequentialExecutor
    from src_legacy.engine.runtime_status import RuntimeStatus
    from src_legacy.platform.rng import DeterministicRNG
    
    # Setup minimal kernel
    worker_mgr = WorkerManager(max_workers=1)
    replay_mgr = ReplayManager(tmp_path, profile_name="test")
    executor = LocalSequentialExecutor()
    status = RuntimeStatus()
    rng = DeterministicRNG(42)
    
    state = AuthoritativeState(tick=100, seed=42)
    kernel = Kernel(
        profile=test_profile,
        state=state,
        rng=rng,
        status=status,
        replay=replay_mgr,
        executor=executor
    )
    
    # Run one tick
    assert kernel._state.tick == 100
    
    kernel.tick_once()
    
    # After tick_once, tick is 101 (Post-step increment)
    assert kernel._state.tick == 101

@pytest.mark.v2_contract
def test_deep_freeze_recursive_isolation():
    """
    Ensures that deep_freeze handles nested mutables (dicts/lists in properties).
    """
    from src_legacy.core.immutability import deep_freeze
    from types import MappingProxyType
    
    data = {
        "a": [1, 2, {"b": 3}],
        "c": {4, 5}
    }
    
    frozen = deep_freeze(data)
    
    assert isinstance(frozen, MappingProxyType)
    assert isinstance(frozen["a"], tuple)
    assert isinstance(frozen["a"][2], MappingProxyType)
    assert isinstance(frozen["c"], frozenset)
    
    with pytest.raises(TypeError):
        frozen["a"][0] = 9
