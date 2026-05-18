# Phase 3 Performance Hardening Walkthrough

## Overview
Phase 3 focused on reducing compute time and object churn in the authoritative simulation tick for 1,000+ entities. By implementing lazy reconstruction patterns and spatial indexing, we achieved a ~50% reduction in simulation tick duration.

## Key Changes

### 1. Authoritative State Caching
- **`AuthoritativeState._readonly_entities_cache`**: Added an internal cache for the `ReadOnlyDict` of entities. Since the passive phase often results in many entities remaining identical (no-op updates), we now reuse the previous tick's dictionary object if no mutations occurred.
- **`AuthoritativeState.to_readonly()`**: Optimized to hit this cache, reducing dictionary reconstruction time from ~45ms to ~13ms for 1,000 entities.

### 2. Apply Pipeline Optimizations
- **Lazy `ApplyPath.apply_partial`**: Refactored the authoritative mutation loop to defer the expensive `dict(state.entities)` clone until an actual update or removal is detected.
- **Cached `region_id`**: Added a cached `region_id` to `NavigationComponent`. This allows `apply_passive` to perform $O(1)$ regional lookups instead of $O(N)$ spatial scans for every entity on every tick.
- **Spatial Index for LoS**: Refactored `LegalityServiceV2.has_line_of_sight` to use the `building_tiles` spatial index. This removes the bottleneck of scanning all building objects during the Bresenham check.

### 3. Bug Fixes & Regression Guards
- **Determinism Fix**: Corrected a regression in `test_replay_determinism.py` where `audit_mode` was not being enforced during replay, leading to trace mismatches.
- **Performance Integrity Suite**: Added `tests/unit/kernel/test_performance_integrity.py` to ensure that optimizations (like lazy dicts) do not violate the core authoritative contract.

## Performance Metrics (IDLE_1000)

| Phase | Before (Phase 2) | After (Phase 3) | Improvement |
| :--- | :--- | :--- | :--- |
| **`to_readonly`** | ~45ms | **~13ms** | **~71%** |
| **`apply_passive`** | ~35ms | **~18ms** | **~48%** |
| **Total Tick (Sim)** | ~90ms | **~45ms** | **~50%** |

## Next Steps
- **Phase 4**: Implement movement congestion recovery and parallel pathfinding refinement.
- **Persistence Optimization**: Investigate reducing the overhead of `checkpoint.get_hash` and `asdict` which currently consume significant time during the persistence phase.
