---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-OCC-COLLISION
artifact_type: test_plan
tags: [occ, collision]
---

# Test Plan: Occupancy Collision & Cascading Rejection

## Objective

Verify that the V2 engine correctly handles movements, yielding conflicts, and cascading rejections without violating `LAW-OCCUPANCY-COLLISION` rules.

## Automated Verification

1. **Unit Tests**:
   - Run existing unit tests for movement:
     `pytest tests/unit/movement/`
   - We will check if they pass after the modification.

2. **New Collision/Rejection Cases**:
   - We will write a specific regression test in `tests/unit/movement/test_movement_collision_resolution.py` to construct the cascading rejection scenario:
     - Entity A (210) wants to move to Tile X.
     - Entity B (209) is at Tile X, and yields to Tile Y.
     - Tile Y is blocked by a static entity C (208).
     - Verify that BOTH Entity A and Entity B moves are rejected, reverting A to its old tile and B to Tile X safely.
   - Run the new test specifically.

3. **Staging / Sweep Verification**:
   - Run the simulation scenarios to verify no crashes occur at tick 1291.
