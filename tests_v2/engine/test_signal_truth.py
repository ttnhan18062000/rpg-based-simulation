import pytest
import time
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
        max_queue_depth=10,
        max_replay_buffer_kb=1024,
        max_tick_budget_ms=16.6,
        max_observability_budget_percent=5.0,
        sampling_interval_ticks=1, # Sample RSS every tick for test
        confidence_window_ticks=0   # No windowing for transition tests here
    )

@pytest.fixture
def initial_state():
    return AuthoritativeState(tick=0, seed=1)

def test_signal_truth_peak_utilization(mock_profile, initial_state):
    """Verify that worker_utilization captures PEAK pressure, not idle state."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    
    kernel = Kernel(mock_profile, initial_state, rng)
    wm = kernel._worker_manager
    
    # Simulate a spiky load: 4 workers busy, then 0
    wm._active_count = 4
    wm._peak_active = 4
    
    stats = wm.get_stats()
    assert stats["worker_utilization"] == 1.0
    assert stats["active_workers"] == 4
    
    # Now simulate idle state (e.g. at the end of tick)
    wm._active_count = 0
    stats = wm.get_stats()
    assert stats["worker_utilization"] == 1.0 # Still 1.0 because of Peak accounting!
    assert stats["active_workers"] == 0
    
    # Snapshot should reflect the peak
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    assert snapshot.worker_utilization == 1.0
    assert snapshot.active_workers == 0

def test_signal_truth_rolling_compute_average(mock_profile, initial_state):
    """Verify that compute average uses a rolling 5-tick window."""
    from src_v2.platform.rng import DeterministicRNG
    from src_v2.core.governance import PressureSignals
    rng = MagicMock(spec=DeterministicRNG)
    
    kernel = Kernel(mock_profile, initial_state, rng)
    status = kernel.status
    
    # Record 10 ticks of varying compute time
    for i in range(1, 11):
        signals = PressureSignals(
            tick_compute_ms = 10.0 if i <= 5 else 20.0, 
            work_debt_total=0, worker_utilization=0, queue_utilization=0,
            memory_estimate_mb=0, replay_backlog_kb=0, active_workers=0, dropped_work_delta=0
        )
        status.record_signals(signals)
        
    # The last 5 samples are all 20.0
    # Rolling average should be 20.0, NOT the cumulative average of 15.0
    last_signals = status.signal_history[-1]
    assert last_signals.tick_compute_ms_avg == 20.0

def test_signal_truth_windowed_memory_trend(mock_profile, initial_state):
    """Verify that memory trend reflects slope over 5 samples."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    
    kernel = Kernel(mock_profile, initial_state, rng)
    collector = kernel._collector
    
    # Simulate memory growth: 100, 110, 120, 130, 140
    for i, m in enumerate([100.0, 110.0, 120.0, 130.0, 140.0]):
        # Mock psutil memory_info
        collector._process.memory_info = MagicMock(return_value=MagicMock(rss=int(m * 1024 * 1024)))
        # Use successive ticks to fill history
        stats = collector.collect_platform_signals(tick=i, interval_override=1)
        
    # After 5 samples: [100, 110, 120, 130, 140]
    # Trend = (10+10+10+10)/4 = 10.0 
    assert stats["memory_trend"] == 10.0

def test_signal_truth_dropped_work(mock_profile, initial_state):
    """Verify that dropped_work_count tracks actual scheduler shedding."""
    from src_v2.platform.rng import DeterministicRNG
    from src_v2.engine.scheduler import PeriodicDefinition
    rng = MagicMock(spec=DeterministicRNG)
    
    periodic_defs = [
        PeriodicDefinition(subsystem_id="opt_task", work_kind="OPT", cadence=1, is_authoritative=False)
    ]
    
    from src_v2.engine.scheduler import DeterministicScheduler
    scheduler = DeterministicScheduler(periodic_defs=periodic_defs)
    
    kernel = Kernel(mock_profile, initial_state, rng, scheduler=scheduler)
    kernel._status.max_total_dropped = 100
    
    # Force SURVIVAL mode
    kernel._status.current_mode = RuntimeMode.SURVIVAL
    
    # Tick once. The non-auth task should be shed.
    kernel.tick_once()
    
    assert kernel.status.total_dropped_work == 1
    
    collector = SignalCollector("test_truth")
    snapshot = collector.get_snapshot(kernel)
    assert snapshot.dropped_work_count == 1
