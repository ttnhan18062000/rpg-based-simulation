# Plan: Metropolis Occupancy Collision Fix

## Proposed Changes

We will implement two targeted enhancements to resolve the Metropolis occupancy collision:

### 1. Raid Spawning Scatterness
We will modify `src/world/raid.py` to offset the spawn position of each raider to prevent them from spawning on the identical tile.

#### [MODIFY] [raid.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/raid.py)
In the spawning loop:
```python
        for i in range(raid_size):
            # Scatter coordinates in a small circle or grid around the base spawn position
            # using simple, deterministic, state-free offsets to avoid overlapping
            ox = spawn_pos[0] + (i % 3) - 1
            oy = spawn_pos[1] + (i // 3) - 1
            
            mob = generator.spawn_monster(
                state=state,
                kind="goblin_raider",
                pos=(ox, oy),
                difficulty_tier=4
            )
```

### 2. Fresh Spatial Index for Hard Law Monitor
We will modify `src/observability/hard_law_monitor.py` to clear the cached `world_indexes` before checking occupancy.

#### [MODIFY] [hard_law_monitor.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/hard_law_monitor.py)
In `HardLawMonitor.check_occupancy`:
```python
        # Force fresh index rebuild to bypass cached start-of-tick positions
        if hasattr(state, "world_indexes"):
            try:
                delattr(state, "world_indexes")
            except AttributeError:
                pass
```

## Verification Plan

### Automated Tests
1. Run `check_events.py` reproduction script to confirm that the Metropolis simulation executes past tick 2503 without `LAW-OCCUPANCY-COLLISION` crashes.
2. Run occupancy unit tests (`pytest tests/unit/movement/test_occupancy_conflicts.py`) to confirm no regressions are introduced.
