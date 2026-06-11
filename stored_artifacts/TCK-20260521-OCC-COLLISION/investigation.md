---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-OCC-COLLISION
artifact_type: investigation
tags: [occ, collision]
---

# Investigation: Metropolis Occupancy Collision at Tick 1291 & 2503

## Issue Summary

During the `long_run_complex_sweep_2026` / Metropolis scenarios, the simulation crashes with a `LAW-OCCUPANCY-COLLISION` violation. Initially caught at tick 1291, a deterministic reproduction using the `audit_mode=True` run flags isolated the crash at tick 2503 at coordinate `(-7, -23)` between entity 536 and entity 537.

## Root-Cause Analysis

### 1. Raid Spawning Contention (Primary Trigger)
- At tick 2500, `RaidService.check_for_raid` is triggered (`state.tick % 500 == 0`).
- It calculates a single deterministic `spawn_pos` based on tick angle: `(-7, -23)`.
- It loops `raid_size` (4) times and spawns all raider entities at the **exact same coordinate**!
- As a result, entities 536 and 537 (along with others) are added to the authoritative state sharing the identical coordinate `(-7.0, -23.0)`.
- Since they spawn at the identical position, they begin their simulation lives in an overlapping state.

### 2. Stale Spatial Index in Hard Law Monitor (Monitoring Gap)
- Mutating positions during the tick does not invalidate `state.world_indexes` because the cache is tied to `state.tick`.
- The `HardLawMonitor` checks occupancy at the very end of the tick (Advancement Phase) using `WorldIndexService.get_indexes(state, dirty_set)`.
- Because the cache is never cleared within a tick, the monitor queries the stale start-of-tick index.
- Therefore, when entities first spawn/overlap (tick 2500) or remain stationary (tick 2501, 2502), the monitor does not detect the collision because no movement dirty flag was raised or the index was stale.
- Only when one of the overlapping entities attempts to move (tick 2503), the dirty flag is raised, and the monitor finally detects the concurrent occupancy at `(-7, -23)`.

### 3. Cascading Rejection (Resolution)
- The iterative cascading rejection in `OccupancyPhase.resolve` correctly reverts moving entities when their target is blocked or occupied by a static entity.
- However, if the entities are *already* overlapping from birth and do not move, `OccupancyPhase` receives `None` updates for the non-moving entity and cannot resolve the pre-existing overlap.

## Solution

1. **Scatter Raid Spawns**:
   In `src/world/raid.py`, offset the coordinates for each raider during spawning so they are placed on adjacent free tiles rather than stacked on the identical tile.
   
2. **Refresh Spatial Index for Hard Law Monitor**:
   In `src/observability/hard_law_monitor.py`, explicitly clear the cached `world_indexes` attribute on the state before running `check_occupancy` to guarantee the check is performed against the actual final resolved positions.
