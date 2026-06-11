---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-FIX-TEST-REGRESSIONS
artifact_type: investigation
tags: [fix, test, regressions]
---

# Investigation: Test Regressions

## Failure 1: TacticalDecisionSystem AttributeError
- Test: `test_target_selection_parity` and `test_retreat_threshold_divergence`.
- Error: `AttributeError: type object 'TacticalDecisionSystem' has no attribute 'evaluate'`.
- Cause: Renaming or refactoring of the system in Phase 8/9.

## Failure 2: OA on disengagement
- Test: `test_oa_triggered_on_disengagement_hardened`.
- Symptom: Likely no OA being triggered or wrong damage.

## Failure 3: Movement Parity [blocked_terrain]
- Test: `test_movement_parity_with_oracle[blocked_terrain]`.
- Symptom: V2 might be allowing movement where V1 blocked it, or vice versa.
