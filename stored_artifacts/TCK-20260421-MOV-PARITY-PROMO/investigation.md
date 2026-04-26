# Investigation: Movement Parity Promotion

## Current State
- Movement parity is currently verified via a standalone script: `tests/parity/movement_oracle/verify_v2_movement.py`.
- It loads expected results from `tests/parity/movement_oracle/results.json`.
- It maps scenarios to V2 initial state and calls `MovementSystem.resolve_move`.
- It performs manual assertion checks and prints results.
- It is not integrated into `pytest` or the main test suite.

## Scenarios in `results.json`
- `success_move`: Simple move to empty tile.
- `blocked_terrain`: Move to tile blocked by grid.
- `occupied_tile`: Move to tile occupied by another entity.
- `actor_dead`: Move attempt by a dead entity.
- `double_claim`: Move to tile that is already claimed this tick (concurrency case).

## V2 Implementation Details
- `MovementSystem.resolve_move` handles the logic.
- It uses `LegalityServiceV2` for occupancy and terrain checks.
- It handles the `double_claim` case via a `transient_claims` context if provided.
- Success returns an `EntityUpdate` with `moved_this_tick=True` and a position update.
- Failure returns an `EntityUpdate` with `failure_reason` and `last_move_failed=True`.

## Required Changes
1.  **New Test File**: `tests/parity/test_movement_parity.py`.
2.  **Pytest Integration**: Use `@pytest.mark.parametrize` to iterate over scenarios in `results.json`.
3.  **State Setup**: Use standard V2 core models (`AuthoritativeState`, `EntityState`) to setup the test context.
4.  **Assertion Logic**: Standardize on `pytest` assertions for `moved_this_tick` and `failure_reason`.
5.  **Documentation**: Update `attach_gate1_movement_scope.md` or similar to point to this new test as the official proof.

## Open Questions
- **Q1**: Should `capture_src_movement_oracle.py` be integrated into the test suite?
  - *Recommendation*: Keep it as a standalone utility for now (Task 1 doesn't ask for full re-capture on every test run, which would require `src` environment).
- **Q2**: Should I create `tests/gameplay` directory as mentioned in the task possible affected files?
  - *Answer*: Yes, if `tests/parity/test_movement_parity.py` is better located there. But Milestone 1, Task 1 says `tests/parity/test_movement_parity.py`. I will follow the explicit path provided.

## Next Steps
- Propose implementation plan.
- Create the test file.
- Verify with `pytest`.
