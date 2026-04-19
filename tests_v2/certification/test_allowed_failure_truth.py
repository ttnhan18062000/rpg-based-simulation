import pytest
from src_v2.certification.conformance import ConformanceEvaluator
from src_v2.certification.models import (
    MeasurementPoint, ScenarioExpectations, FailureKind, FailureKind as FK
)
from src_v2.config.profiles import RuntimeProfile, HardwareClass

def test_allowed_failure_preserves_truth():
    """
    M10 Law: Allowed failures must be recorded honestly.
    conformance_passed=True, allowed_failure_observed=True, failure_kind=Actual
    """
    profile = RuntimeProfile(
        name="test_profile",
        max_ram_mb=100.0,
        max_tick_budget_ms=10.0,
        hardware_class=HardwareClass.CLASS_A,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0
    )
    
    # Expectations whitelists FAILED_ENVELOPE
    expectations = ScenarioExpectations(
        allowed_failure_kinds=[FK.FAILED_ENVELOPE]
    )
    
    # Measurements contain a RAM violation
    measurements = [
        MeasurementPoint(
            tick=0, mode="NORMAL", memory_rss_mb=150.0, # VIOLATION
            memory_trend_mb_per_tick=0.0, tick_compute_ms=1.1,
            tick_compute_ms_avg=1.1, work_debt=0,
            worker_utilization=0.1, queue_utilization=0.0,
            replay_pressure=0.0, active_workers=1
        )
    ]
    
    passed, fail_kind, fail_reason, allowed_observed = ConformanceEvaluator.evaluate(
        profile, expectations, measurements, ["NORMAL"], "hash", "hash", "hash"
    )
    
    # M10 Assertions: The truth is preserved even though it passed
    assert passed is True
    assert allowed_observed is True
    assert fail_kind == FK.FAILED_ENVELOPE
    assert "RAM violation" in fail_reason

def test_unallowed_failure_fails_normally():
    """Verify that failures NOT in the whitelist still cause a certification failure."""
    profile = RuntimeProfile(
        name="test",
        max_ram_mb=100.0,
        max_tick_budget_ms=10.0,
        hardware_class=HardwareClass.CLASS_A,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0
    )
    expectations = ScenarioExpectations(allowed_failure_kinds=[FK.FAILED_RECOVERY_TIMEOUT]) # Different kind
    
    measurements = [
        MeasurementPoint(
            tick=0, mode="NORMAL", memory_rss_mb=150.0, # ENVELOPE violation
            memory_trend_mb_per_tick=0.0, tick_compute_ms=1.1,
            tick_compute_ms_avg=1.1, work_debt=0,
            worker_utilization=0.1, queue_utilization=0.0,
            replay_pressure=0.0, active_workers=1
        )
    ]
    
    passed, fail_kind, fail_reason, allowed_observed = ConformanceEvaluator.evaluate(
        profile, expectations, measurements, ["NORMAL"], "hash", "hash", "hash"
    )
    
    assert passed is False
    assert allowed_observed is False
    assert fail_kind == FK.FAILED_ENVELOPE
