# Test Plan: MovementPlanCache

## Unit Tests (`tests/unit/optimization/test_movement_plan_cache.py`)
Verify all requirements specified in `perf_test_plan.md`:
1. `test_plan_cache_reuses_plan_when_key_unchanged()`: Verify cache returns the cached plan when tick < valid_until_tick and key matches.
2. `test_plan_cache_invalidates_when_entity_moves()`: Calling `invalidate_for_dirty` with `dirty.movement_entities` containing the entity invalidates its cached plan.
3. `test_plan_cache_invalidates_when_target_changes()`: Changing `target_tile` produces a different key, resulting in cache miss.
4. `test_plan_cache_invalidates_when_occupancy_version_changes()`: When `dirty.movement_entities` is non-empty, `occupancy_version` increments, invalidating keys with old versions.
5. `test_plan_cache_does_not_reuse_blocked_step()`: If a move is blocked or illegal, it is not cached or used.
6. `test_cached_movement_plan_matches_uncached_resolution()`: Calling `MovementSystem.resolve_move` twice with identical state and target produces identical results, utilizing the cache on the second call.

## Regression Suite
Run `pytest tests/unit/ -m "not slow"` to ensure zero regressions across all 750+ tests.
