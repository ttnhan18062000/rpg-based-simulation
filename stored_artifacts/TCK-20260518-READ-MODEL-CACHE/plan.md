# Plan: Read Model and API Projection Optimization

## Objective
Implement Milestone 12 as defined in `perf_plan.md` to cache API read models and drive DTO invalidation via `DirtySet`.

## Proposed Architecture

```
+-------------------+        state + dirty_set        +----------------------------+
|    V2 Kernel      | ------------------------------> |      ReadModelCache        |
+-------------------+                                 +----------------------------+
                                                            |               |
                                     invalidate dirty IDs   |               | cache DTOs
                                                            v               v
                                            +---------------------+   +---------------------+
                                            | InvalidationPolicy  |   | Cached Entity DTOs  |
                                            +---------------------+   +---------------------+
                                                                                ^
                                                                                | O(1) read
                                                                      +---------------------+
                                                                      |   V2EngineManager   |
                                                                      +---------------------+
```

### 1. `src/api/read_model_cache.py`
Create `ReadModelInvalidationPolicy`:
- Method `get_dirty_entity_ids(dirty_set: Optional[DirtySet], all_entity_ids: Set[int]) -> Set[int]`.
- If `dirty_set` is None or `force_full_scan` is active, return `all_entity_ids` (invalidate all).
- Otherwise, return the union of all entity-related dirty fields (`movement_entities | combat_entities | inventory_entities | strategic_entities | social_entities | biological_entities | lifecycle_entities | attributes_entities`).

Create `ReadModelCache`:
- `_minimal_summary: Dict[str, Any]`
- `_entity_dtos: Dict[int, Dict[str, Any]]`
- `_region_dtos: Dict[int, Dict[str, Any]]`
- `_tick: int`
- `_hits: int = 0`
- `_misses: int = 0`
- `_invalidations: int = 0`

Methods:
- `update(state: AuthoritativeState, dirty_set: Optional[DirtySet], force_full_scan: bool = False)`:
  - Updates `_minimal_summary`.
  - Determines dirty entity IDs via `ReadModelInvalidationPolicy`.
  - Removes dirty IDs from `_entity_dtos` (or proactively regenerates them).
  - Updates metrics (`_invalidations += len(dirty_ids)`).
- `get_entity_dto(entity: EntityState) -> Dict[str, Any]`:
  - If `entity.id` in `_entity_dtos`, `_hits += 1`, return cached copy.
  - Else, `_misses += 1`, generate via `StatePresenter.present_entity(entity)`, store in `_entity_dtos`, and return.
- `get_entities_paged(state: AuthoritativeState, offset: int, limit: int) -> Dict[str, Any]`:
  - Retrieves sorted IDs, slices page, calls `get_entity_dto` for each entity in the page.
- `get_metrics() -> Dict[str, int]`: Return hits, misses, invalidations.

### 2. `src/api/engine_manager.py`
Integrate `ReadModelCache`:
- In `__init__`, instantiate `self._read_cache = ReadModelCache()`.
- In `_update_latest_state(state)`, pass `state` and the kernel's active `dirty_set` (from `self._kernel.status.dirty_set` if available) to `self._read_cache.update(state, dirty_set)`.
- Update `get_state()`, `get_entity()`, `get_entities_paged()` to read from `self._read_cache`.

### 3. Testing Suite
- `tests/unit/api/test_read_model_cache.py`: Unit test verifying cache hit/miss counting, selective invalidation on dirty domains, and fallback to full rebuild when `dirty_set` is None.
- `tests/perf/test_api_projection_perf.py`: Performance benchmark comparing repeated paged retrieval with and without `ReadModelCache`.
