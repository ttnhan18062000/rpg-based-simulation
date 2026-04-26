import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass
import os

def test_arena_5v5_startup():
    """Verify that the 5v5 Arena spawns entities and runs for 10 ticks."""
    profile = RuntimeProfile(
        name="ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=50.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_5V5"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    # 5v5 should have 10 entities total
    assert len(state.entities) == 10
    
    harness = CertificationHarness(profile, output_dir="reports/arena_test")
    result = harness.run_scenario(scenario_id, state, expectations, ticks=10)
    
    assert result.conformance_passed
    print(f"Arena 5v5 passed 10 ticks. Final Hash: {result.final_hash}")

def test_arena_50v50_scaling():
    """Verify that the 50v50 Stress Arena spawns 100 entities."""
    scenario_id = "COMBAT_ARENA_STRESS_50V50"
    state = build_scenario_state(scenario_id)
    
    assert len(state.entities) == 100
    print("Arena 50v50 scaling injection successful.")
