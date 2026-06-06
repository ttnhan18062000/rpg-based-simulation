# TCK-20260506-TOWN-TEST-STABILIZATION

## Title

Migrate town test suites to V2EntityBuilder

## Status
DONE
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Resolve 21 test suite failures in `tests/town/` by refactoring legacy `EntityState` instantiations to the `V2EntityBuilder` fluent API.

## Scope

- Identify legacy `EntityState` instantiations in `tests/town/`
- Migrate all 9 test files in `tests/town/` to `V2EntityBuilder`
- Final verification of all tests in `tests/town/`

## Out of Scope

- Changes to town resolution logic.

## Acceptance Criteria

- All tests in `tests/town/` pass.
- No direct `EntityState` instantiations in the affected test files.

## Related Tickets

- TCK-20260506-STRATEGIC-HARDENING-TEST-STABILIZATION

## Related Docs

- logic_checklist_exhaustive.md

## Related Stored Artifacts

- None

## Related Code Areas

- tests/town/

## Assumptions / Open Questions

- None

## Implementation Notes

- Use `V2EntityBuilder` for all entity creation in tests.

## Test Summary

- Initial run: 21 failed.

## Files Changed

- TBD

## Completion Summary

- TBD
