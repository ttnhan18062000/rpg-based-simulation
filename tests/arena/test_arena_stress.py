import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass

def test_arena_stress_50v50():
    """Verify that a 50v50 battle stays within resource limits."""
    profile = RuntimeProfile(
        name="STRESS_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=400.0, max_queue_depth=500,
        max_replay_buffer_kb=4096, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_STRESS_50V50"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_stress")
    # Run for 50 ticks to measure scaling
    result = harness.run_scenario(scenario_id, state, expectations, ticks=50)
    
    assert result.conformance_passed
    print(f"Stress Arena 50v50 completed.")
    print(f"Peak RSS: {result.peak_rss_mb:.1f} MB")
    print(f"Total CPU: {result.total_cpu_sec:.3f} sec")
    
    # Assert memory growth is bounded (starting from ~48MB, should stay well below 200MB)
    assert result.peak_rss_mb < 200.0
