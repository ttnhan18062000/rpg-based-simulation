import pytest
from src.core.governance import RuntimeMode, PressureSignals
from src.engine.governor import ResourceGovernor
from src.engine.runtime_status import RuntimeStatus
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


@pytest.fixture
def base_profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_work_debt=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=16.0
    )


def test_escalation_path(base_profile):
    """Verify that mode escalates immediately with rising pressure."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # 1. Normal
    signals_normal = PressureSignals(tick_compute_ms=5.0)
    gov.evaluate(base_profile, signals_normal, status, 0)
    assert status.current_mode == RuntimeMode.NORMAL
    
    # 2. Constrained (threshold 16.0 * 0.7 = 11.2)
    signals_constrained = PressureSignals(tick_compute_ms = 12.0)
    gov.evaluate(base_profile, signals_constrained, status, 1)
    assert status.current_mode == RuntimeMode.CONSTRAINED
    
    # 3. Degraded (threshold 16.0)
    signals_degraded = PressureSignals(tick_compute_ms = 20.0)
    gov.evaluate(base_profile, signals_degraded, status, 2)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 4. Survival (threshold 16.0 * 1.5 = 24.0)
    signals_survival = PressureSignals(tick_compute_ms = 30.0)
    gov.evaluate(base_profile, signals_survival, status, 3)
    assert status.current_mode == RuntimeMode.SURVIVAL


def test_multi_signal_escalation(base_profile):
    """Verify that debt trigger also causes escalation."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # Debt threshold: 100. Degraded at 50% (50). Survival at 100% (100).
    signals = PressureSignals(work_debt_total=60)
    gov.evaluate(base_profile, signals, status, 10)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    signals_survival = PressureSignals(work_debt_total=110)
    gov.evaluate(base_profile, signals_survival, status, 11)
    assert status.current_mode == RuntimeMode.SURVIVAL


def test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure():
    """TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER: a real, uninstrumented
    Kernel run with max_worker_count=0 (matching ScenarioRuntimeService's own real construction,
    src/engine/scenario_runtime.py:395; also BROKER_DISABLED=1's real operational mode,
    src/config/loader.py:74) must start in and stay in RuntimeMode.NORMAL absent real compute
    pressure. Before the fix, WorkerManager.get_stats()'s own 1.0 sentinel for max_workers<=0 was
    read by ResourceGovernor as genuine 90%+ saturation, forcing DEGRADED unconditionally from
    tick 1 -- confirmed independent of entity count or world contents."""
    profile = RuntimeProfile(
        name="test-worker-util-zero",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=1000,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=200.0,
    )
    state = AuthoritativeState(tick=0, seed=1, world_time=0, entities={})
    rng = DeterministicRNG(1)
    kernel = Kernel(profile, state, rng, flags={"no_replay": True})
    try:
        for _ in range(5):
            kernel.tick_once()
            assert kernel.status.current_mode == RuntimeMode.NORMAL
    finally:
        kernel.shutdown()
