"""Unit coverage for BenchHarness.run_benchmark()'s CPU-time sampler
(TCK-20260702-OBSISO-ISOLATION-PROOF, Step 1).

BenchHarness previously only sampled RSS memory. This adds a
psutil.Process.cpu_times() delta (start-of-warmup -> end-of-sample-window)
so downstream benchmarks (tests/perf/test_simq_isolation_overhead.py) can
compare engine-process CPU cost across SimQ modes, not just wall-clock TPS.
"""
from __future__ import annotations

from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state


def test_bench_harness_cpu_time_sampling():
    profile = PERF_PROFILES["PERF_512MB_LOCAL"]
    state = build_movement_state(entity_count=20)

    result = BenchHarness(profile).run_benchmark(
        scenario_id="CPU_SAMPLER_UNIT_TEST",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=10,
    )

    for key in ("cpu_time_user_delta_s", "cpu_time_system_delta_s", "cpu_time_total_delta_s"):
        assert key in result, f"BenchHarness result missing {key}"
        assert isinstance(result[key], float)
        # A start->end CPU-time delta over a busy window can never be negative —
        # this is the "monotonically non-decreasing" guarantee psutil.cpu_times()
        # itself provides (the counters only ever increase for a live process).
        assert result[key] >= 0.0, f"{key} was negative: {result[key]}"

    assert result["cpu_time_total_delta_s"] == round(
        result["cpu_time_user_delta_s"] + result["cpu_time_system_delta_s"], 4
    )
