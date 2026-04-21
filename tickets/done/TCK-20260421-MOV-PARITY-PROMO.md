# TCK-20260421-MOV-PARITY-PROMO

## Title
Promote Movement Parity Verification to Standard Test Path

## Status
DONE

## Request Summary
Take the existing movement parity work (currently in script-oriented support) and turn it into an ordinary validation requirement in `tests_v2/parity/test_movement_parity.py` that runs under `pytest`.

## Scope
- [x] Create `tests_v2/parity/test_movement_parity.py`.
- [x] Refactor logic from `tests_v2/parity/movement_oracle/verify_v2_movement.py` into `pytest` class/methods.
- [x] Integrate with existing `results.json` oracle data.
- [x] Ensure parity verification is part of the standard `tests_v2` gate.
- [x] Update documentation to reference the new official proof path.

## Out of Scope
- Implementing new movement features.
- Changing `src` (original) movement logic.
- Performance benchmarking (separate task).

## Acceptance Criteria
- [x] `pytest tests_v2/parity/test_movement_parity.py` passes.
- [x] Failures are clearly reported using standard `pytest` assertions.
- [x] Supported movement scope (grid, blocked, occupancy, dead-actor) is explicitly tested.
- [x] `results.json` is used as the source of truth for original behavior.

## Related Tickets
- None

## Related Docs
- [resource_phase5_implementation_milestone_1.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase5_implementation_milestone_1.md)
- [src_v2_principle.md](file:///home/vboxuser/Work/rpg-based-simulation/src_v2_principle.md)
- [attach_gate1_movement_scope.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/attach_gate1_movement_scope.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `tests_v2/parity/movement_oracle/`
- `src_v2/engine/movement.py`

## Assumptions / Open Questions
- **Assumption**: `tests_v2/parity/movement_oracle/results.json` is already up-to-date and represents the intended behavior.
- **Question**: Should we also include the `capture_src_movement_oracle.py` logic in the test suite to allow re-capturing if needed (e.g. as a separate flag)?

## Implementation Notes
- Use `pytest.mark.parametrize` to run all scenarios from `results.json`.
- Match the failure reason codes exactly where parity is intended.

## Test Summary
- All 5 scenarios (`success_move`, `blocked_terrain`, `occupied_tile`, `actor_dead`, `double_claim`) passing under pytest.

## Files Changed
- `tests_v2/parity/test_movement_parity.py`
- `docs/engine/attach_gate1_movement_scope.md`

## Completion Summary
- Movement parity is now a first-class citizen of the `tests_v2` suite.
- Parity is verified against original `src` behavior using the captured oracle data.
- Documentation updated to reflect the new official proof path.
