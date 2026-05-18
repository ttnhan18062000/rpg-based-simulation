# Investigation: Cache Lifecycle and Memory Boundaries (Milestone 19)

## 1. Background & Problem Statement
Optimization mechanisms introduced in earlier milestones rely heavily on in-memory caching:
- `MovementPlanCache` caches tile-by-tile pathing steps for entities.
- `ReadModelCache` caches API DTO projections to eliminate O(N) allocation during status checks.
- `AuthoritativeState` caches spatial grids, region lists, and node maps.

While `MovementPlanCache` invalidates entries when entities move, and `ReadModelCache` invalidates dirty entities, there is no centralized governance over total cache memory footprints. Under extreme scenarios (e.g., thousands of entities entering and leaving simulation regions over days), orphaned entries or large cached structures could exceed RAM budgets or cause unpredictable GC pauses.

Milestone 19 introduces a formal `CacheRegistry` and `CacheBudgetPolicy` to provide unified observability, bounded capacities, and deterministic eviction.

## 2. Existing Caching Implementations & Reuse Opportunities
- `src/engine/movement_cache.py`: `MovementPlanCache` has `_cache`, `hits`, `misses`, `occupancy_version`. Needs eviction tracking and invalidation tick tracking.
- `src/api/read_model_cache.py`: `ReadModelCache` has `_entity_dtos`, `_hits`, `_misses`, `_invalidations`. Needs eviction tracking and invalidation tick tracking.
- `src/core/state.py`: `AuthoritativeState` caches spatial grids and maps on demand (`_spatial_grid_cache`, `_region_list_cache`, etc.). Can be registered as a spatial cache wrapper.

## 3. Technical Requirements
1. **Standardized Interface (`ICacheable`)**: Every cache must expose `get_metrics()`, `evict_expired(current_tick, policy)`, and `clear()`.
2. **Central Registry (`CacheRegistry`)**: Maintains weak references or explicit references to active caches in the simulation.
3. **Budget Policy (`CacheBudgetPolicy`)**: Defines limits like `max_movement_plans = 5000`, `max_read_dtos = 2000`, etc. When a cache exceeds its budget during `CacheRegistry.sweep_caches()`, LRU or deterministic FIFO eviction must prune excess entries.
4. **Integration in Kernel**: During `_phase_cleanup`, `Kernel` invokes `self._cache_registry.sweep_caches(self._state.tick)` to keep all caches within their memory boundaries.
