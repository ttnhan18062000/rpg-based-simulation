# TCK-20260504-CORE-TEST-STABILIZATION

## Title

Fix all failed tests by restoring EntityState backward compatibility and updating tests

## Status

INPROGRESS

## Request Summary

Fix all failed tests using pytest. Ensure graphify is updated and used for context. Use logic_checklist_exhaustive.md and follow clean-code principles.

## Scope

- Identify root cause of widespread test failures (done: EntityState __init__ mismatch)
- Restore backward compatibility in EntityState __init__ using InitVars
- Update tests that cannot be fixed via EntityState changes
- Ensure all 433+ failures are resolved
- Update graphify graph

## Out of Scope

- Major architectural changes to the V2 engine (unless necessary for parity)
- Implementing new features not required by existing tests

## Acceptance Criteria

- All tests pass (0 failed, 0 errors)
- EntityState maintains AOA purity while supporting legacy initialization
- Graphify is updated and reflects the changes
- Logic checklist is followed

## Related Tickets

- None

## Related Docs

- logic_checklist_exhaustive.md
- src_v2_principle.md
- src_v2_overview.md

## Related Stored Artifacts

- None

## Related Code Areas

- src/core/state.py
- src/core/builder.py
- tests/

## Assumptions / Open Questions

- Assumption: Restoring keyword parity in EntityState.__init__ will fix the majority of failures.
- Question: Should I also update tests to use V2EntityBuilder where appropriate, or stick to InitVars for now to minimize churn?

## Implementation Notes

- Use InitVars in EntityState to support legacy keywords without conflicting with properties.

## Test Summary

- Initial run: 433 failed, 39 errors.

## Files Changed

- TBD

## Completion Summary

- TBD
