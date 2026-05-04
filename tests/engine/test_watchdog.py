import pytest
import time
from unittest.mock import patch
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.certification.harness import CertificationHarness
from src.certification.models import ScenarioExpectations, ArenaStopCondition
from src.config.profiles import RuntimeProfile, HardwareClass

def test_arena_watchdog_trigger():
    profile = RuntimeProfile(
        name="WATCHDOG_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=0,
        max_tick_budget_ms=10.0, # 10ms budget
        max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    state = AuthoritativeState(tick=100, seed=42)
    harness = CertificationHarness(profile, output_dir="reports/test_watchdog")
    expectations = ScenarioExpectations(reproducibility_required=False)
    
    # Mock tick_once to sleep for 2 seconds (exceeding 1s minimum timeout)
    with patch("src.engine.kernel.Kernel.tick_once") as mock_tick:
        def slow_tick():
            time.sleep(2.0)
        mock_tick.side_effect = slow_tick
        
        result = harness.run_scenario("WATCHDOG_SCENARIO", state, expectations, ticks=10)
        
        assert result.stop_condition == ArenaStopCondition.WATCHDOG
        print("\nSuccessfully verified Arena Watchdog (hang detection).")
