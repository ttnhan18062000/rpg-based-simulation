# TCK-20260504-V2-ENGINE-REGRESSION-FIX

## Title
Fix 39 engine test regressions by completing V2EntityBuilder migration

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The simulation engine has 39 failing tests in the `tests/engine/` directory. These failures are primarily due to legacy code (specifically `EntityGenerator` and various test files) attempting to instantiate `EntityState` directly, which violates the V2 engine's frozen dataclass and updated component contract.

## Scope
- Refactor `src/systems/generator.py` to use `V2EntityBuilder`.
- Audit and refactor all remaining failed tests in `tests/engine/` to use `V2EntityBuilder`.
- Update `V2EntityBuilder` to include missing fluent methods for navigation (`home_position`, `leash_radius`).
- Ensure all entities are initialized with 100.0 readiness where interactive behavior is expected.

## Out of Scope
- Implementing new engine features.
- Refactoring tests outside of `tests/engine/` unless strictly necessary.

## Acceptance Criteria
- All 39 previously failing tests in `tests/engine/` pass.
- `EntityGenerator` no longer instantiates `EntityState` directly.
- All refactored tests adhere to the `AuthoritativeApplyPipeline` truth.

## Related Tickets
- TCK-20260504-V2-TEST-HARDENING (Closed)

## Related Docs
- logic_checklist_exhaustive.md

## Related Stored Artifacts
- None

## Related Code Areas
- `src/systems/generator.py`
- `src/core/builder.py`
- `tests/engine/`

## Assumptions / Open Questions
- None at this time.

## Implementation Notes
- Use `V2EntityBuilder.at()` for position.
- Use `V2EntityBuilder.with_base_stats()` for combat stats.
- Remember to call `.build()` at the end of the chain.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
