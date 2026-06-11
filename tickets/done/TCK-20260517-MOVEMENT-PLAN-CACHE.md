---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260517-MOVEMENT-PLAN-CACHE
phase: done
date: 2026-05-17
tags: [movement, plan, cache]
---


# TCK-20260517-MOVEMENT-PLAN-CACHE

## Title

MovementPlanCache Implementation for Spatial Routing Recomputation Optimization

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `MovementPlanCache` to cache next-step movement decisions when entity position, target position, and local occupancy conditions remain unchanged, reducing A* and flow-field navigation calculations.

## Scope

- Create `MovementPlanCache`, `MovementPlanKey`, and `MovementPlan` in `src/engine/movement_cache.py`.
- Support `get(key, current_tick)` and `put(key, plan)` methods.
- Support `invalidate_for_dirty(dirty: DirtySet)` to track occupancy version and invalidate moved entities.
- Ensure blocked movements (failed legality checks) are not cached or reused.
- Integrate cache into `MovementSystem.resolve_move` and pipeline refinement.
- Implement unit test suite in `tests/unit/optimization/test_movement_plan_cache.py`.

## Out of Scope

- Modifying combat rules or pathfinding algorithms.

## Acceptance Criteria

- [x] Cache hit produces same next step as uncached logic.
- [x] Cache invalidates on movement, target change, and occupancy change.
- [x] Cache cannot reuse blocked movement.

## Related Tickets

- TCK-20260517-OCCUPANCY-SNAPSHOT.md

## Related Docs

- perf_test_plan.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260517-MOVEMENT-PLAN-CACHE/

## Related Code Areas

- src/engine/movement_cache.py
- src/engine/movement.py
- src/core/state.py
- src/engine/pipeline.py
- src/engine/apply.py
- tests/unit/optimization/test_movement_plan_cache.py

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `MovementPlanCache` tracking cached movement plans and global occupancy versions.
- Attached `movement_cache` to `AuthoritativeState` and preserved it across readonly view copies and generation updates.
- Integrated cache eviction on pipeline dirty set derivation.

## Test Summary

- Run `pytest tests/unit/optimization/test_movement_plan_cache.py -v`: 6/6 passed (0.27s).
- Run full regression suite `pytest tests/unit/ -m "not slow"`: 768/768 passed (13.54s).

## Files Changed

- src/engine/movement_cache.py
- src/engine/movement.py
- src/core/state.py
- src/engine/pipeline.py
- src/engine/apply.py
- tests/unit/optimization/test_movement_plan_cache.py

## Completion Summary

- `MovementPlanCache` successfully implemented, tested, and integrated into the authoritative V2 simulation engine, providing O(1) cached routing decisions under stable occupancy and navigation conditions.
