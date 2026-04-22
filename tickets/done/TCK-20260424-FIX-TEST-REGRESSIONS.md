# TCK-20260424-FIX-TEST-REGRESSIONS

## Title
Fix Test Regressions in tests_v2/

## Status
DONE

## Request Summary
Fix 4 failed test cases in `tests_v2/` identified after Phase 9 closure.

## Scope
- Fix `TacticalDecisionSystem.evaluate` AttributeError in `test_tactical_parity.py`.
- Fix OA triggered on disengagement in `test_oa_parity.py`.
- Fix movement parity with oracle in `test_movement_parity.py`.

## Out of Scope
- Major architectural changes unless required by the fix.

## Acceptance Criteria
- [x] `pytest tests_v2/` passes 100%.

## Related Tickets
- None

## Related Docs
- None

## Related Stored Artifacts
- None

## Related Code Areas
- `src_v2/systems/tactical.py`
- `tests_v2/parity/test_tactical_parity.py`
- `tests_v2/parity/test_oa_parity.py`
- `tests_v2/parity/test_movement_parity.py`

## Assumptions / Open Questions
- The `TacticalDecisionSystem` API changed during Phase 8/9 development and tests weren't updated.

## Implementation Notes
- Aligned `TacticalDecisionSystem` API in tests (renamed `evaluate` to `evaluate_entity_intent`).
- Fixed `ImportError` in `MovementSystem` (renamed `CombatReactionSystem` to `CombatResolutionSystem`).
- Fixed `blocked_terrain` parity mismatch in `LegalityServiceV2` by adding `blocked_tiles` check.
- Fixed double-damage bug in `ApplyPath` where both `hp_delta` and `damage_taken` were being subtracted.

## Test Summary
- `pytest tests_v2/` passed 100% (375 tests).
- Verified OA parity damage (12 points).
- Verified tactical selection and retreat thresholds.
- Verified blocked terrain enforcement.

## Files Changed
- `src_v2/engine/legality.py`
- `src_v2/engine/movement.py`
- `src_v2/engine/apply.py`
- `tests_v2/parity/test_tactical_parity.py`
