---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
phase: inprogress
date: 2026-10-23
tags: []
---

# TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1

## Title
Remove the free meal for every kind (decision 73) as its own measured step against v1, before milestone 1

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner ruling 2026-10-23 (#715 6356123802): decision 73's free-meal removal is a separate step BEFORE milestone 1, measured against v1 (341f700d0) as the milestone 0 gate's own step (roadmap §12.3, the free-meal off arm). If it moves the world, its record is the milestone 1 base (v1.1). It retires the V1 known entry (TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL, expires 2026-12-31).

## Scope
1. Remove the free meal for every kind at once (decision 44/73): no hunger drop without an accepted transfer (the inn charge accepted at 0 gold and clamped, building_services.py:71-74 / conservation.py:256 / inventory.py:156, per the V1 entry's note).
2. Measure it as its own paired step against 341f700d0 (3 worlds x seeds 42-46 x 5000t, full decision-76 stop rules), plus the §12.3 gate H1-H7 and R1-R5 on the off arm.
3. If the world moves, record v1.1 (gate rebaseline plus disclosure delta); retire the V1 known entry.

## Out of Scope
Milestone 1 items. Births (decision 67).

## Acceptance Criteria
- V1 = 0 violations on all 15 gate runs; the V1 known entry removed.
- The paired step passes the stop line, or the owner rules.
- The gate H1-H7 hold on the off arm; R1-R5 reported.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0).

## Related Docs
docs/plans/systemic_world/roadmap.md §12.3, §12.5; docs/plans/systemic_world/v1_disclosure.md; owner_decision_memo.md.

## Related Stored Artifacts
agent-working/staging_artifacts/TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1/ (investigation, plan, test_plan; plan only, 2026-10-28)
agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/ (probes, earlier evidence)

## Related Code Areas
src/systems (building_services, conservation, inventory); src/ai need_pull

## Assumptions / Open Questions
Owner rulings already made: memo row 73 (paid meal gives 60, price 5 gold, rest keeps its effects at 10 gold, payment atomic, no clamp), row 89 (order and v1.1), row 92 (v3 base). Open points for rpg-planner are listed in plan.md section 'Questions'.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
