# TCK-20260504-V2-TEST-HARDENING

## Title
Hardening Legacy Test Suites via V2EntityBuilder

## Status
INPROGRESS

## Request Summary
Complete the AOA (Atomic Object Access) migration for the V2 RPG Engine by refactoring legacy test suites to strictly utilize the `V2EntityBuilder`. This ensures that all entity state constructions are consistent with the V2 architecture and that no legacy `EntityState` instantiations bypass the builder's validation and component population logic.

## Scope
- Refactor all `EntityState(...)` instantiations in `tests/engine/` to use `V2EntityBuilder`.
- Ensure all refactored tests pass with the new AOA patterns.
- Resolve any regressions caused by inconsistent state initialization (e.g., readiness, factions, components).

## Out of Scope
- Modifying core engine logic unless necessary to support test patterns.
- Refactoring non-engine tests (unless they also use legacy patterns).

## Acceptance Criteria
- No direct `EntityState` constructor calls remain in `tests/engine/`.
- `pytest tests/engine/` passes 100% (or at least the refactored ones).
- All tests comply with the "Atomic Conservation Law" and "Runtime Truth" principles.

## Related Tickets
- None

## Related Docs
- `architecture.md`
- `RULE[architecture.md]`

## Related Stored Artifacts
- None

## Related Code Areas
- `tests/engine/`
- `src/core/builder.py`

## Assumptions / Open Questions
- `V2EntityBuilder` is feature-complete enough to replace all legacy instantiations.
- Legacy tests that rely on direct state mutation might need deeper refactoring to use `replace()` or `EntityUpdate`.

## Implementation Notes
- Use `V2EntityBuilder(id).kind(k).at(pos).build()` as the base pattern.
- For nested components (inventory, combat), use builder methods like `with_inventory()`, `with_base_stats()`.
- Ensure `readiness` is set correctly for tests that execute actions.

## Test Summary
- `tests/engine/test_resource_v2_boundary.py`: PASSED
- `tests/engine/test_combat_matrix.py`: PASSED

## Files Changed
- `tests/engine/test_resource_v2_boundary.py`

## Completion Summary
- In Progress.
