"""Unit coverage for BenchHarness.run_benchmark()'s CPU-time sampler
(TCK-20260702-OBSISO-ISOLATION-PROOF, Step 1).

BenchHarness previously only sampled RSS memory. This adds a
psutil.Process.cpu_times() delta (start-of-warmup -> end-of-sample-window)
so downstream benchmarks (tests/perf/test_simq_isolation_overhead.py) can
compare engine-process CPU cost across SimQ modes, not just wall-clock TPS.
"""
from __future__ import annotations

from src.core.governance import RuntimeMode
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


def test_run_benchmark_records_mode_sequence():
    profile = PERF_PROFILES["PERF_1GB_LOCAL"]
    state = build_movement_state(entity_count=20)

    result = BenchHarness(profile).run_benchmark(
        scenario_id="MODE_SEQUENCE_UNIT_TEST",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=10,
    )

    assert "mode_sequence" in result
    assert len(result["mode_sequence"]) == 10
    valid_names = {m.name for m in RuntimeMode}
    assert all(m in valid_names for m in result["mode_sequence"])
    # Deviation from plan.md Step 5a (TCK-20260817-RUNTIMEMODE-BENCH-SCOPING, see
    # staging_artifacts/.../plan.md Deviations): the plan's original assertion here asserted
    # every tick stays NORMAL, on the unverified assumption that an ordinary low-load movement
    # scenario would. The Step 4 empirical pass proved this false for every PERF_*_LOCAL profile,
    # not just this one: WorkerManager.get_stats() (src/engine/worker_manager.py:229-232) defaults
    # worker_utilization to 1.0 (not 0.0) whenever max_worker_count == 0, and every PERF_*_LOCAL
    # profile (src/perf/profiles.py) sets workers=0 -- so ResourceGovernor._get_indicated_mode()
    # (src/engine/governor.py:88, worker_utilization >= 0.9 -> DEGRADED) trips unconditionally on
    # tick 1 of any LOCAL-mode benchmark regardless of real load. This is a pre-existing Governor/
    # WorkerManager signal defect, not something this ticket is scoped to fix (Scope Guards forbid
    # touching governor.py/worker_manager.py or recalibrating profiles) -- flagged as a follow-up
    # recommendation in the ticket's Implementation Notes instead. This test therefore only proves
    # the sampling wiring itself (shape, length, valid enum names) -- exactly what 5a is for per
    # Design Decision (c); it does not assert a specific RuntimeMode value.
