# Milestone 13 Implementation Plan: Proof Instrumentation & Lock

## 1. Core Model Instrumentation (`src/core/`)
- **`src/core/governance.py`**: Add `metrics: Dict[str, float] = field(default_factory=dict)` to `PressureSignals`.
- **`src/core/updates.py`**: Add `metric_counters: Dict[str, int] = field(default_factory=dict)` to `StateUpdate`. Update `merge_many` and `is_noop`.
- **`src/core/state.py`**: Add `_index_hits` and `_index_misses` to `AuthoritativeState`.

## 2. Engine Subsystem Instrumentation (`src/engine/` & `src/systems/`)
- **`src/engine/movement_cache.py`**: Add `hits` and `misses` to `MovementPlanCache`. Track in `get`.
- **`src/engine/world_index.py`**: Track `_index_hits` and `_index_misses` on state when reusing/rebuilding indexes.
- **`src/engine/pipeline_phases/movement.py`**: In `route_movement_intent`, record candidate count in `update.metric_counters["movement_candidates"]`. Remove from `sub_phase_costs`.
- **`src/systems/strategic_systems/intelligence.py`**: In `fused_strategic_pass`, record candidate count in `update.metric_counters["strategic_candidates"]`.
- **`src/engine/pipeline.py` & `src/engine/compactor.py`**: In `refine`, record compaction metrics (`raw_entity_updates`, `compacted_entity_updates`) in `metric_counters`.
- **`src/engine/apply.py`**: Sum `moved_this_tick` across entity updates to calculate `movement_count`. Pass index hit/miss counters to new state.
- **`src/engine/kernel.py`**: Extract `metric_counters` and cache/index stats into `self._metrics`. Pass `self._metrics` to `PressureSignals`.

## 3. Benchmarking & Reporting (`src/perf/` & `scripts/`)
- **`src/perf/bench_harness.py`**: Aggregate `metrics` across signal history.
- **`reports/perf/baseline.json`**: Copy historical unoptimized baseline from `stored_artifacts/TCK-20260512-PERF-COMPLETION/latest.json`.
- **`scripts/generate_optimization_proof.py`**: Run benchmark suite across baseline scenarios and output `optimization_proof.json` and `optimization_proof.md`.

## 4. Verification & Testing (`tests/perf/`)
- **`tests/perf/test_optimization_proof_report.py`**: Implement automated test asserting empirical speedup and metric collection correctness.
