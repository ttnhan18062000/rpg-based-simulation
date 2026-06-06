# TCK-20260512-PERF-HARNESS-ENHANCEMENT

## Title
Enhance BenchHarness with p95, p99, and RSS metrics

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Upgrade the `BenchHarness` to capture production-grade telemetry, including latency percentiles and physical memory usage (RSS).

## Scope
- [x] Modify `src/perf/bench_harness.py`.
- [x] Integrate `psutil` for RSS sampling.
- [x] Implement p50, p95, p99 calculations for tick and phase costs.
- [x] Include memory metrics in results.

## Out of Scope
- Implementation of regression tests.

## Acceptance Criteria
- `BenchHarness.run_benchmark` returns p50, p95, and p99 metrics for tick compute time and phase costs.
- Results include `avg_rss_mb` and `max_rss_mb`.
- No significant performance overhead from the harness itself (use efficient sampling).

## Related Tickets
- TCK-20260512-PERF-INVESTIGATION (Done)
- TCK-20260512-PERF-PROFILES (Done)
- TCK-20260512-PERF-SCENARIOS (Done)

## Related Docs
- [performance_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/performance_implementation.md)

## Related Code Areas
- `src/perf/bench_harness.py`

## Implementation Notes
- Use `psutil.Process().memory_info().rss / (1024 * 1024)` for MB.
- Percentiles should be calculated using `statistics.quantiles` or simple sorting.

## Test Summary
- Verify that benchmark results contain the new keys.

## Files Changed
- [MODIFY] src/perf/bench_harness.py

## Completion Summary
- N/A
