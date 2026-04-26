# TCK-20260425-PH7-M4-SABOTAGE

## Title

Implementation of Building Damage and Sabotage

## Status

DONE

## Request Summary

Implement authoritative building damage and regional trauma. Ensure building destruction has world-level consequences.

## Scope

- Implement \`SabotageAction.apply\` for building damage.
- Detect building destruction in \`ApplyPath.apply_generation\`.
- Propagate \`trauma_score\` to regions upon building death.
- Add contract tests for sabotage and trauma.

## Out of Scope

- Repair actions (deferred).
- Detailed building collapse animations/events.

## Acceptance Criteria

- [x] Sabotage reduces building HP authoritatively.
- [x] Buildings become non-functional at 0 HP.
- [x] Regional trauma increases on building destruction.
- [x] All tests in \`tests/town/test_building_sabotage.py\` pass.

## Related Tickets

- TCK-20260425-PH7-M3-RECOVERY (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/town/sabotage.py [NEW]
- src/engine/apply.py

## Implementation Notes

- Added building death detection in \`ApplyPath\`.
- \`trauma_score\` increment is set to 2.0 per building destroyed.
- Integrates with \`LegalityServiceV2\` for region lookup.

## Test Summary

- \`tests/town/test_building_sabotage.py\`:
  - \`test_building_sabotage_damage\`: PASS
  - \`test_building_destruction_and_trauma\`: PASS
  - \`test_sabotage_proximity_validation\`: PASS

## Files Changed

- src/town/sabotage.py [NEW]
- src/engine/apply.py

## Completion Summary

Phase 7 Milestone 4 is complete. The world now supports authoritative building destruction with regional consequences, finalizing the Town and Building infrastructure phase.
