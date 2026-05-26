# TCK-20260519-SIM-OBS-PHASE3-M10

## Title

Milestone 10: Metric Window Recorder

## Status

DONE

## Request Summary

Implement rolling metric window recording capabilities for post-run analysis, creating the standard `metric_windows.jsonl` artifact containing aggregated tick performance, memory usage, events, violations, and game state metrics over standard time/tick bounds.

## Scope

- **MetricWindowRecord Schema**: Define standard JSON-serializable schema with required and optional metric metrics.
- **MetricWindowAccumulator**: Create rolling statistics calculator capturing tick snapshots without scanning world state.
- **MetricWindowRecorder**: Manage files, window size configuration, and append operations to standard run directories.
- **Kernel Integration**: Register recorder instantiation, feed tick updates, and handle final flush sequences on simulation end.
- **Testing suite**: Unit tests for accumulator aggregates and exact p95 math; integration tests verifying file emission and deterministic state parity.

## Out of Scope

- Anomaly rule execution or post-run analysis (Milestone 11/12).
- API or CLI interfaces for metric queries.
- live dashboard visualization support.

## Acceptance Criteria

- **JSONL Output Validation**: Simulation run generates a valid, standard JSONL file `metric_windows.jsonl` containing one JSON object per completed or partial window.
- **Accumulator Math Correctness**: Average, max, and exact windowed p95 calculations match mathematical expectations precisely.
- **Zero Simulation Hash Drift**: State hashes under `OFF` and `LIGHT` modes are 100% bit-identical.
- **Zero Hot-path World Scans**: Metrics extraction is bounded to pre-existing snapshots without querying entities/components repeatedly.
- **100% Test Coverage Success**: All tests pass cleanly.

## Related Tickets

- `TCK-20260519-SIM-OBS-PHASE3-M9` (Completed)

## Related Docs

- `obs_sim_phase3.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/metric_recorder.py` [NEW]
- `src/engine/kernel.py`

## Assumptions / Open Questions

- We assume standard default short window size is 100 ticks.

## Implementation Notes

- Designed dynamic `window_start_tick` assignments based on the first recorded tick to cleanly support loop offsets.
- Implemented deterministic linear interpolation for `p95` tick compute math.
- Added comprehensive slots to Kernel slot array to ensure strict runtime class constraints are kept intact.

## Test Summary

- Added `tests/unit/observability/test_metric_window_recorder.py` testing schemas, serialization, and aggregation math (4/4 passing).
- Added `tests/integration/observability/test_metric_windows_flow.py` testing end-to-end runs, file writes, and hash parity verification (3/3 passing).
- Verified that all 26/26 tests inside the observability suites pass cleanly.

## Files Changed

- `src/observability/reporting/metric_recorder.py` [NEW]
- `src/engine/kernel.py`
- `tests/unit/observability/test_metric_window_recorder.py` [NEW]
- `tests/integration/observability/test_metric_windows_flow.py` [NEW]
- `obs_sim_phase3.md`

## Completion Summary

- Created `MetricWindowRecord`, `MetricWindowAccumulator`, and `MetricWindowRecorder` cleanly isolating in-memory aggregation from global authoritative updates.
- Successfully integrated hooks into the Kernel runtime cycle and certified zero state hash drift under multiple operational modes.
