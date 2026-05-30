# TCK-20260529-OBS-PHASE20

## Title

Observability Runtime Performance Profiling Lane (Phase 20)

## Status

DONE

## Request Summary

Implement the Phase 20 Runtime Performance Profiling Lane to track simulation phase costs, metrics windows, and observability overhead separately.

## Scope

- Define and implement `PhaseTimingRecord` dataclass in `src/observability/performance/models.py` or config registry.
- Implement `PhaseProfiler` and `PhaseProfileScope` context manager in `src/observability/performance/profiler.py`.
- Extend existing `MetricWindowRecord` with optional phase timing JSON metrics and observability overhead averages.
- Implement observability overhead tracking (event extraction, serialization, queue push, timeline append).
- Add unit, integration, and performance budget tests.

## Out of Scope

- Implementing the non-blocking event emission queue (Phase 21) or normalization (Phase 22+)

## Acceptance Criteria

- `PhaseTimingRecord` represents accurate phase cost and counter statistics.
- `PhaseProfiler` profiles phases safely with context manager and minimal overhead.
- Profiler supports optional disabled status when `OBS_RUNTIME_PROFILING` is False.
- Metric windows serializations remain backward compatible with old shapes.
- Observability overhead is monitored and reported separately from simulation phase timings.
- Unit and integration tests pass successfully with zero regression in performance.

## Related Tickets

- TCK-20260529-OBS-PHASE19

## Related Docs

- docs/architecture/observability_behavior_profiling_boundary.md
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260529-OBS-PHASE19/
- stored_artifacts/TCK-20260529-OBS-PHASE20/plan.md
- stored_artifacts/TCK-20260529-OBS-PHASE20/investigation.md
- stored_artifacts/TCK-20260529-OBS-PHASE20/test_plan.md

## Related Code Areas

- `src/observability/performance/`
- `src/observability/reporting/metric_recorder.py`
- `tests/unit/observability/performance/`
- `tests/integration/observability/`

## Assumptions / Open Questions

- Overhead measurements should utilize cheap monotonic clocks (e.g. `time.perf_counter_ns()`).

## Implementation Notes

- Designed and implemented exception-safe `PhaseProfiler` and `PhaseProfileScope` using `time.perf_counter_ns()`.
- Extended `MetricWindowRecord` in `src/observability/reporting/metric_recorder.py` with 8 new optional performance timing and overhead metrics.
- Preserved backward compatibility of the metric windows schema with safe default values for existing runs.

## Test Summary

- Tested exception-safety, counter incrementing, and disabled mode no-op behavior of `PhaseProfiler` in `tests/unit/observability/performance/test_phase20_phase_profiler.py`.
- Tested backward schema compatibility and JSON serialization of `MetricWindowRecord` in `tests/unit/observability/performance/test_phase20_metric_window_extension.py`.
- Tested phase timings accumulation and flush integration in `tests/integration/observability/test_phase20_phase_timing_integration.py`.
- **Result**: All 7 tests passed successfully.

## Files Changed

- `src/observability/performance/models.py`
- `src/observability/performance/profiler.py`
- `src/observability/performance/__init__.py`
- `src/observability/reporting/metric_recorder.py`
- `tests/unit/observability/performance/test_phase20_phase_profiler.py`
- `tests/unit/observability/performance/test_phase20_metric_window_extension.py`
- `tests/integration/observability/test_phase20_phase_timing_integration.py`

## Completion Summary

- Successfully completed the Runtime Performance Profiling Lane (Phase 20) with full timing aggregation, backward compatibility, and isolated overhead monitoring. All tests passing.
