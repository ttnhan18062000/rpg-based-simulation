---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260417-ARENA-PERF-HARDENING
artifact_type: plan
tags: [arena, perf, hardening]
---

# Arena Performance Hardening Plan

## Goal
Resolve resource exhaustion and stability issues in the arena regression harness (`tests/arena/test_arena_harness_contract.py`).

## Proposed Changes

### 1. Model & Data Hardening
- **[MODIFY] Snapshot ([snapshot.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/snapshot.py))**:
    - Align `_SPATIAL_CELL` with `SimulationConfig.spatial_cell_size`.
    - Enable direct spatial dictionary sharing in shallow mode.

### 2. Infrastructure Hardening
- **[MODIFY] WorldLoop ([world_loop.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/world_loop.py))**:
    - Add explicit cleanup for `_phases`, `_tick_events`, and `_last_applied` in `shutdown()`.
- **[MODIFY] PersistencePhase ([persistence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/phases/persistence.py))**:
    - Early return in `execute()` if Redis and Kafka are disabled.

### 3. Monitoring & Regression
- **[MODIFY] ArenaRunner ([runner.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/arena/runner.py))**:
    - Implement per-iteration RSS delta monitoring.
    - Explicit `gc.collect()` and shutdown in `finally` block.
- **[MODIFY] Test Config ([conftest.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/conftest.py))**:
    - Update tripwire thresholds based on optimized baseline.

## Acceptance Criteria
- `tests/arena/test_arena_harness_contract.py` passes 100%.
- Process RSS remains stable across multiple arena iterations.
- No "System Crash" (Resource Exhaustion) triggers during standard regression runs.
