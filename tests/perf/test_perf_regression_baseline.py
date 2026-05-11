import pytest
import json
import os
from pathlib import Path

from src.perf.scenarios import build_idle_state
from src.perf.profiles import PERF_PROFILES

@pytest.mark.perf
def test_regression_vs_baseline(perf_harness):
    """
    Compare current performance against established baseline.json.
    Only runs if baseline.json exists.
    """
    baseline_path = Path("reports/perf/baseline.json")
    if not baseline_path.exists():
        pytest.skip("No baseline.json found to compare against.")
        
    with open(baseline_path, "r") as f:
        baseline = json.load(f)
        
    # We'll check the IDLE_100 scenario as a quick smoke test for regression
    scenario_id = "IDLE_100"
    if scenario_id not in baseline:
        pytest.skip(f"Scenario {scenario_id} not in baseline.")
        
    profile_name = baseline[scenario_id]["profile"]
    harness = perf_harness(profile_name)
    state = build_idle_state(entity_count=100)
    
    # Run a shorter benchmark for the regression guard
    result = harness.run_benchmark(
        scenario_id=f"REGRESSION_{scenario_id}",
        initial_state=state,
        warmup_ticks=20,
        sample_ticks=100
    )
    
    baseline_avg = baseline[scenario_id]["avg_tick_compute_ms"]
    current_avg = result["avg_tick_compute_ms"]
    
    # Threshold: Allow 20% regression or 5ms, whichever is larger
    # This accounts for environment variance in CI/local
    threshold = max(5.0, baseline_avg * 1.2)
    
    print(f"\nScenario: {scenario_id}")
    print(f"Baseline: {baseline_avg:.2f}ms")
    print(f"Current:  {current_avg:.2f}ms")
    print(f"Limit:    {threshold:.2f}ms")
    
    assert current_avg <= threshold, f"Performance regression detected! {current_avg:.2f}ms > {threshold:.2f}ms"
