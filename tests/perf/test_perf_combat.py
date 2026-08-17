import pytest
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_combat_arena_state

@pytest.mark.slow
@pytest.mark.perf
@pytest.mark.parametrize("side_count", [10, 50, 100, 500])
def test_perf_combat(side_count, perf_report_dir):
    profile = PERF_PROFILES["PERF_2GB_LOCAL"]
    state = build_combat_arena_state(team_a_count=side_count, team_b_count=side_count)

    result = BenchHarness(profile).run_benchmark(
        scenario_id=f"COMBAT_{side_count}v{side_count}",
        initial_state=state,
        warmup_ticks=10,
        sample_ticks=50
    )

    print(f"\n[COMBAT {side_count}v{side_count}] p95={result['p95_tick_compute_ms']:.2f}ms. BREAKDOWN:", result["phase_breakdown"])
    # 750ms bound is sized for the [500] case (real measured ~432-500ms across local/CI runs,
    # TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER) -- [10]/[50]/[100] (12-68ms measured)
    # have materially looser effective regression sensitivity as a result of sharing this one bound.
    assert result["p95_tick_compute_ms"] < 750.0 # Combat is more expensive
