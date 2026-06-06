# TCK-20260517-OCCUPANCY-SNAPSHOT

## Title

OccupancySnapshot Implementation for Stable Per-Tick Spatial Read Model

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `OccupancySnapshot` to provide an immutable, stable read model for entity tile occupancy and priority per tick, eliminating redundant recalculations during movement and legality checks.

## Scope

- Implement `OccupancySnapshot` in `src/engine/occupancy_snapshot.py`.
- Support `from_state(state)` factory method to build snapshot for the current tick.
- Cache `occupancy_by_tile` and `priority_by_entity` inside the immutable dataclass.
- Provide `occupant_at(tile)` and `is_occupied(tile)` query methods.
- Provide `get_priority(entity_id)` query method.
- Create comprehensive unit test suite in `tests/unit/optimization/test_occupancy_snapshot.py`.

## Out of Scope

- Modifying combat rules or pathfinding algorithms.

## Acceptance Criteria

- [x] Snapshot matches current state positions.
- [x] Snapshot is immutable for the tick.
- [x] Snapshot rebuilds after state advances.
- [x] Movement legality using snapshot matches existing legality result.

## Related Tickets

- TCK-20260517-MOVEMENT-CANDIDATE-SELECTOR.md

## Related Docs

- perf_test_plan.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260517-OCCUPANCY-SNAPSHOT/

## Related Code Areas

- src/engine/occupancy_snapshot.py
- src/engine/legality.py
- tests/unit/optimization/test_occupancy_snapshot.py

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `OccupancySnapshot` frozen dataclass providing O(1) immutable lookups for tile occupancy and tie-breaking priority.
- Initialized automatically at the start of `AuthoritativeApplyPipeline.refine` and `Kernel._phase_init`.
- Integrated seamlessly into `LegalityServiceV2` and `MovementSystem`.

## Test Summary

- Run `pytest tests/unit/optimization/test_occupancy_snapshot.py -v`: 6/6 passed (0.16s).
- Run full regression suite `pytest tests/unit/ -m "not slow"`: 762/762 passed (13.44s).

## Files Changed

- src/engine/occupancy_snapshot.py
- src/core/state.py
- src/engine/kernel.py
- src/engine/pipeline.py
- src/engine/legality.py
- src/engine/movement.py
- tests/unit/optimization/test_occupancy_snapshot.py

## Completion Summary

- `OccupancySnapshot` successfully implemented, tested, and integrated into the authoritative V2 simulation pipeline, ensuring per-tick spatial query stability and O(1) performance.
