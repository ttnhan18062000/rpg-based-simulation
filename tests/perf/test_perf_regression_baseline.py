import pytest
import json
import sys
from pathlib import Path

from src.perf.scenarios import build_idle_state, build_movement_state, build_combat_arena_state

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from calibrate_simq import _load_world_state  # noqa: E402

from tests.tools.perf_assertions import assert_perf_threshold, PerformanceThresholdWarning


def _load_corpus_world_state(world_name: str, seed: int = 42):
    """Adapter matching the parametrize table's builder_fn(**kwargs) convention —
    TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION's real SimQ corpus worlds, alongside the
    existing synthetic scenario builders above."""
    state, _report = _load_world_state(world_name, seed)
    return state


# TCK-20260817-RUNTIMEMODE-BENCH-SCOPING: which of the 6 parametrized scenarios get a hard
# (AssertionError) vs. soft (PerformanceThresholdWarning) RuntimeMode-excursion gate is decided
# empirically, not guessed -- see plan.md Step 4 / Design Decisions (b). This set is populated
# ONLY after running the real, newly-instrumented gate (warmup_ticks=10, sample_ticks=50) against
# every scenario below and recording which ones stayed RuntimeMode.NORMAL throughout. Any
# scenario NOT in this set excursed under real load during that measurement and must stay soft,
# with a documented follow-up-ticket recommendation (ticket Out-of-Scope item 3) -- never silently
# add a scenario here without having actually run it.
_RUNTIME_MODE_HARD_SCENARIOS: frozenset[str] = frozenset({
    # Implement fills this in from the Step 4 empirical run. Example shape once measured:
    # "idle_100_local", "movement_100_local", ...
})


def _assert_runtime_mode_stayed_normal(mode_sequence: list, scenario_id: str, *, hard: bool) -> None:
    """Extracted so it is directly unit-testable against a synthetic mode_sequence, independent
    of BenchHarness/Governor load timing (see test_perf_regression_baseline_flags_runtime_mode_excursion)."""
    excursions = [m for m in mode_sequence if m != "NORMAL"]
    assert_perf_threshold(
        len(excursions), 0,
        f"RuntimeMode excursions during {scenario_id} "
        f"(modes seen: {sorted(set(mode_sequence))}, hard_gate={hard})",
        op="<=",
        hard=hard,
    )


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
    
    print(f"RuntimeMode modes observed for {scenario_id}: {sorted(set(result['mode_sequence']))}")
    _assert_runtime_mode_stayed_normal(
        result["mode_sequence"], scenario_id,
        hard=scenario_id in _RUNTIME_MODE_HARD_SCENARIOS,
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


@pytest.mark.parametrize("hard", [True, False])
def test_perf_regression_baseline_flags_runtime_mode_excursion(hard):
    """Forces a RuntimeMode excursion via a synthetic mode_sequence (never runs BenchHarness or
    touches compute time at all) and asserts the gate's extracted assertion helper surfaces it --
    AssertionError when hard=True, PerformanceThresholdWarning when hard=False -- proving the
    check is decoupled from avg_tick_compute_ms per AC3."""
    forced_sequence = ["NORMAL"] * 49 + ["CONSTRAINED"]
    if hard:
        with pytest.raises(AssertionError):
            _assert_runtime_mode_stayed_normal(forced_sequence, "SYNTHETIC_SCENARIO", hard=True)
    else:
        with pytest.warns(PerformanceThresholdWarning):
            _assert_runtime_mode_stayed_normal(forced_sequence, "SYNTHETIC_SCENARIO", hard=False)


def test_performance_contract_lists_runtimemode_scoped_claim():
    contract_text = Path("docs/engine/performance_contract.md").read_text()
    scoped_claims_section = contract_text.split("### 3.1 Scoped Claims")[1].split("### 3.2")[0]
    assert "RuntimeMode" in scoped_claims_section
