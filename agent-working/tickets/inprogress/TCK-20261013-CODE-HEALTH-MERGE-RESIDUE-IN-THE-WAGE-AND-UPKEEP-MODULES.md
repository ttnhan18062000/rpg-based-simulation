---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261013-CODE-HEALTH-MERGE-RESIDUE-IN-THE-WAGE-AND-UPKEEP-MODULES
phase: implement
date: 2026-10-13
tags: []
---

# TCK-20261013-CODE-HEALTH-MERGE-RESIDUE-IN-THE-WAGE-AND-UPKEEP-MODULES

## Title
Clear the four new code-health violations that the batch-3 merge left on the combined RPG branch.

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`python -m codebase.health check` on rpg-single-pr reported 4 NEW violations: building_services.py:35 PLC0415 (a function-local import of offers_work to break a work_shift <-> building_services cycle), town_resolution.py:2 I001, work_shift.py:12 I001 and work_shift.py:20 F401 (an unused nearest_serving).

## Scope
Fix in code, no suppression, no baseline edit: move maintenance_open and offers_work into building_services (work_shift already imports it, so the cycle and the local import are gone); sort the imports; drop the unused import. Behaviour-free.

## Out of Scope
The WORSE items (reported separately to rpg-planner).

## Acceptance Criteria
codebase.health reports 0 NEW violations; mypy baseline clean; the wage and upkeep tests pass.

## Related Tickets
EXCH-02 batch 3 treasury tickets (closed).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/building_services.py, work_shift.py, town_resolution.py

## Assumptions / Open Questions
None.

## Implementation Notes
offers_work and maintenance_open now live in building_services (the module that already owns SERVICE_KINDS and service_building); work_shift imports them. offers_work returns bool(...) to satisfy mypy.

## Test Summary
tests/unit/world + tests/unit/economy + treasury upkeep scenario: 471 passed.

## Files Changed
src/engine/{building_services,work_shift,town_resolution}.py; tests/unit/world/test_work_shift_pays_a_wage_from_the_inns_purse.py (import path)

## Completion Summary
Pending PR.
