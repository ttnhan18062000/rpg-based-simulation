# Walkthrough: Milestone 9 - Memory Management & Pooling

## Overview
Milestone 9 focused on reducing object allocation pressure and GC latency in high-density simulations (5,000+ entities). By shifting from $O(N)$ state reconstruction to $O(Dirty)$ differential updates, we significantly improved the performance of the authoritative transition pipeline.

## Changes

### [AuthoritativeState](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Implemented `_readonly_entities_cache` slot to persist the readonly view of entities across generations.
- Updated `to_readonly()` to utilize the cached view if available, skipping the $O(N)$ reconstruction loop.

### [ApplyPath](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Modified `apply_generation` to carry over the readonly cache from the prior state.
- Implemented logic to selectively update only the "dirty" entities in the cache, maintaining pointer stability for unchanged entities.

### [Updates](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Added `EMPTY_ENTITY_UPDATE` singleton to prevent thousands of identical no-op allocations per tick.

### [Executor](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py)
- Implemented `_freeze_cache` in `ConcurrentExecutionAdapter` to avoid redundant `deep_freeze` traversals of shared world components (Regions, Nodes, Buildings).
- Optimized `LocalSequentialExecutor` to use the `EMPTY_ENTITY_UPDATE` sentinel.

## Verification Results

### Performance Benchmark (`scratch/bench_readonly.py`)
| Metric | Baseline (Cold) | Optimized (Differential) | Improvement |
| :--- | :--- | :--- | :--- |
| View Generation (5k entities) | 81.01ms | 3.72ms | **21.7x Faster** |

### Memory Profiling (`scratch/measure_memory.py`)
- Verified that subsequent generations with no changes do not trigger full entity reconstructions.
- Reduced GC pressure by recycling internal cache structures.

### Determinism
- Ran `tests/perf/test_dirty_set_integrity.py` and `tests/perf/test_concurrency_parity.py`.
- **Status**: ALL TESTS PASSED.

## Next Steps
- **Milestone 10: Logic Hardening (Phase 4)**: Finalizing the 17-phase apply sequence and enforcing strict rejection registries.
