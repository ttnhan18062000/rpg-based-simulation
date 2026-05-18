# TCK-20260518-PERF-REGRESSION-GATE

## Title
PerfRegressionGate Implementation and Automated Baseline Comparison

## Status
DONE

## Request Summary
Implement `PerfRegressionGate`, `PerfBaseline`, `PerfResult`, and `PerfGateResult` in `src/perf/regression_gate.py` to compare benchmark runs against committed baselines. Prevent silent regression on compute latency percentiles (p95, p99), phase costs, and memory consumption (RSS peak, memory delta), while isolating comparisons from wall-clock variance and strictly enforcing CI baseline presence.

## Scope
- Defined dataclasses `PerfBaseline`, `PerfResult`, and `PerfGateResult`.
- Implemented `PerfRegressionGate.compare` checking:
  - `p95_tick_compute_ms`
  - `p99_tick_compute_ms`
  - Phase p95 costs (`phase_p95_ms`)
  - `peak_rss_mb`
  - `memory_delta_mb`
  - `compute_tps`
  - `raw_entity_updates` vs `compacted_entity_updates`
- Supported CI vs local mode for missing baselines (raises error in CI, returns warning/skip in local mode).
- Created unit test suite `tests/unit/perf/test_perf_regression_gate.py` verifying all criteria.

## Out of Scope
- None

## Acceptance Criteria
- [x] CI cannot silently skip missing baseline.
- [x] Gate compares compute metrics, not wall-clock metrics.
- [x] Gate includes phase-level regression.
- [x] Gate includes memory regression.

## Related Tickets
- TCK-20260517-PERF-HARDENING

## Related Docs
- perf_test_plan.md

## Related Stored Artifacts
- `stored_artifacts/TCK-20260518-PERF-REGRESSION-GATE/`

## Related Code Areas
- `src/perf/regression_gate.py`

## Assumptions / Open Questions
- Default regression threshold: 10% tolerance for latency/memory metrics before triggering a failure.

## Implementation Notes
- Implemented strict isolation from wall-clock variance by evaluating pure `compute_tps` and compute latency.
- Supported seamless conversion from `BenchHarness` dictionary format via `PerfResult.from_bench_dict`.

## Test Summary
- `pytest tests/unit/perf/test_perf_regression_gate.py`: 8/8 passed in 0.06s.
- `pytest tests/unit/ -m "not slow"`: 805/805 passed in 11.58s.

## Files Changed
- `src/perf/regression_gate.py`
- `tests/unit/perf/test_perf_regression_gate.py`

## Completion Summary
- Successfully implemented the performance regression gate, establishing a robust automated verification barrier for all future engine development.
