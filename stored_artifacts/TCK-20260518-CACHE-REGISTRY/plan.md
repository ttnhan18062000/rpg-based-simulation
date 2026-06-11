---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260518-CACHE-REGISTRY
artifact_type: plan
tags: [cache, registry]
---

# Plan: Cache Lifecycle and Memory Boundaries (Milestone 19)

## 1. Architectural Design

### Standardized Interface: `ICacheable`
```python
class ICacheable(Protocol):
    def get_metrics(self) -> CacheMetrics: ...
    def evict_expired(self, current_tick: int, policy: CacheBudgetPolicy) -> int: ...
    def clear(self) -> None: ...
```
`CacheMetrics` dataclass:
- `name`: str
- `current_size`: int
- `hit_count`: int
- `miss_count`: int
- `eviction_count`: int
- `last_invalidation_tick`: int

### Budget Policy: `CacheBudgetPolicy`
A dataclass defining capacity limits:
- `max_movement_plans`: int = 10000
- `max_read_dtos`: int = 5000
- `max_spatial_grid_versions`: int = 10
- `max_strategic_queues`: int = 5000
- `sweep_interval_ticks`: int = 10

### Central Registry: `CacheRegistry`
Located in `src/engine/cache_registry.py`:
- `register_cache(name: str, cache: ICacheable) -> None`
- `get_all_metrics() -> Dict[str, CacheMetrics]`
- `sweep_caches(current_tick: int, policy: CacheBudgetPolicy) -> Dict[str, int]` (Returns eviction counts per cache)
- `clear_all() -> None`

## 2. Adaptation & Integration
1. **`MovementPlanCache`**: Add `_eviction_count`, `_last_invalidation_tick`, and implement `get_metrics()`, `evict_expired(current_tick, policy)`. If `len(_cache) > policy.max_movement_plans`, evict oldest entries (using insertion order or valid_until_tick).
2. **`ReadModelCache`**: Add `_eviction_count`, `_last_invalidation_tick`, and implement `get_metrics()`, `evict_expired(current_tick, policy)`. If `len(_entity_dtos) > policy.max_read_dtos`, evict oldest accessed/inserted DTOs.
3. **`Kernel` Integration**: Add `self._cache_registry = CacheRegistry()` and `self._cache_policy = CacheBudgetPolicy()`. During kernel initialization, register `self._state.movement_cache` and any engine manager read caches. In `_phase_cleanup`, if `t % policy.sweep_interval_ticks == 0`, invoke `sweep_caches`.

## 3. Deliverables & Testing
1. `src/engine/cache_registry.py` (NEW): Defines interfaces, policy, and registry.
2. `tests/unit/optimization/test_cache_registry.py` (NEW): Unit tests asserting registration, metric observability, and exact budget eviction.
3. `tests/integration/optimization/test_cache_memory_bounds.py` (NEW): Integration tests running simulation ticks under a constrained `CacheBudgetPolicy` ensuring caches stay perfectly within configured boundaries.

## 4. Verification Plan
- Execute `pytest -s tests/unit/optimization/test_cache_registry.py`.
- Execute `pytest -s tests/integration/optimization/test_cache_memory_bounds.py`.
