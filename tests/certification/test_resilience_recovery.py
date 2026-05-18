import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.certification.harness import CertificationHarness
from src.certification.scenarios import get_scenario_expectations, PressureInjector
from src.certification.models import FailureKind


def test_harness_catches_failed_recovery():
    """
    M9 Law: Harness must catch failures to return to NORMAL mode.
    """
    profile = RuntimeProfile(
        name="NO_RECOVERY", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=100.0,
        max_observability_budget_percent=5.0
    )
    
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    state = AuthoritativeState(tick=0, seed=42, entities={
        1: (V2EntityBuilder(1)
            .kind("HERO")
            .identity(faction=Faction.HERO_GUILD)
            .build()),
        2: (V2EntityBuilder(2)
            .kind("MONSTER")
            .identity(faction=Faction.MONSTER_HORDE)
            .build())
    })
    harness = CertificationHarness(profile, output_dir="tmp/test_harness_resilience")
    from dataclasses import replace
    # We use RAM_PRESSURE but EXPLICITLY forbid recovery timeout for this test
    # so that the harness.run_scenario actually fails with conformance_passed=False
    expectations = replace(
        get_scenario_expectations("RAM_PRESSURE"), 
        allowed_failure_kinds=[FailureKind.NONE],
        required_sampling_interval_ticks=1
    )
    
    from unittest.mock import patch
    # We will mock the governor's evaluation
    with patch("src.engine.governor.ResourceGovernor.evaluate") as mock_eval:
        from src.core.governance import RuntimeMode
        from src.engine.policy import GovernorPolicy
        
        def g_eval_side_effect(profile, signals, status, current_tick, **kwargs):
            g_eval_side_effect.call_count += 1
            if g_eval_side_effect.call_count <= 5: 
                mode = RuntimeMode.NORMAL
            elif g_eval_side_effect.call_count <= 12:
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
