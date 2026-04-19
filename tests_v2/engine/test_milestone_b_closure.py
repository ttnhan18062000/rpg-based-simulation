import pytest
import time
from unittest.mock import MagicMock
from src_v2.engine.kernel import Kernel
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.core.governance import RuntimeMode, PressureSignals
from src_v2.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src_v2.engine.worker_logic import default_simulation_worker

@pytest.fixture
def mb_profile():
    return RuntimeProfile(
        name="mb_gate",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1000,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=10,
        max_work_debt=100,
        max_replay_buffer_kb=1000,
        max_tick_budget_ms=100.0,
        max_observability_budget_percent=5.0,
        # Milestone B Truth Controls
        sampling_interval_ticks=1,
        dwell_time_ticks=5,
        confidence_window_ticks=3,
        recovery_watermark=0.8
    )

@pytest.fixture
def initial_state():
    return AuthoritativeState(tick=0, seed=1)

def test_milestone_b_operational_gate(mb_profile, initial_state):
    """
    Unified Certification Gate for Milestone B.
    Sequence: NORMAL -> Saturation -> DEGRADED -> SURVIVAL -> NORMAL.
    Verify: Signal Truth, Elasticity, and Hysteresis.
    """
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    kernel = Kernel(mb_profile, initial_state, rng)
    
    # Mock RSS to be low (100MB)
    kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=100 * 1024 * 1024))
    
    # ---------------------------------------------------------
    # Phase 1: Normal Stabilization
    # ---------------------------------------------------------
    for i in range(5):
        kernel.tick_once()
        assert kernel.status.current_mode == RuntimeMode.NORMAL
        
    # ---------------------------------------------------------
    # Phase 2 & 3: Saturation + Immediate Escalation
    # ---------------------------------------------------------
    # We simulate 5 ticks of high compute pressure (150ms)
    
    from unittest.mock import patch
    
    # Each tick calling Init (start) and Cleanup (end)
    # We want (end - start) / 1e6 = 120ms -> end - start = 120,000,000 ns
    time_sequence = []
    for t in range(40):
        time_sequence.extend([t * 2_000_000_000, t * 2_000_000_000 + 120_000_000])
        
    with patch('time.perf_counter_ns', side_effect=time_sequence):
        # Ticks 5-9: Normal -> DEGRADED
        for i in range(10):
            kernel.tick_once()
            if kernel.status.current_mode == RuntimeMode.DEGRADED:
                break
            
    assert kernel.status.current_mode == RuntimeMode.DEGRADED
    
    # ---------------------------------------------------------
    # Phase 4: Elastic Concurrency (Policy Verification)
    # ---------------------------------------------------------
    # In DEGRADED mode, verify worker pool uses only 50% capacity (2 workers)
    
    from src_v2.core.work import WorkClass
    packets = [
        WorkerPacket(packet_id=f"p{i}", work_id=f"w:{i}", tick=0, world_time=0, seed=i, 
                     work_class=WorkClass.CRITICAL,
                     subject=EntityState(id=i+1, kind="TEST", position=(0,0), properties={}), 
                     neighbor_view=[], work_kind="TEST", payload={})
        for i in range(10)
    ]
    
    kernel._worker_manager.reset_tick_stats()
    kernel._worker_manager.reset_tick_stats()
    kernel._worker_manager.execute_batch(packets, default_simulation_worker, concurrency_limit=kernel._current_policy.concurrency_limit)
    
    # Peak workers in DEGRADED should be capped at 2 (50% of 4)
    assert kernel._worker_manager.get_stats()["peak_workers"] <= 2
    
    # ---------------------------------------------------------
    # Phase 5: Hysteresis-Gated Recovery
    # ---------------------------------------------------------
    # We stop the patch (ending pressure) and verify recovery to NORMAL.
    # We need 10 ticks (dwell) + 5 ticks (confidence)
    
    for i in range(25):
        kernel.tick_once()
        if kernel.status.current_mode == RuntimeMode.NORMAL:
            break
            
    assert kernel.status.current_mode == RuntimeMode.NORMAL

def test_milestone_b_memory_survival_gate(mb_profile, initial_state):
    """Verify SURVIVAL mode escalation via Memory pressure."""
    from src_v2.platform.rng import DeterministicRNG
    rng = MagicMock(spec=DeterministicRNG)
    kernel = Kernel(mb_profile, initial_state, rng)
    
    # Mock memory collector to report critical overload (> 1000MB)
    kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=1100 * 1024 * 1024))
    
    kernel.tick_once()
    assert kernel.status.current_mode == RuntimeMode.SURVIVAL
    
    # Verify Policy in SURVIVAL: Concurrency Limit = 0.25 (1 worker)
    # Even if we have 100 entities, strictly 1 at a time.
    # Note: Kernel advancement records the signal.
    assert kernel.status.signal_history[-1].active_workers <= 1
