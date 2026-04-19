import pytest
from unittest.mock import MagicMock
from src_v2.engine.observability import SignalCollector
from src_v2.engine.kernel import Kernel
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.state import AuthoritativeState
from src_v2.core.governance import RuntimeMode

@pytest.fixture
def mock_profile():
    return RuntimeProfile(
        name="test_truth",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_tick_budget_ms=16.6,
        max_observability_budget_percent=5.0
    )

@pytest.fixture
def initial_state():
    return AuthoritativeState(tick=0, seed=1)

def test_signal_truth_worker_utilization(mock_profile, initial_state):
    """Verify that capacity_utilization is real and not a placeholder."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    
    kernel = Kernel(mock_profile, initial_state, rng)
    
    # Force some 'inflight' count in the worker manager
    # We use the explicit interface we just added
    kernel._worker_manager._inflight_count = 50 # Manually simulating load for test
    
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    
    # util = 50 / 100 = 0.5
    assert snapshot.capacity_utilization == 0.5
    assert snapshot.active_workers == 50
    assert snapshot.capacity_utilization > 0 # Prove it's not a placeholder 0.0

def test_signal_truth_replay_backlog(mock_profile, initial_state):
    """Verify that replay_backlog_kb is real and sourced from the buffer."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    
    kernel = Kernel(mock_profile, initial_state, rng)
    
    # Simulate replay backlog
    # ReplayBuffer item_count -> backlog_kb (items // 4)
    kernel._replay._buffer._buffer.append(MagicMock()) # 1 item
    kernel._replay._buffer._buffer.append(MagicMock()) # 2 items
    kernel._replay._buffer._buffer.append(MagicMock()) # 3 items
    kernel._replay._buffer._buffer.append(MagicMock()) # 4 items -> 1 KB
    
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    
    assert snapshot.replay_backlog_kb == 1
    assert snapshot.replay_backlog_kb > 0 # Prove it's not a placeholder 0

def test_signal_truth_dropped_work(mock_profile, initial_state):
    """Verify that dropped_work_count tracks actual scheduler shedding."""
    from src_v2.platform.rng import DeterministicRNG
    from src_v2.engine.scheduler import PeriodicDefinition
    rng = MagicMock(spec=DeterministicRNG)
    
    # Add a non-authoritative periodic task that will be shed in SURVIVAL
    periodic_defs = [
        PeriodicDefinition(subsystem_id="opt_task", work_kind="OPT", cadence=1, is_authoritative=False)
    ]
    
    from src_v2.engine.scheduler import DeterministicScheduler
    scheduler = DeterministicScheduler(periodic_defs=periodic_defs)
    
    kernel = Kernel(mock_profile, initial_state, rng, scheduler=scheduler)
    
    # Force SURVIVAL mode
    kernel._status.current_mode = RuntimeMode.SURVIVAL
    
    # Tick once. The non-auth task should be shed.
    kernel.tick_once()
    
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    
    assert snapshot.dropped_work_count == 1
    assert kernel.status.total_dropped_work == 1

def test_signal_truth_work_debt(mock_profile, initial_state):
    """Verify that work_debt_total is real sum of authoritative state debt."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    
    # Add some debt to state
    initial_state.work_debt["sub1"] = 10
    initial_state.work_debt["sub2"] = 5
    
    kernel = Kernel(mock_profile, initial_state, rng)
    
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    
    assert snapshot.work_debt_total == 15
