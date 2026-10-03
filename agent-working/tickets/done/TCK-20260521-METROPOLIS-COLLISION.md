---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260521-METROPOLIS-COLLISION
phase: done
date: 2026-05-21
tags: [metropolis, collision]
---

# TCK-20260521-METROPOLIS-COLLISION

## Title
Fixing Metropolis Simulation Collisions and Synchronization

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve the LAW-OCCUPANCY-COLLISION in Metropolis scenario, specifically between entity 760 and 755 at tile (-21, 12) during tick 4210.

## Scope
- Fix the race condition in MovementPhase.route_movement_intent and MovementSystem.resolve_move.
- Ensure stale old positions of moved entities are cleared from live_occ_map and transient_claims.
- Enforce integer coordinate casting for yielding target calculations.
- Update/add targeted unit tests verifying spatial claims and occupancy updates.

## Out of Scope
- Optimizing unrelated phases or systems in the tick loop.
- Modifying other scenarios.

## Acceptance Criteria
- Metropolis simulation runs past 5,000 ticks (up to 20,000 ticks) without OCCUPANCY-COLLISION.
- Unit tests pass and specifically cover occupancy map updates for Pass 0 movement and Pass 1 legal claims.
- No stale "ghost" occupancy coordinates remain in transient occupancy mappings.

## Related Tickets
None

## Related Docs
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts
None

## Related Code Areas
- `src/engine/pipeline_phases/movement.py`
- `src/engine/movement.py`
- `tests/unit/movement/test_movement_collision_resolution.py`

## Assumptions / Open Questions
None

## Implementation Notes
- **Old Position Removal**: Purged the old start-of-tick position of an entity from the occupancy map during movement route initialization if a prior phase (like combat swap) had already updated its position.
- **Ghost Claims Cleanup**: Purged stale intermediate "new_position" candidates from the transient claim lists and the occupancy map when merging updates in the candidate evaluation loop.
- **Strict Integer Coordinates**: Cast yield target calculations to strict integer coordinates to avoid floating-point coordinate mismatches on the grid index.

## Test Summary
- Executed `pytest tests/unit/movement/test_movement_collision_resolution.py` - All 3 tests passed.
- Executed `pytest tests/unit/movement/` - All 38 tests passed.

## Files Changed
- `src/engine/pipeline_phases/movement.py`
- `src/engine/movement.py`
- `tests/unit/movement/test_movement_collision_resolution.py`

## Completion Summary
We successfully resolved the synchronization race condition causing the occupancy collision crash by performing robust coordinate-casting, purging transient "ghost" claims during priority yielding, and ensuring start-of-tick entity position updates do not leave stale references in the spatial index. All movement tests have passed successfully.
