---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-METROPOLIS-COLLISION
artifact_type: test_plan
tags: [metropolis, collision]
---

# Test Plan - Metropolis Collision Resolution

## Automated Tests
We will add a new test file: `tests/unit/movement/test_movement_collision_resolution.py`.

### Test Cases:
1. **test_intermediate_yield_ghost_removal**:
   - Create two entities.
   - Set up refined entity updates with a pre-existing `new_position` update for Entity A.
   - Generate a subsequent movement update for Entity A with a different `new_position`.
   - Call the candidate resolution update logic (or mock the phase execution).
   - Assert that the intermediate position is removed from the `live_occ_map` and `live_claims` and only the final `new_position` remains.

2. **test_prior_update_old_position_removal**:
   - Set up an entity with a pre-existing `new_position` (e.g. from combat).
   - Initialize the `live_occ_map` and `live_claims` in `route_movement_intent`.
   - Assert that the entity's start-of-tick position has been deleted from `live_occ_map` and only the `new_position` is recorded.

3. **test_yield_tile_integer_casting**:
   - Set up an occupant entity at a floating point position (e.g. `(1.5, 2.7)`).
   - Resolve a prioritized movement that triggers yielding.
   - Assert that the yielded target position has integer grid coordinates.

## Verification Commands
- `pytest tests/unit/movement/test_movement_collision_resolution.py`
- `pytest tests/unit/movement/`
