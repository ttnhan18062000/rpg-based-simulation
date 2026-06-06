# TCK-20260518-CACHE-INVALIDATION-POLICY

## Title

CacheInvalidationPolicy Implementation and Centralized Invalidation Rules

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `invalidated_indexes` in `CacheInvalidationPolicy` to centralize dirty-domain cache invalidation rules and verify with a comprehensive unit test suite.

## Scope

- Add `invalidated_indexes(dirty: DirtySet) -> set[str]` to `CacheInvalidationPolicy` in `src/engine/world_index.py`.
- Map dirty sets (`resource_node_ids`, `building_ids`, `movement_entities`, `ground_item_ids`, `corpse_ids`, `region_ids`) to their corresponding index names (`active_resource_node_index`, `building_kind_index`, `entity_position_index`, `occupancy_snapshot`, `ground_item_index`, `corpse_index`, `region_index`).
- Create comprehensive unit test suite `tests/unit/optimization/test_cache_invalidation_policy.py`.

## Out of Scope

- Modifying dirty set generation logic.

## Acceptance Criteria

- [x] Invalidation rules are centralized.
- [x] No cache owns private invalidation logic.
- [x] WorldIndexService uses this policy.

## Related Tickets

- TCK-20260517-WORLD-INDEX-SERVICE.md

## Related Docs

- perf_test_plan.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260518-CACHE-INVALIDATION-POLICY/

## Related Code Areas

- src/engine/world_index.py
- tests/unit/optimization/test_cache_invalidation_policy.py

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `invalidated_indexes(dirty)` returning exactly the set of index names mapped from dirty sets.
- Aligned `should_invalidate(domain, dirty)` with `invalidated_indexes`.
- Added comprehensive unit tests covering all 6 dirty domains, empty sets, and None fallbacks.

## Test Summary

- Run `pytest tests/unit/optimization/test_cache_invalidation_policy.py`: 7/7 passed in 0.08s.
- Run full regression suite `pytest tests/unit/ -m "not slow"`: 785/785 passed in 12.77s.

## Files Changed

- src/engine/world_index.py
- tests/unit/optimization/test_cache_invalidation_policy.py [NEW]

## Completion Summary

Successfully completed Milestone 11. All spatial index and cache invalidation rules are now strictly centralized inside `CacheInvalidationPolicy`, ensuring flawless consistency and zero private/ad-hoc invalidation logic across the engine.
