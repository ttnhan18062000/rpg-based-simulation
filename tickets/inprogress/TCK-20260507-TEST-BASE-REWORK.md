# TCK-20260507-TEST-BASE-REWORK

## Title

Rework test base to remove legacy V2EntityBuilder API calls

## Status

INPROGRESS

## Request Summary

Migrate all test files and production code from legacy V2EntityBuilder methods to current V2 API, following test_base_rework_plan.md strictly. Fix all 320 failures + 49 errors caused by removed builder methods.

## Scope

- Fix `src/systems/generator.py` legacy builder calls (production code)
- Fix `src/certification/scenarios.py` legacy builder calls
- Migrate all test-local `make_entity` helpers in every failing test domain
- Work domain by domain in dependency order
- Remove all legacy compatibility shims

## Out of Scope

- Restructuring test directory layout (plan items §1, §4-§12 deferred)
- Consolidating local helpers into shared `tests/helpers/` (follow-up)
- Adding new test coverage
- Changing test logic or RPG rules

## Acceptance Criteria

- All 537 currently-passing tests continue to pass
- All 320 failures + 49 errors are resolved
- Zero uses of legacy builder methods remain
- No legacy compatibility shims in builder

## Related Tickets

- Previous: engine V2 migration conversations

## Related Docs

- `test_base_rework_plan.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/builder.py`
- `src/systems/generator.py`
- `src/certification/scenarios.py`
- `tests/rpg/`
- `tests/engine/`
- `tests/combat/`
- `tests/social/`
- `tests/strategic/`
- `tests/strategy/`
- `tests/systems/`
- `tests/town/`
- `tests/world/`
- `tests/unit/`
- `tests/tactical/`
- `tests/contract/`
- `tests/verify/`

## Assumptions / Open Questions

- Production code fixes in generator.py are in scope
- Test logic is NOT changed, only builder API calls updated

## Implementation Notes

(updated during work)

## Test Summary

(updated after work)

## Files Changed

(updated after work)

## Completion Summary

(pending)
