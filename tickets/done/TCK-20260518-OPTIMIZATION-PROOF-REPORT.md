# TCK-20260518-OPTIMIZATION-PROOF-REPORT

## Title

Optimization Proof Instrumentation and Post-Implementation Lock

## Status

DONE

## Request Summary

Execute Milestone 13 of the V2 Performance Roadmap (`perf_plan_v2.md`): Structural discovery and proof instrumentation. Establish empirical proof reports comparing unoptimized vs optimized performance across the core benchmark scenarios.

## Scope

- Instrument compaction metrics (`raw_entity_updates`, `compacted_entity_updates`) without distorting kernel phase timing.
- Instrument `movement_candidates` and `strategic_candidates` as separate metric counters.
- Instrument spatial indexing and movement plan cache hit/miss rates.
- Create baseline report `reports/perf/baseline.json` from historical pre-optimization artifacts (`stored_artifacts/TCK-20260512-PERF-COMPLETION/latest.json`).
- Implement `scripts/generate_optimization_proof.py` to run the benchmark suite and output `optimization_proof.json` and `optimization_proof.md`.
- Implement regression test `tests/perf/test_optimization_proof_report.py` to enforce speedup requirements.

## Out of Scope

- Modifying simulation domain rules or laws.
- Changing non-performance core gameplay logic.

## Acceptance Criteria

- `generate_optimization_proof.py` executes successfully across `MOVEMENT_1000`, `RESOURCE_1000`, `COMBAT_100`, `STRATEGIC_500`, `MIXED_1000`.
- All newly added metrics (`raw_entity_updates`, `compacted_entity_updates`, `movement_candidates`, `strategic_candidates`, hit/miss rates) are accurately recorded in benchmark output without distorting `tick_compute_ms`.
- Automated regression test `tests/perf/test_optimization_proof_report.py` passes.
- Staging artifacts (`plan.md`, `investigation.md`, `test_plan.md`) and ticket are fully updated and aligned.

## Related Tickets

- TCK-20260518-READ-MODEL-CACHE

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/authoritative_pipeline.md`

## Related Code Areas

- `src/core/updates.py`
- `src/core/state.py`
- `src/core/governance.py`
- `src/engine/compactor.py`
- `src/engine/pipeline.py`
- `src/engine/apply.py`
- `src/engine/kernel.py`
- `src/engine/movement_cache.py`
- `src/engine/world_index.py`
- `src/perf/bench_harness.py`

## Assumptions / Open Questions

- Pre-optimization baseline in `stored_artifacts/TCK-20260512-PERF-COMPLETION/latest.json` provides correct baseline data for unoptimized engine performance.

## Implementation Notes

- Separating `metrics` (counts and ratios) from `phase_costs_ms` (durations) in `PressureSignals` prevents kernel compute time inflation.

## Test Summary

- `pytest tests/perf/test_optimization_proof_report.py` successfully passed in 2.99s.
- `pytest tests/perf/test_profiler_integrity.py` passed successfully.
- `pytest tests/integration/kernel/test_minimal_kernel.py` passed successfully.

## Files Changed

- `src/core/governance.py`: Added `metrics` field to `PressureSignals`.
- `src/core/updates.py`: Added `metric_counters` field to `StateUpdate`.
- `src/core/state.py`: Added `_index_hits` and `_index_misses` to `AuthoritativeState`.
- `src/engine/movement_cache.py`: Added `hits` and `misses` to `MovementPlanCache`.
- `src/engine/world_index.py`: Tracked spatial index hit/miss rates.
- `src/engine/pipeline_phases/movement.py`: Tracked `movement_candidates` in `metric_counters`.
- `src/systems/strategic_systems/intelligence.py`: Tracked `strategic_candidates` in `metric_counters`.
- `src/engine/pipeline.py`: Extracted compaction metrics into `metric_counters`.
- `src/engine/apply.py`: Calculated exact `movement_count` and passed index stats.
- `src/engine/kernel.py`: Extracted `metric_counters` and cache stats into `_metrics`. Added `_metrics` to `__slots__`.
- `src/perf/bench_harness.py`: Aggregated `metrics` into benchmark output.
- `reports/perf/baseline.json`: Copied unoptimized historical baseline.
- `scripts/generate_optimization_proof.py`: Created optimization proof generator script.
- `tests/perf/test_optimization_proof_report.py`: Created automated test asserting empirical speedup and metric correctness.

## Completion Summary

Milestone 13 is fully complete. The engine pipeline has been cleanly instrumented with granular hit/miss counters and compaction ratios without distorting nanosecond/millisecond compute phase timing. The empirical optimization proof report generator successfully demonstrates speedups across all five benchmark scenarios (`MOVEMENT_1000` speedup: 33.43x, `RESOURCE_1000` speedup: 83.95x, `COMBAT_100` speedup: 14.17x, `STRATEGIC_500` speedup: 21.77x, `MIXED_1000` speedup: 33.32x) and verify pristine compute latency reductions. All tests pass successfully and staging artifacts are locked.
