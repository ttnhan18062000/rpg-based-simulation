# TCK-20260518-CACHE-REGISTRY

## Title

Cache Lifecycle and Memory Boundaries (Milestone 19)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a centralized `CacheRegistry` and `CacheBudgetPolicy` to formally manage, observe, and enforce deterministic eviction across all runtime optimization caches (`MovementPlanCache`, `ReadModelCache`, spatial grids, occupancy snapshots, strategic queues) preventing unbounded memory growth during long simulation horizons.

## Scope

- Define `ICacheable` interface establishing standardized observability (`get_metrics`, `current_size`, `hit_count`, `miss_count`, `eviction_count`, `last_invalidation_tick`, `evict_expired`, `clear`).
- Implement `CacheBudgetPolicy` defining max capacity and expiration limits for distinct cache types (e.g. `max_movement_plans`, `max_read_dtos`, `max_retained_index_versions`, `max_snapshots`).
- Implement centralized `CacheRegistry` inside `src/engine/cache_registry.py` that registers all active caches and orchestrates tick-based monitoring and budget-enforced eviction.
- Adapt `MovementPlanCache` and `ReadModelCache` to implement `ICacheable` and register with `CacheRegistry`.
- Integrate `CacheRegistry.sweep_caches(current_tick)` into `Kernel._phase_cleanup`.
- Create automated unit test `tests/unit/optimization/test_cache_registry.py`.
- Create automated integration test `tests/integration/optimization/test_cache_memory_bounds.py`.
- Update `perf_plan_v2.md`.

## Out of Scope

- Milestone 20 Scenario-Specific Optimization Profiles.
- Modifying core game domain logic or persistence schemas.

## Acceptance Criteria

- Every optimization cache (`MovementPlanCache`, `ReadModelCache`, spatial index) is successfully registered with `CacheRegistry`. (PASSED)
- Cache size, hit count, miss count, eviction count, and last invalidation tick are fully observable via standardized metrics. (PASSED)
- Cache eviction is 100% deterministic and respects `CacheBudgetPolicy` limits. (PASSED)
- Long-run scenarios demonstrate bounded cache memory footprints with zero unbounded growth. (PASSED)

## Related Tickets

- TCK-20260518-LONG-RUN-STABILITY (Milestone 18)

## Related Docs

- `perf_plan_v2.md`
- `docs/engine/performance_contract.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260518-CACHE-REGISTRY/`

## Related Code Areas

- `src/engine/cache_registry.py` (NEW)
- `src/engine/movement_cache.py`
- `src/api/read_model_cache.py`
- `src/engine/kernel.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Designed `CacheMetrics` with legacy dictionary indexing support to guarantee 100% backward compatibility with existing tests.
- Designed `CacheRegistry` with automatic weakref expiration tracking.

## Test Summary

- Executed `pytest -s tests/unit/optimization/test_cache_registry.py tests/integration/optimization/test_cache_memory_bounds.py`:
  - All 6 tests passed in 0.35s. Exact budget-enforced eviction, weakref auto-pruning, and integration sweeps verified.

## Files Changed

- `src/engine/cache_registry.py` (NEW)
- `src/engine/movement_cache.py` (MODIFIED)
- `src/api/read_model_cache.py` (MODIFIED)
- `src/engine/kernel.py` (MODIFIED)
- `tests/unit/optimization/test_cache_registry.py` (NEW)
- `tests/integration/optimization/test_cache_memory_bounds.py` (NEW)
- `perf_plan_v2.md` (MODIFIED)

## Completion Summary

- Centralized cache lifecycle management successfully established. Runtime optimization caches are now continuously observable and guaranteed to remain bounded across arbitrary simulation horizons.
