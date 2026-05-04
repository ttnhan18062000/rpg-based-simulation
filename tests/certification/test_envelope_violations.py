import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.certification.harness import CertificationHarness
from src.certification.scenarios import get_scenario_expectations, PressureInjector
from src.certification.models import FailureKind


def test_harness_catches_ram_violation():
    """
    M9 Law: Harness must catch envelope ceiling violations.
    """
    # Extremely low RAM ceiling to force violation
    profile = RuntimeProfile(
        name="CRUSH_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1, # 1MB limit - will be exceeded by practically anything
        max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    from src.core.builder import V2EntityBuilder
    state = AuthoritativeState(tick=0, seed=42, entities={
        i: (V2EntityBuilder(i)
            .kind("TEST")
            .position(0.0, 0.0)
            .readiness(100.0)
            .build())
        for i in range(1, 101) # 100 entities in 1MB limit should fail
    })
    
    harness = CertificationHarness(profile)
    from dataclasses import replace
    expectations = replace(get_scenario_expectations("IDLE_CLEAN"), required_sampling_interval_ticks=1)
    
    result = harness.run_scenario("IDLE_CLEAN", state, expectations, ticks=1)
    
    # VERIFY: Violation detected
    assert not result.conformance_passed
    assert result.failure_kind == FailureKind.FAILED_ENVELOPE
    assert "RAM violation" in result.failure_reason


def test_harness_detects_missing_degradation_mode():
    """
    M9 Law: Conformance fails if expected mode transitions never occur.
    """
    profile = RuntimeProfile(
        name="NORMAL_ONLY", hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    state = AuthoritativeState(tick=0, seed=42, entities={})
    harness = CertificationHarness(profile)
    
    # We use a scenario that EXPECTS a transition to DEGRADED
    # but run a perfectly idle simulation that stays in NORMAL.
    from dataclasses import replace
    expectations = replace(get_scenario_expectations("RAM_PRESSURE"), required_sampling_interval_ticks=1)
    
    result = harness.run_scenario("RAM_PRESSURE", state, expectations, ticks=5)
    
    # VERIFY: Fails because DEGRADED was never entered
    assert not result.conformance_passed
    assert result.failure_kind == FailureKind.FAILED_DEGRADATION_SEQUENCE
    assert "Required mode 'DEGRADED' was never entered" in result.failure_reason
