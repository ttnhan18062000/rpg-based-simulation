# Test Plan: Cache Lifecycle and Memory Boundaries (Milestone 19)

## 1. Test Targets
- `CacheRegistry` and `CacheBudgetPolicy` in `src/engine/cache_registry.py`.
- `MovementPlanCache` in `src/engine/movement_cache.py`.
- `ReadModelCache` in `src/api/read_model_cache.py`.

## 2. Automated Test Cases

### Unit Tests (`test_cache_registry.py`)
1. **`test_cache_registration_and_metrics`**:
   - Instantiate `CacheRegistry`, register mock caches and real `MovementPlanCache`.
   - Verify `get_all_metrics()` returns precise current_size, hit_count, miss_count, eviction_count, and last_invalidation_tick.
2. **`test_cache_budget_eviction`**:
   - Register `MovementPlanCache` with 20 items.
   - Sweep with `CacheBudgetPolicy(max_movement_plans=10)`.
   - Assert cache size drops to exactly 10 and eviction_count increments by 10.
3. **`test_read_model_cache_eviction`**:
   - Populate `ReadModelCache` with 50 entity DTOs.
   - Sweep with `CacheBudgetPolicy(max_read_dtos=25)`.
   - Assert cache size drops to exactly 25 and metrics correctly reflect eviction.

### Integration Tests (`test_cache_memory_bounds.py`)
1. **`test_kernel_integrated_cache_sweep`**:
   - Initialize simulation kernel with 100 entities moving dynamically.
   - Attach `CacheRegistry` with strict budget (e.g. max movement plans = 20).
   - Run 100 ticks.
   - Assert that at tick termination, movement plan cache and read model cache never exceed their budget limits.

## 3. Execution Scope
Run via pytest:
```bash
pytest -s tests/unit/optimization/test_cache_registry.py
pytest -s tests/integration/optimization/test_cache_memory_bounds.py
```
