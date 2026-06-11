---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260506-STRATEGIC-HARDENING-TEST-STABILIZATION
phase: done
date: 2026-05-06
tags: [strategic, hardening, test, stabilization]
---

# TCK-20260506-STRATEGIC-HARDENING-TEST-STABILIZATION

## Title

Migrate strategic hardening test suites to V2EntityBuilder

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Resolve 37 test suite failures in `tests/strategic/` by refactoring legacy `EntityState` instantiations to the `V2EntityBuilder` fluent API.

## Scope

- Identify legacy `EntityState` instantiations in `tests/strategic/` [x]
- Migrate `test_biological_needs.py` to `V2EntityBuilder` [x]
- Migrate `test_detour_suggestion.py` to `V2EntityBuilder` [x]
- Migrate `test_event_interpretation.py` to `V2EntityBuilder` [x]
- Migrate `test_interruption_resistance.py` to `V2EntityBuilder` [x]
- Migrate `test_role_biasing.py` to `V2EntityBuilder` [x]
- Final verification of all tests in `tests/strategic/` [x]

## Out of Scope

- Changes to strategic intelligence systems logic.

## Acceptance Criteria

- All tests in `tests/strategic/` pass. [x]
- No direct `EntityState` instantiations in the affected test files. [x]

## Related Tickets

- TCK-20260506-STRATEGY-TEST-STABILIZATION

## Related Docs

- logic_checklist_exhaustive.md

## Related Stored Artifacts

- None

## Related Code Areas

- tests/strategic/

## Assumptions / Open Questions

- None

## Implementation Notes

- Use `V2EntityBuilder` for all entity creation in tests.
- Extended `V2EntityBuilder` to support `concerns` and fixed `with_strategic_profile` keyword arguments (`breadth` and `depth`).
- Fixed `test_pipeline_integrates_biological_concerns` by setting `tick=99` to pass the frequency guard.

## Test Summary

- Final run: 37 passed.

## Files Changed

- src/core/builder.py
- tests/strategic/test_biological_needs.py
- tests/strategic/test_detour_suggestion.py
- tests/strategic/test_event_interpretation.py
- tests/strategic/test_interruption_resistance.py
- tests/strategic/test_role_biasing.py

## Completion Summary

Successfully migrated all 37 strategic hardening tests to the V2 architecture.
