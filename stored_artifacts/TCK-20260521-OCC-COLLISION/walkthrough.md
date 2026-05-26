# Walkthrough: Metropolis Occupancy Collision Resolution

We have successfully resolved the deterministic `LAW-OCCUPANCY-COLLISION` crash occurring at tick 2503 in the Metropolis simulation.

## Changes Made

### 1. Unique Coordinate Spawning for Raiders
We modified `src/world/raid.py` to scatter raider spawn positions using a small grid offset (`i % 3 - 1`, `i // 3 - 1`) instead of deterministic overlapping coordinate assignments. This prevents multiple entities from spawning on the identical tile at birth.

### 2. Cache Invalidation in Hard Law Monitor
We modified `src/observability/hard_law_monitor.py` to explicitly clear the cached `world_indexes` from the state before running `check_occupancy`. This guarantees the monitor verifies final resolved positions at the end of the tick rather than relying on stale start-of-tick cached index mappings.

### 3. Config Reversion
Reverted `max_tick_budget_ms` in `src/config/loader.py` to its production-standard value of `50.0` ms.

## Verification Results

1. **Reproduction Test**:
   The `check_events.py` reproduction script executed deterministically and passed the previous tick 2503 crash point, successfully running past tick 4000 with zero `LAW-OCCUPANCY-COLLISION` violations!
   
2. **Occupancy Unit Tests**:
   All 39 occupancy and movement unit tests (`pytest tests/unit/movement/`) pass perfectly with no regressions.
