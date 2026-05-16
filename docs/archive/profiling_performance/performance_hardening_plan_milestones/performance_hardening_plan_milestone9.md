# Milestone 9 — Memory Management & Pooling

## Goal
Reduce object allocation pressure and garbage collection latency during high-density simulations (5,000+ entities) by implementing differential caching and object recycling.

## Tasks

| Task | Implementation Logic |
| :--- | :--- |
| M9.1 Differential Caching | Shift `AuthoritativeState.to_readonly` from $O(N)$ rebuild to $O(Dirty)$ update. |
| M9.2 Cache Carry-over | Modify `ApplyPath` to persist readonly entity caches across simulation generations. |
| M9.3 Update Singletons | Implement `EMPTY_ENTITY_UPDATE` to eliminate no-op allocations per tick. |
| M9.4 Deep-Freeze Cache | Implement identity-based caching for `deep_freeze` on shared world components. |

## Acceptance Checklist
- [x] `to_readonly()` avoids full dict reconstruction for unchanged entities.
- [x] Memory profiling confirms stable RSS during idle ticks at scale 5000.
- [x] Bit-identical determinism is preserved with caching enabled.
- [x] `EMPTY_ENTITY_UPDATE` is used by all authoritative executors for no-op result signals.

## Exit Condition
The engine achieves a >10x reduction in state view generation latency for large-scale simulations.
