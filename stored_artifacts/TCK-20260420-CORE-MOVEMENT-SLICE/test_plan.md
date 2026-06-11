---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260420-CORE-MOVEMENT-SLICE
artifact_type: test_plan
tags: [core, movement, slice]
---


# Test Plan - TCK-20260420-CORE-MOVEMENT-SLICE

## Verification Strategy
- **Differential Parity Test**: Capture movement validation results from the original `src` engine and verify that the `src` engine produces bit-identical outputs for the same scenarios.

## Test Harness
- Oracle: `tests/parity/movement_oracle/results.json` (Captured via `capture_src_movement_oracle.py`)
- Verifier: `tests/parity/movement_oracle/verify_v2_movement.py`

## Scenarios
1. **success_move**: Valid cardinal step.
2. **blocked_terrain**: Target is in static blocked tiles.
3. **occupied_tile**: Target is occupied by another entity.
4. **actor_dead**: Actor is not active (No-Op).
5. **double_claim**: Target is claimed by another agent in the same tick (Transient Claim).

## Result
- All 5 scenarios PASSED.
