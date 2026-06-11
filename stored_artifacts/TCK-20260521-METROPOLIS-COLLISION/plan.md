---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-METROPOLIS-COLLISION
artifact_type: plan
tags: [metropolis, collision]
---

# Implementation Plan - Metropolis Collision Resolution

## Goal Description
Resolve spatial collision crashes in the V2 RPG Engine by ensuring atomic occupancy mapping during movement resolution, clearing ghost claims, and ensuring coordinate parity.

## User Review Required
No breaking changes or significant user review required. We are correcting internal simulation laws and caching mechanisms without changing public API signatures.

## Proposed Changes

### Movement Pipeline Phase

#### [MODIFY] [movement.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline_phases/movement.py)
- **Stale old position cleanup during initialization**:
  Update `route_movement_intent` initialization loop so that if `ent_upd.new_position` is not None, the entity's start-of-tick position is cleared from `live_occ_map`.
- **Atomic updates during candidate resolution**:
  In the candidate loop, when iterating over `move_updates`:
  If the entity already has an existing update with a `new_position`, and `u_upd` sets a different `new_position`, atomically delete the old `existing.new_position` from `live_occ_map` and `live_claims` before performing `merge`.

### Movement System

#### [MODIFY] [movement.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/movement.py)
- **Integer Coordinate Casting**:
  In `MovementSystem.resolve_move`, cast coordinates to integers when calculating `yield_tile` to guarantee clean grid coordinates.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/movement/` to verify no regressions in spatial occupancy, congestion, or position swaps.
- Create a new unit test `tests/unit/movement/test_movement_collision_resolution.py` to assert that:
  1. Stale intermediate yield positions are cleared when subsequent yields/moves occur.
  2. Start-of-tick old positions are correctly removed when updates are pre-populated.
  3. Yield coordinates are cast to integers.

### Manual Verification
- Run a simulation sweep with metropolis scenario to verify it completes successfully (running past tick 4210 up to 5,000+ ticks).
