# Implementation Plan - TCK-20260515-PERF-M1

## Goal
Improve measurement accuracy by isolating compute cost from frame pacing and replay overhead.

## Proposed Changes

### Core Engine
#### [MODIFY] [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
- In `__init__`, check for `no_frame_pacing` flag.
- In `tick_once`, skip `time.sleep` if `no_frame_pacing` is enabled.
- Reorganize `tick_once` to ensure `_final_compute_ms` captures all phases including persistence.
- Move status recording to the end of `tick_once`.
- Add validation that `tick_compute_ms` accurately represents the sum of phase costs.

### Performance Tools
#### [MODIFY] [bench_harness.py](file:///home/vboxuser/Work/rpg-based-simulation/src/perf/bench_harness.py)
- Default `flags` to `{"no_replay": True, "no_frame_pacing": True}` if not provided.
- Update `run_benchmark` to calculate `wall_clock_tps` separately from `compute_tps`.
- Update result schema to include compute vs wall-clock metrics.
- Include `replay_enabled` and `frame_pacing_enabled` in the report.

## Verification Plan

### Automated Tests
- Create `tests/perf/test_profiler_integrity.py` with the following tests:
    - `test_benchmark_disables_replay_by_default`
    - `test_benchmark_disables_frame_pacing_by_default`
    - `test_recorded_tick_compute_includes_all_phases`
    - `test_phase_breakdown_sum_is_consistent`
    - `test_benchmark_schema_contains_compute_and_wall_clock_metrics`

### Manual Verification
- Run a small benchmark and verify the JSON output schema.
