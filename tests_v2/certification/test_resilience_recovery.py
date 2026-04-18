import pytest
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.certification.harness import CertificationHarness
from src_v2.certification.scenarios import get_scenario_expectations, PressureInjector
from src_v2.certification.models import FailureKind


def test_harness_catches_failed_recovery():
    """
    M9 Law: Harness must catch failures to return to NORMAL mode.
    """
    profile = RuntimeProfile(
        name="NO_RECOVERY", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0
    )
    
    state = AuthoritativeState(tick=0, seed=42, entities={})
    harness = CertificationHarness(profile)
    expectations = get_scenario_expectations("RAM_PRESSURE") # requires_recovery=True
    
    # We will mock the kernel's mode status 
    from unittest.mock import PropertyMock, patch
    with patch("src_v2.engine.runtime_status.RuntimeStatus.current_mode", new_callable=PropertyMock) as mock_mode:
        from src_v2.core.governance import RuntimeMode
        # Baseline (10 ticks) + Cert (10 ticks). 
        # current_mode is accessed multiple times per tick.
        # We need a robust side_effect.
        def mode_side_effect(*args, **kwargs):
            mode_side_effect.call_count += 1
            # First 50 calls (baseline + start of cert) are NORMAL
            if mode_side_effect.call_count < 50:
                return RuntimeMode.NORMAL
            return RuntimeMode.DEGRADED
        
        mode_side_effect.call_count = 0
        mock_mode.side_effect = mode_side_effect
        
        result = harness.run_scenario("RAM_PRESSURE", state, expectations, ticks=10)
        
        # VERIFY: Fails because it never returned to NORMAL at the END
        assert not result.conformance_passed
        assert result.failure_kind == FailureKind.FAILED_RECOVERY
        assert "failed to return to NORMAL" in result.failure_reason
