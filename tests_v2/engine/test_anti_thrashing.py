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
        max_tick_budget_ms=10.0 # Small threshold for easy tests
    )


def test_recovery_dwell_time(base_profile):
    """Verify that recovery is blocked until dwell time expires."""
    dwell = 5
    gov = ResourceGovernor(dwell_time=dwell)
    status = RuntimeStatus()
    
    # 1. Escalate to DEGRADED (Threshold is 10.0; Survival is 15.0)
    signals_hi = PressureSignals(tick_compute_ms = 12.0)
    gov.evaluate(base_profile, signals_hi, status)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 2. Pressure drops to NORMAL level
    signals_lo = PressureSignals(tick_compute_ms = 2.0)
    
    # Evaluate for dwell-1 ticks
    for _ in range(dwell - 1):
        gov.evaluate(base_profile, signals_lo, status)
        # Should stay in DEGRADED due to dwell time
        assert status.current_mode == RuntimeMode.DEGRADED
        
    # 3. Final tick(s) satisfy dwell time
    gov.evaluate(base_profile, signals_lo, status) # Dwell reaches 5
    gov.evaluate(base_profile, signals_lo, status) # Recovery happens
    # Recovery should happen (to CONSTRAINED first, as we recovery one level at a time)
    assert status.current_mode == RuntimeMode.CONSTRAINED


def test_low_watermark_blocking(base_profile):
    """Verify that recovery is blocked if signals are not below watermark."""
    gov = ResourceGovernor(dwell_time=0, recovery_watermark=0.5) # Dwell 0, Watermark 50%
    status = RuntimeStatus()
    
    # 1. Escalate to DEGRADED (trigger was 10.0)
    signals_hi = PressureSignals(tick_compute_ms = 11.0)
    gov.evaluate(base_profile, signals_hi, status)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 2. Pressure drops to 8.0 (Below trigger 10.0, but ABOVE watermark 5.0)
    signals_mid = PressureSignals(tick_compute_ms = 8.0)
    gov.evaluate(base_profile, signals_mid, status)
    # Should stay in DEGRADED
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 3. Pressure drops to 4.0 (Below watermark 5.0)
    signals_lo = PressureSignals(tick_compute_ms = 4.0)
    gov.evaluate(base_profile, signals_lo, status)
    assert status.current_mode == RuntimeMode.CONSTRAINED
