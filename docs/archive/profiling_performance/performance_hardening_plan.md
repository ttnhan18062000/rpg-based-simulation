# Performance Hardening Plan

## Goal
Establish a high-fidelity performance baseline for the V2 RPG Engine and systematically eliminate compute and memory bottlenecks while maintaining 100% logic parity.

---

## Milestone 0: Baseline Establishment [DONE]
- [x] Integrate `BenchHarnessV2` into the core pipeline.
- [x] Establish initial p95/p99 latency metrics for 100-actor scenarios.
- [x] Document the "Zero Overhead" measurement principle.

## Milestone 1: Profiler/Benchmark Truth [DONE]
- [x] Decouple engine compute costs from frame pacing and replay serialization.
- [x] Implement Kernel status signal recording for phase-based profiling.
- [x] Validate measurement integrity via profiler integrity tests.

## Milestone 2: Memory & Object Churn [DONE]
- [x] Reduce `dataclasses.replace` overhead in the hot path.
- [x] Implement lazy reconstruction for `AuthoritativeState`.
- [x] Audit component instantiation costs.

## Milestone 3: O(Dirty) Parity Verification [DONE]
- [x] Implement `DirtySet` for incremental state tracking.
- [x] Verify semantic parity between full-scan and dirty-scan modes.
- [x] Ensure 100% parity across idle, movement, resource, and combat scenarios.

## Milestone 4: Concurrency & Determinism [DONE]
- [x] Validate deterministic resolution across varying worker counts.
- [x] Fix race conditions in proposal aggregation.
- [x] Implement chunk-size tuning based on measured overhead.

## Milestone 5: Reporting & Matrix Expansion [DONE]
- [x] Normalize scenario builders for consistent measurement.
- [x] Implement the reporting layer (comparison matrix).
- [x] Expand benchmarks to cover `mixed_200` stress tests.

## Milestone 6: Baseline Schema & Regression Gate [DONE]
- [x] Commit stable performance baselines in `tests/perf/baselines/`.
- [x] Implement the `check_perf_regression.py` CI gate.
- [x] Define dual-threshold (absolute + relative) regression laws.

## Milestone 7: Optimization Phase (Hot Path Hardening) [DONE]
- [x] **Incremental DirtySet**: Updated `AuthoritativeApplyPipeline` and `DirtySet` to support incremental derivation, reducing redundant scans.
- [x] **Strategic Hot-Path**: Optimized `StrategicIntelligenceSystem` by pre-parsing coordinate strings and using O(1) inventory count lookups.
- [x] **Region ID Propagation**: Reduced redundant spatial lookups in `ApplyPath` by propagating `region_id` from movement resolution.
- [x] **Results**: Achieved ~46% reduction in `mixed_200_local` p95 compute time (28.2ms -> 15.2ms).

## Milestone 8: Documentation & Checklist Reconciliation [DONE]
- [x] Align `performance_contract.md` with new engine laws.
- [x] Verify all PERF checklist items have associated proof paths.
- [x] Establish developer guide for performance-safe extensions.

## Milestone 9: Memory Management & Pooling [DONE]
- [x] Implement differential readonly caching for $O(Dirty)$ view reconstruction.
- [x] Optimize `ApplyPath` for cross-tick cache persistence.
- [x] Integrate `EMPTY_ENTITY_UPDATE` singletons to minimize object churn.
- [x] Implement `deep_freeze` caching for shared world components.

## Milestone 10: Production Tuning & Stress-Testing [DONE]
- [x] Define calibrated production resource profiles (PROD_SMALL to PROD_STRESS).
- [x] Implement incremental GC in `Kernel` to smooth out P95 spikes.
- [x] Validate 10,000-entity stability under stress scenarios.
- [x] Document finalized latency p99 guarantees (PROD_STRESS budget: 500ms).

---

## Exit Condition
The engine meets production-grade performance targets with a robust, automated regression gate that prevents performance drift.
