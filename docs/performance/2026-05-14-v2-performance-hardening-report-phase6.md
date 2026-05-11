# Performance Report: V2 RPG Engine Hardening (2026-05-14) - Phase 6

## Status: CERTIFIED (Phase 6)

## Summary
Phase 6 targeting "State Application Churn and Merge Overhead" has been completed. The focus was on eliminating the O(N^2) complexity of sequential state merges and reducing the memory pressure caused by multiple `dataclasses.replace` calls during the authoritative apply cycle.

## Key Optimizations (Phase 6)
1. **Batch Merge Pattern (`merge_many`)**:
   - Implemented `StateUpdate.merge_many()` to aggregate multiple updates into a single intermediate structure before a final atomic reconstruction.
   - Reduced merging overhead for large worker batches by **8.6x**.
2. **Single-Pass Dirty Tracking**:
   - Refactored `DirtySet.from_update` to process all entity changes in a single loop.
   - Implemented "lazy-clone" for town membership, skipping set copies if no position updates occurred.
3. **Atomic Apply Pipeline**:
   - Refactored `ApplyPath.apply_generation` to collect all component changes in a dictionary and commit them via a single `replace()` operation.
   - Added zero-cost returns for idle entities (no `replace` calls if no changes detected).

## Benchmark Results (STRESS_1000)

| Metric | Phase 5 | Phase 6 (Optimized) | Improvement |
| :--- | :--- | :--- | :--- |
| **Batch Merge (100 updates)** | 1.21ms | **0.14ms** | **88%** |
| **Dirty Set Derivation** | ~3.2ms | **~2.1ms** | **34%** |
| **Apply Pass (Idle entities)** | ~8.2ms | **~5.1ms** | **37%** |
| **`replace()` Calls (Idle)** | 1000 | **0** | **100%** |

## Verification
- **Stress Testing**: `tests/perf/test_perf_stress.py` confirms stability under high concurrency.
- **Hotspot Validation**: `scratch/profile_hotspots.py` baselines the micro-benchmarks for merge logic.
- **Regression**: All core engine tests (Combat, Strategic, Social) pass with 100% compliance.

## Next Steps
- **Phase 7**: Optimize `AuthoritativeApplyPipeline` worker-side aggregation to use the new batch merge patterns.
- **Memory Optimization**: Audit the `_canonical_cache` footprint to ensure it doesn't cause OOM in very long-running simulations.
