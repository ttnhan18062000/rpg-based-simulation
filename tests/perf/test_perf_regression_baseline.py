import pytest
import json
import sys
from pathlib import Path

from src.perf.scenarios import build_idle_state, build_movement_state, build_combat_arena_state

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from calibrate_simq import _load_world_state  # noqa: E402

from tests.tools.perf_assertions import assert_perf_threshold


def _load_corpus_world_state(world_name: str, seed: int = 42):
    """Adapter matching the parametrize table's builder_fn(**kwargs) convention —
    TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION's real SimQ corpus worlds, alongside the
    existing synthetic scenario builders above."""
    state, _report = _load_world_state(world_name, seed)
    return state


@pytest.mark.perf
@pytest.mark.slow
@pytest.mark.parametrize("scenario_id, builder_fn, kwargs", [
    ("idle_100_local", build_idle_state, {"entity_count": 100}),
    ("movement_100_local", build_movement_state, {"entity_count": 100}),
    ("combat_10_local", build_combat_arena_state, {"team_a_count": 5, "team_b_count": 5}),
    ("simq_corpus_frontier_extended", _load_corpus_world_state, {"world_name": "frontier_extended"}),
    ("simq_corpus_frontier_marches", _load_corpus_world_state, {"world_name": "frontier_marches"}),
    ("simq_corpus_crowded_frontier", _load_corpus_world_state, {"world_name": "crowded_frontier"}),
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
    
    assert_perf_threshold(
        current_avg, threshold,
        f"Performance regression check for {scenario_id}", op="<=",
    )
