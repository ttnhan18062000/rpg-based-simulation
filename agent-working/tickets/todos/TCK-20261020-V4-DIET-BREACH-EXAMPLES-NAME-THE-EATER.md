---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-V4-DIET-BREACH-EXAMPLES-NAME-THE-EATER
phase: open
date: 2026-10-20
tags: [observability]
---

# TCK-20261020-V4-DIET-BREACH-EXAMPLES-NAME-THE-EATER

## Title
V4's diet-breach examples name each eater and its tick, the way V5's and V8's examples already do

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
V4 (`rpg_gate_metrics._check_diet_gates`) emits only aggregate examples: `{"consumption": "group|source|item", "count", ...}`. A red V4 can't be traced to a body. V5 (`out_of_world_examples`) and V8 (`unsourced_examples`) already keep a bounded list of `{entity_id, tick, ...}`. Testing-planner raised this on 2026-10-20 while mapping the kernel positive for each V-id. Do it after v1; it is not part of the pre-v1 PR.

## Scope
- In `src/observability/run_ledger.py`, add `_diet_breach_examples` (reset with the other example lists). Where a diet breach is counted, append `{entity_id, tick, kind_group, source, item}` while the list is below `MAX_EXAMPLES`. Emit `diet_breach_examples` in the summary.
- In `rpg_gate_metrics._check_diet_gates`, return those examples for the consumption part. The count stays the sum of breaches.
- In the V4 real-kernel test, assert that the example names the forced meat-only body and its tick.
- Update the format doc's V4 row if the example shape is written there (testing-planner's file, so ask it).

## Out of Scope
- Any change to what counts as a breach, or to V4's pass or fail.

## Acceptance Criteria
- A forced breach makes V4 emit an example that carries the eater's entity_id and tick.
- Examples are capped at MAX_EXAMPLES.
- V4 counts and verdicts are identical before and after on the 3 gate worlds at seed 42.
- The final hash is identical, because the ledger is an observer.

## Related Tickets
- TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION
- TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY (same pattern)
- TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE (testing)

## Related Docs
- the rpg gate format doc (V4 row)

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/run_ledger.py (diet breach counting)
- src/observability/rpg_gate_metrics.py (`_check_diet_gates`)
- tests/integration/observability/test_v4_counts_a_forbidden_meal_through_the_real_kernel.py

## Assumptions / Open Questions
- The harness hash may move because of the new field. Tell testing-planner before it lands.

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary
