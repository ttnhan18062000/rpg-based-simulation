# TCK-20260425-PH7-M3-RECOVERY

## Title

Implementation of Inn, Home, and Class Hall Services

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement town recovery services (Inn/Home) and progression hubs (Class Hall). Ensure biological debt can be managed and strategic blockers can be resolved through town actions.

## Scope

- Implement \`InnAction.rest\` for biological recovery.
- Implement \`HomeAction.rest\` and \`HomeAction.upgrade\`.
- Implement \`ClassHallAction.train\` for skill acquisition.
- Resolve \`maintenance\` and \`capability\` blockers via services.
- Add contract tests for all services.

## Out of Scope

- Visuals for buildings.
- Complex skill trees (deferred).

## Acceptance Criteria

- [x] Inn rest resets \`sleep_debt\` and consumes gold.
- [x] Class Hall training adds \`known_recipes\` and resolves matching \`capability\` blockers.
- [x] Home upgrade resolves \`maintenance\` blockers.
- [x] All tests in \`tests/town/test_recovery_class_hall.py\` pass.

## Related Tickets

- TCK-20260425-PH7-M2-GUILD (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/town/inn.py [NEW]
- src/town/home.py [NEW]
- src/town/class_hall.py [NEW]
- src/engine/apply.py (Updated for BiologicalUpdate set fields)

## Implementation Notes

- Updated \`BiologicalUpdate\` in \`updates.py\` to support \`set\` fields for debt resetting.
- \`ApplyPath\` now handles explicit biological value setting.
- Service actions perform atomic state updates (inventory + strategic + biological).

## Test Summary

- \`tests/town/test_recovery_class_hall.py\`:
  - \`test_inn_rest_recovery\`: PASS (Accounts for passive decay)
  - \`test_home_upgrade_blocker\`: PASS
  - \`test_class_hall_training\`: PASS

## Files Changed

- src/town/inn.py [NEW]
- src/town/home.py [NEW]
- src/town/class_hall.py [NEW]
- src/core/updates.py
- src/engine/apply.py

## Completion Summary

Phase 7 Milestone 3 is complete. The town now provides essential recovery and progression services that directly impact the entity's strategic and biological status.
