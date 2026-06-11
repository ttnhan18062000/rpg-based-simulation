---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260510-REFACTOR-SUBSYSTEM-TEST-MIGRATION
phase: done
date: 2026-05-10
tags: [refactor, subsystem, test, migration]
---

# TCK-20260510-REFACTOR-SUBSYSTEM-TEST-MIGRATION

## Title
Migrate Subsystem Unit Tests and World Long-Run Tests

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Move long-run world simulation tests and direct system tests to their respective `unit/` and `integration/world/` folders as per Milestone 1 (Tasks 1.3 & 1.4).

## Scope
- Move `tests/rpg/test_living_world_ph9.py` to `tests/integration/world/`.
- Add `@pytest.mark.slow` and `@pytest.mark.world_long_run` markers to PH9 world test.
- Classify and move direct system tests (Combat, Legality, Resource, Quest, Social, Strategic, World) to `tests/unit/`.

## Out of Scope
- Reorganizing `tests/engine/` beyond direct system tests.
- Kernel integration tests (part of Task 1.2/1.4 depending on interpretation, but I'll focus on the listed systems).

## Acceptance Criteria
- [x] `test_living_world_ph9.py` moved and marked correctly.
- [x] Direct system tests (Combat, Resource, etc.) moved to their new `unit/` subfolders.
- [x] No assertion changes.
- [x] All moved tests pass.

## Related Tickets
- [TCK-20260510-REFACTOR-TEST-STRUCTURE-INIT](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260510-REFACTOR-TEST-STRUCTURE-INIT.md)

## Related Docs
- [refactor_implementation_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/refactor_implementation_plan.md)

## Related Code Areas
- `tests/`

## Implementation Notes
- Use `git mv`.
- Classification rules from Milestone 1 will be followed strictly.

## Test Summary
- `pytest tests/unit -q`
- `pytest tests/integration/world -q -m "not slow"`

## Files Changed
- TBD

## Completion Summary
- TBD
