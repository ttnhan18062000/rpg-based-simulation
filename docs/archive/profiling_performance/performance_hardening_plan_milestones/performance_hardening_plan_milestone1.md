---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Milestone 1 — Fix Benchmark / Profiler Truth

## Goal

Make benchmark numbers reflect the real engine cost. Right now, perf tests use `avg_tps`, `p95_tick_compute_ms`, memory caps, and `tick_ms` thresholds, but some tests rely on loose thresholds and do not isolate frame pacing or replay overhead. Existing perf tests show this pattern across idle, movement, resource, strategic, combat, and mixed stress tests.  

## Problem to fix

The profiler must answer:

```text
How much compute did the authoritative tick actually cost?
```

Not:

```text
How much time passed including sleep, replay overhead, or missing phases?
```

## Tasks

| Task                                               | Narrow implementation logic                                                                                                                                                                                       | Files / area                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| M1.1 Add benchmark execution options               | Add flags/options: `no_replay`, `no_frame_pacing`, `capture_phase_breakdown`, `strict_phase_accounting`.                                                                                                          | `src/perf/bench_harness.py`, `src/engine/kernel.py` |
| M1.2 Default benchmark to no replay                | In `BenchHarness.run_benchmark`, default `flags["no_replay"] = True` unless explicitly overridden.                                                                                                                | `BenchHarness`                                      |
| M1.3 Disable frame pacing in benchmark             | Add a kernel/runtime switch so benchmark mode does not call sleep for `max_tick_budget_ms`.                                                                                                                       | `Kernel.tick_once()`                                |
| M1.4 Move status recording to the real end of tick | Ensure `PressureSignals` / runtime status is recorded after all phases, including persistence/final accounting.                                                                                                   | `Kernel.tick_once()`                                |
| M1.5 Validate phase accounting                     | Ensure `tick_compute_ms` is greater than or approximately equal to the sum of phase costs.                                                                                                                        | Kernel status                                       |
| M1.6 Standardize benchmark result schema           | Output must include: `avg_tick_compute_ms`, `p95_tick_compute_ms`, `p99_tick_compute_ms`, `avg_tps_compute_only`, `wall_clock_s`, `phase_breakdown`, `memory_delta_mb`, `replay_enabled`, `frame_pacing_enabled`. | `BenchHarness`                                      |
| M1.7 Separate wall-clock TPS from compute TPS      | Keep `wall_clock_tps` for real elapsed time. Add `compute_tps` for optimization decisions.                                                                                                                        | `BenchHarness`                                      |

## New tests to add

```python
def test_benchmark_disables_replay_by_default():
    """
    Law:
        BenchHarness must not include replay/hash overhead unless explicitly requested.
    """

def test_benchmark_disables_frame_pacing_by_default():
    """
    Law:
        Perf TPS must measure compute throughput, not artificial sleep pacing.
    """

def test_recorded_tick_compute_includes_all_phases():
    """
    Law:
        RuntimeStatus tick_compute_ms must include all authoritative tick phases.
    """

def test_phase_breakdown_sum_is_not_greater_than_tick_compute_by_large_margin():
    """
    Law:
        Phase accounting must not report impossible timings.
    """

def test_benchmark_schema_contains_compute_and_wall_clock_metrics():
    """
    Law:
        Benchmark report must distinguish compute-only cost from wall-clock elapsed time.
    """
```

## Acceptance checklist

```text
[ ] BenchHarness defaults to no_replay=True.
[ ] BenchHarness defaults to no_frame_pacing=True.
[ ] Benchmark result distinguishes compute TPS and wall-clock TPS.
[ ] Kernel status is recorded after all relevant tick phases.
[ ] Phase breakdown includes every measured authoritative phase.
[ ] Existing perf tests are updated to assert compute metrics, not polluted wall-clock metrics.
[ ] New profiler-integrity tests pass.
```

## Exit condition

You can trust benchmark numbers enough to compare two branches.

Not perfect. Trustworthy enough.

---
