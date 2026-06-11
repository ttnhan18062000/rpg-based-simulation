---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-OCCUPANCY-SNAPSHOT
artifact_type: test_plan
tags: [occupancy, snapshot]
---

# Test Plan: OccupancySnapshot

## Objectives

Verify `OccupancySnapshot` correctly extracts active/alive entity tile occupancy and tie-breaking priority, remains immutable for a tick, rebuilds when state advances, and matches existing `LegalityServiceV2` occupancy checks.

## Test Cases (`tests/unit/optimization/test_occupancy_snapshot.py`)

1. `test_occupancy_snapshot_contains_entity_positions`:
   - Builds snapshot from state with multiple active entities and verifies `occupancy_by_tile` contains exactly their `(x, y)` tile positions.
2. `test_occupancy_snapshot_reports_occupied_tile`:
   - Calls `is_occupied(tile)` and `occupant_at(tile)` for occupied tiles and verifies correct return values.
3. `test_occupancy_snapshot_reports_empty_tile`:
   - Calls `is_occupied(tile)` and `occupant_at(tile)` for empty tiles and verifies False / None.
4. `test_occupancy_snapshot_is_stable_for_tick`:
   - Modifies an entity's position in `state` after snapshot creation; verifies snapshot remains stable/unchanged.
5. `test_occupancy_snapshot_rebuilt_after_apply_changes_position`:
   - Advances state (e.g., tick increment or new state) and verifies a fresh `OccupancySnapshot.from_state` reflects the new position and new tick.
6. `test_movement_legality_uses_snapshot_result_equivalent_to_current_logic`:
   - Compares `verify_occupancy` or movement legality using the snapshot with the legacy direct state verification and verifies identical results.

## Execution

```bash
pytest tests/unit/optimization/test_occupancy_snapshot.py -v
pytest tests/unit/ -m "not slow"
```
