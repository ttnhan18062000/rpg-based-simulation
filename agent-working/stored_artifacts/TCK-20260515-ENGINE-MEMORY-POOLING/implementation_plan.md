---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [engine, memory, pooling]
---

# Milestone 9: Memory Management & Pooling

## Goal Description
The objective of this milestone is to harden the engine's memory performance by reducing the number of object allocations per tick. In high-density simulations (5,000+ entities), the overhead of creating new state views and update objects every tick leads to significant GC pressure and latency spikes.

## Proposed Changes

### [Engine Core]
#### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Update `AuthoritativeState` to support persistent cache carry-over.
- Modify `to_readonly()` to perform differential updates instead of a full dictionary rebuild.

#### [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Update `apply_generation` to carry over the `_readonly_entities_cache` from the prior state.
- Implement invalidation logic based on the `DirtySet`.

### [Execution Optimization]
#### [MODIFY] [executor.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py)
- Implement `EMPTY_ENTITY_UPDATE` singleton to avoid no-op allocations.
- Optimize `ConcurrentExecutionAdapter` to recycle shared world data across `WorkerPacket` creations.

#### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Add `EMPTY_ENTITY_UPDATE` constant.
- Ensure all update sub-classes use `__slots__` (already done, but verify compliance).

## Verification Plan

### Automated Tests
- **Memory Profiling**: Use `scratch/measure_memory.py` to compare object allocation counts before and after changes.
- **Regression Suite**: Run `scripts/run_benchmarks.py --smoke` to ensure no semantic regressions.
- **Determinism Check**: Verify that hashes remain identical with caching enabled.

### Manual Verification
- Monitor RSS (Resident Set Size) growth during a 1000-tick stress test at scale 5000.
