# Performance Report: V2 RPG Engine Hardening (2026-05-14)

## Status: CERTIFIED (Phase 3)

## Summary
Phase 3 of the V2 RPG Engine performance hardening has been completed, targeting object churn and spatial lookup overhead. The core simulation tick for 1,000 entities now consistently stabilizes within the 50ms budget (avg ~45ms) for simulation logic.

## Key Optimizations (Phase 3)
1. **Lazy State Reconstruction**:
   - `AuthoritativeState` now caches its read-only entity view (`_readonly_entities_cache`).
   - Rebuilding the entities dictionary is skipped if no mutations occurred during the tick.
2. **Lazy Mutation Pipeline**:
   - `ApplyPath.apply_partial` now defers cloning the entities dictionary until an actual update is committed.
3. **Cached Regional Lookups**:
   - Entities now cache their `region_id` in `NavigationComponent`.
   - `apply_passive` uses this cache for $O(1)$ region retrieval, eliminating $O(N)$ spatial scans.
4. **Spatial LoS Optimization**:
   - `LegalityServiceV2.has_line_of_sight` now uses the `building_tiles` spatial index for $O(1)$ obstruction detection, removing a major bottleneck in tactical scenarios.

## Benchmark Results (IDLE_1000)

| Metric | Phase 2 (2026-05-13) | Phase 3 (2026-05-14) | Improvement |
| :--- | :--- | :--- | :--- |
| **`to_readonly`** | ~45ms | **~13ms** | **~71%** |
| **`apply_passive`** | ~35ms | **~18ms** | **~48%** |
| **Total Sim Tick** | ~90ms | **~45ms** | **~50%** |

## Verification
- **Integrity**: `tests/unit/kernel/test_performance_integrity.py` confirms that lazy reconstruction does not break state contracts.
- **Determinism**: 100% pass rate on `tests/integration/pipeline/test_replay_determinism.py` with audit mode enforced.
- **Coverage**: All regression tests for combat, movement, and progression remain passing.

## Next Steps
- **Phase 4**: Parallelize pathfinding within the worker execution phase.
- **Persistence Hardening**: Optimize `CanonicalStateHasher.get_hash` to reduce JSON serialization and sorting overhead during the checkpoint phase.
