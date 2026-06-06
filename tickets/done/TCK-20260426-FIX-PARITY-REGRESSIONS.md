# TCK-20260426-FIX-PARITY-REGRESSIONS

## Title
Fix RPG Progression and Action Readiness Regressions

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Fix regressions in RPG progression (XP rewards during evolution) and action readiness (double-subtraction bug) to restore 100% parity with src engine and pass all pytest tests.

## Scope
- `src/engine/evolution.py`: Include `RewardUpdate` XP gain in evolution evaluation.
- `src/engine/pipeline.py`: Correct readiness subtraction logic to avoid double-dipping.
- `tests/parity/test_parity_rpg_recovery.py`: Align XP assertions with V2 evolution precedence.

## Out of Scope
- New feature implementation.
- Refactoring the entire pipeline.

## Acceptance Criteria
- 100% pass rate in `pytest tests/`.
- `test_rpg_progression_recovery` passes with level-up to 2 and 10 XP remaining.
- `test_rpg_combat_recovery_loop` and `test_rpg_pursuit_recovery` pass.

## Related Tickets
- None

## Related Docs
- `docs/engine/authoritative_refinement_contract.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/evolution.py`
- `src/engine/pipeline.py`
- `src/engine/apply.py`

## Assumptions / Open Questions
- Evolution consumes 1000 XP and sets level to 2, which is expected to "starve" the standard leveling loop in the same tick.

## Implementation Notes
- Modified `EvolutionSystem.evaluate` to import and check `RewardUpdate`.
- Modified `Pipeline._refine_step` to use `min(existing_delta, update_delta)` for readiness to avoid double-subtraction between Brain and Physical updates.

## Test Summary
- `pytest tests/`: 600 passed, 2 skipped (async).

## Files Changed
- `src/engine/evolution.py`
- `src/engine/pipeline.py`
- `tests/parity/test_parity_rpg_recovery.py`

## Completion Summary
- Pending final move to done.
