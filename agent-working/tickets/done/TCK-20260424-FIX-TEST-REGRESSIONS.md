---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260424-FIX-TEST-REGRESSIONS
phase: done
date: 2026-04-24
tags: [fix, test, regressions]
---

# TCK-20260424-FIX-TEST-REGRESSIONS

## Title
Fix Test Regressions in tests/

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Fix 4 failed test cases in `tests/` identified after Phase 9 closure.

## Scope
- Fix `TacticalDecisionSystem.evaluate` AttributeError in `test_tactical_parity.py`.
- Fix OA triggered on disengagement in `test_oa_parity.py`.
- Fix movement parity with oracle in `test_movement_parity.py`.

## Out of Scope
- Major architectural changes unless required by the fix.

## Acceptance Criteria
- [x] `pytest tests/` passes 100%.

## Related Tickets
- None

## Related Docs
- None

## Related Stored Artifacts
- None

## Related Code Areas
- `src/systems/tactical.py`
- `tests/parity/test_tactical_parity.py`
- `tests/parity/test_oa_parity.py`
- `tests/parity/test_movement_parity.py`

## Assumptions / Open Questions
- The `TacticalDecisionSystem` API changed during Phase 8/9 development and tests weren't updated.

## Implementation Notes
- Aligned `TacticalDecisionSystem` API in tests (renamed `evaluate` to `evaluate_entity_intent`).
- Fixed `ImportError` in `MovementSystem` (renamed `CombatReactionSystem` to `CombatResolutionSystem`).
- Fixed `blocked_terrain` parity mismatch in `LegalityServiceV2` by adding `blocked_tiles` check.
- Fixed double-damage bug in `ApplyPath` where both `hp_delta` and `damage_taken` were being subtracted.

## Test Summary
- `pytest tests/` passed 100% (375 tests).
- Verified OA parity damage (12 points).
- Verified tactical selection and retreat thresholds.
- Verified blocked terrain enforcement.

## Files Changed
- `src/engine/legality.py`
- `src/engine/movement.py`
- `src/engine/apply.py`
- `tests/parity/test_tactical_parity.py`
