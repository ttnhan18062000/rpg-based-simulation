import pytest
from src_v2.core.governance import RuntimeMode, PressureSignals
from src_v2.engine.governor import ResourceGovernor
from src_v2.engine.runtime_status import RuntimeStatus
from src_v2.config.profiles import RuntimeProfile, HardwareClass


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
    gov = ResourceGovernor(dwell_time=10)
    status = RuntimeStatus()
    
    # 1. Normal
    signals_normal = PressureSignals(tick_compute_ms=5.0)
    gov.evaluate(base_profile, signals_normal, status)
    assert status.current_mode == RuntimeMode.NORMAL
    
    # 2. Constrained (threshold 16.0 * 0.7 = 11.2)
    signals_constrained = PressureSignals(tick_compute_ms = 12.0)
    gov.evaluate(base_profile, signals_constrained, status)
    assert status.current_mode == RuntimeMode.CONSTRAINED
    
    # 3. Degraded (threshold 16.0)
    signals_degraded = PressureSignals(tick_compute_ms = 20.0)
    gov.evaluate(base_profile, signals_degraded, status)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 4. Survival (threshold 16.0 * 1.5 = 24.0)
    signals_survival = PressureSignals(tick_compute_ms = 30.0)
    gov.evaluate(base_profile, signals_survival, status)
    assert status.current_mode == RuntimeMode.SURVIVAL


def test_multi_signal_escalation(base_profile):
    """Verify that debt trigger also causes escalation."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # Debt threshold: 100. Degraded at 50% (50). Survival at 100% (100).
    signals = PressureSignals(work_debt_total=60)
    gov.evaluate(base_profile, signals, status)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    signals_survival = PressureSignals(work_debt_total=110)
    gov.evaluate(base_profile, signals_survival, status)
    assert status.current_mode == RuntimeMode.SURVIVAL
