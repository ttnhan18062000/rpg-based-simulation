---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260506-STRATEGY-TEST-STABILIZATION
phase: done
date: 2026-05-06
tags: [strategy, test, stabilization]
---

# TCK-20260506-STRATEGY-TEST-STABILIZATION

## Title

Migrate strategy test suites to V2EntityBuilder

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Resolve test suite failures in `tests/strategy/` by refactoring legacy `EntityState` instantiations to the `V2EntityBuilder` fluent API.

## Scope

- Identify legacy `EntityState` instantiations in `tests/strategy/` [x]
- Migrate `test_cognition_capacity.py` to `V2EntityBuilder` [x]
- Migrate `test_leads.py` to `V2EntityBuilder` [x]
- Migrate `test_project_continuity.py` to `V2EntityBuilder` [x]
- Migrate `test_strategic_memory_v2.py` to `V2EntityBuilder` (resolving 'active' keyword error) [x]
- Migrate `test_strategic_reprioritization.py` to `V2EntityBuilder` [x]
- Final verification of all tests in `tests/strategy/` [x]

## Out of Scope

- Changes to strategic intelligence systems unless necessary for parity.

## Acceptance Criteria

- All tests in `tests/strategy/` pass. [x]
- No direct `EntityState` instantiations in the affected test files. [x]

## Related Tickets

- TCK-20260504-CORE-TEST-STABILIZATION
- TCK-20260506-INVENTORY-TEST-STABILIZATION

## Related Docs

- logic_checklist_exhaustive.md

## Related Stored Artifacts

- None

## Related Code Areas

- tests/strategy/

## Assumptions / Open Questions

- None

## Implementation Notes

- Use `V2EntityBuilder` for all entity creation in tests.
- Resolved the `active` keyword issue in `test_strategic_memory_v2.py` by using `.active(True)`.
- Enhanced `V2EntityBuilder` with `with_strategic_profile()` and `with_personality()` to support strategy-specific testing.
- Used `force=True` in `evaluate_strategic_intent` to bypass frequency-based skips during tests.

## Test Summary

- Final run: 15 passed.

## Files Changed

- src/core/builder.py
- tests/strategy/test_cognition_capacity.py
- tests/strategy/test_leads.py
- tests/strategy/test_project_continuity.py
- tests/strategy/test_strategic_memory_v2.py
- tests/strategy/test_strategic_reprioritization.py

## Completion Summary

Successfully migrated all strategy tests to the V2 architecture. 15/15 tests passing.
