import pytest
from src.core.governance import RuntimeMode, PressureSignals
from src.engine.governor import ResourceGovernor
from src.engine.runtime_status import RuntimeStatus
from src.config.profiles import RuntimeProfile, HardwareClass

@pytest.fixture
def mb_profile():
    return RuntimeProfile(
        name="test_anti_thrashing",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=10,
        max_replay_buffer_kb=1024,
        max_tick_budget_ms=10.0, # Easy math: 10ms
        max_work_debt=100,
        max_observability_budget_percent=5.0,
        # Milestone B Truth Controls
        dwell_time_ticks=5,
        confidence_window_ticks=3,
        recovery_watermark=0.8
    )

def test_recovery_confidence_window(mb_profile):
    """Verify that recovery requires sustained low pressure (Confidence Window)."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # 1. Escalate to DEGRADED (Threshold 10ms, Survival at 15ms)
    signals_bad = PressureSignals(tick_compute_ms = 12.0)
    gov.evaluate(mb_profile, signals_bad, status, 0)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # Recovery watermark is 10ms * 0.7 * 0.8 = 5.6ms 
    # (Note: CONSTRAINED trigger is 7.0ms, so recovery to NORMAL is 7.0 * 0.8 = 5.6ms)
    signals_good = PressureSignals(tick_compute_ms = 4.0) 
    
    # 2. First Good Sample: Should NOT recover (Dwell+Confidence)
    gov.evaluate(mb_profile, signals_good, status, 1)
    status.record_signals(signals_good) # Must record to fill history for confidence window
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 3. Second Good Sample: Should NOT recover
    gov.evaluate(mb_profile, signals_good, status, 2)
    status.record_signals(signals_good) 
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # 4. Third Good Sample: Should NOT recover (Dwell time is 5, we are at 3)
    gov.evaluate(mb_profile, signals_good, status, 3)
    status.record_signals(signals_good)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # Continuous good samples until both averaging window (5) and confidence window (3) clear.
    # We need roughly 8-10 ticks of sustained good signal.
    for i in range(1, 15):
        gov.evaluate(mb_profile, signals_good, status, 5 + i)
        status.record_signals(signals_good)
        if status.current_mode == RuntimeMode.CONSTRAINED:
            break
            
    assert status.current_mode == RuntimeMode.CONSTRAINED

def test_anti_thrashing_spiky_load(mb_profile):
    """Verify that a single bad sample in the window resets recovery confidence."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # Escalate
    gov.evaluate(mb_profile, PressureSignals(tick_compute_ms=12.0), status, 0)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # Ticks 1-4: Good (filling dwell but one bad tick follows)
    for i in range(1, 4):
        s = PressureSignals(tick_compute_ms=4.0)
        gov.evaluate(mb_profile, s, status, i)
        status.record_signals(s)
        
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # Tick 4: BAD spike (still below escalation but above recovery watermark)
    # Recovery limit is 5.6ms. We send 6.0ms.
    spike = PressureSignals(tick_compute_ms=6.0)
    gov.evaluate(mb_profile, spike, status, 4)
    status.record_signals(spike)
    assert status.current_mode == RuntimeMode.DEGRADED
    
    # Ticks 5-6: Good again. 
    # Dwell time (5) is satisfied at tick 5, but Confidence Window (3) is NOT 
    # because of the spike in the window [4.0, 6.0, 4.0].
    s = PressureSignals(tick_compute_ms=4.0)
    gov.evaluate(mb_profile, s, status, 5)
    status.record_signals(s)
    assert status.current_mode == RuntimeMode.DEGRADED # Stabilized!

def test_monotonic_recovery_step(mb_profile):
    """Verify that system recovers exactly one mode at a time."""
    gov = ResourceGovernor()
    status = RuntimeStatus()
    
    # Escalate to SURVIVAL (Threshold 15ms)
    gov.evaluate(mb_profile, PressureSignals(tick_compute_ms=25.0), status, 0)
    assert status.current_mode == RuntimeMode.SURVIVAL
    
    # Provide perfect conditions for recovery
    s = PressureSignals(tick_compute_ms=2.0)
    for i in range(1, 10):
        # Once dwell and confidence met, should drop to DEGRADED
        gov.evaluate(mb_profile, s, status, i)
        status.record_signals(s)
        if status.current_mode == RuntimeMode.DEGRADED:
            break
            
    assert status.current_mode == RuntimeMode.DEGRADED
    assert status.mode_dwell_ticks == 0 # Reset on transition
