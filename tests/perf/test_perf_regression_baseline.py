import pytest
import json
from pathlib import Path

from src.perf.scenarios import build_idle_state, build_movement_state, build_combat_arena_state

@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("scenario_id, builder_fn, kwargs", [
    ("idle_100_local", build_idle_state, {"entity_count": 100}),
    ("movement_100_local", build_movement_state, {"entity_count": 100}),
    ("combat_10_local", build_combat_arena_state, {"team_a_count": 5, "team_b_count": 5}),
])
def test_regression_vs_baseline(perf_harness, scenario_id, builder_fn, kwargs):
    """
    Compare current performance against established authoritative baselines.
    Ensures strict performance baseline regression guarding in CI.
    """
    baseline_file = Path(f"tests/perf/baselines/{scenario_id}.json")
    if not baseline_file.exists():
        pytest.skip(f"Baseline file {baseline_file} not found.")
        
    with open(baseline_file, "r") as f:
        baseline = json.load(f)
        
    profile_name = baseline["profile"]
    harness = perf_harness(profile_name)
    state = builder_fn(**kwargs)
    
    # Run benchmark for regression comparison
    result = harness.run_benchmark(
        scenario_id=f"REGRESSION_{scenario_id}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50,
        flags={"no_replay": True}
    )
    
    baseline_avg = baseline["avg_tick_compute_ms"]
    current_avg = result["avg_tick_compute_ms"]
    
    # Threshold: Allow 25% regression or 5ms, whichever is larger, to account for CI environment variance
    threshold = max(5.0, baseline_avg * 1.25)
    
    print(f"\nScenario: {scenario_id}")
    print(f"Baseline: {baseline_avg:.2f}ms")
    print(f"Current:  {current_avg:.2f}ms")
    print(f"Limit:    {threshold:.2f}ms")
    
    assert current_avg <= threshold, f"Performance regression detected in {scenario_id}! {current_avg:.2f}ms > {threshold:.2f}ms"
