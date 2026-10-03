---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-METROPOLIS-COLLISION
artifact_type: investigation
tags: [metropolis, collision]
---

# Investigation Notes - Metropolis Collision Debugging

## Problem Description
A `LAW-OCCUPANCY-COLLISION` crash occurred at tick 4210 during a Metropolis simulation run.
The error log:
`LAW-OCCUPANCY-COLLISION on entity 760: Occupancy collision on tile (-21, 12): entity 760 and entity 755 both occupy this space.`

## Root Cause Analysis
1. **Ghost Occupancy in `live_occ_map`**:
   During the candidate evaluation loop in `MovementPhase.route_movement_intent`, multiple entities can move or yield multiple times in a single tick due to prioritized resolution.
   If an entity `B` is forced to yield to `yield_tile_1`, `live_occ_map[yield_tile_1] = B` is registered.
   If `B` is subsequently forced to yield to `yield_tile_2`, `refined_entity_updates[B]` gets its `new_position` overwritten with `yield_tile_2`.
   However, `yield_tile_1` is NEVER removed from `live_occ_map`!
   As a result, `yield_tile_1` is left as a "ghost occupancy" mapped to `B` in the transient cache.
   Any subsequent queries (like `get_occupant`) see `B` occupying `yield_tile_1`, which triggers false blocked legality checks or illegal moves, leading to eventual occupancy collision when another entity is allowed to move there under a different assumption or when spatial indexes desynchronize.

2. **Pass 0 Stale Initialization**:
   In `route_movement_intent`, `live_occ_map` is initialized with the start-of-tick map.
   If an entity has an update with a `new_position` set prior to the loop (e.g. from combat or Pass 0 position swaps), that `new_position` is added to `live_claims` and `live_occ_map`.
   However, the entity's start-of-tick `old_position` is never deleted!
   This means the entity is registered as occupying BOTH the old and new positions.

3. **Floating-point coordinates in Yield Target Calculations**:
   In `MovementSystem.resolve_move` (line 124):
   `yield_tile = (occupant.navigation.position[0] + dx_y, occupant.navigation.position[1] + dy_y)`
   Using floats can lead to coordinate precision discrepancies (e.g., `-21.0` vs `-21`). It must be cast to integer coordinates `(int(...), int(...))` to maintain strict grid parity.
