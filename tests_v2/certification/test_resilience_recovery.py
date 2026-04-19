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
    
    from unittest.mock import patch
    # We will mock the governor's evaluation
    with patch("src_v2.engine.governor.ResourceGovernor.evaluate") as mock_eval:
        from src_v2.core.governance import RuntimeMode
        from src_v2.engine.policy import GovernorPolicy
        
        def g_eval_side_effect(profile, signals, status, current_tick):
            g_eval_side_effect.call_count += 1
            # Baseline (10 ticks) + Cert (10 ticks). 
            # Governor.evaluate is called once per tick per kernel.
            # Calls 1-10: Baseline (Returns NORMAL)
            # Calls 11-13: Cert (Returns NORMAL)
            # Calls 14-15: Cert (Returns CONSTRAINED)
            # Calls 16-20: Cert (Returns DEGRADED)
            if g_eval_side_effect.call_count <= 13: 
                mode = RuntimeMode.NORMAL
            elif g_eval_side_effect.call_count <= 15:
                mode = RuntimeMode.CONSTRAINED
            else:
                mode = RuntimeMode.DEGRADED
                
            status.current_mode = mode
            return GovernorPolicy.from_mode(mode)
        
        g_eval_side_effect.call_count = 0
        mock_eval.side_effect = g_eval_side_effect
        
        result = harness.run_scenario("RAM_PRESSURE", state, expectations, ticks=10)
        
        # VERIFY: Fails because it never returned to NORMAL at the END
        assert not result.conformance_passed
        assert result.failure_kind == FailureKind.FAILED_RECOVERY_TIMEOUT
        assert "System failed to recover" in result.failure_reason
