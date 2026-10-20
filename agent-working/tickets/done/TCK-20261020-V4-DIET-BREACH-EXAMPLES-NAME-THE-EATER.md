---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-V4-DIET-BREACH-EXAMPLES-NAME-THE-EATER
phase: done
date: 2026-10-20
tags: [observability]
---

# TCK-20261020-V4-DIET-BREACH-EXAMPLES-NAME-THE-EATER

## Title
V4's diet-breach examples name each eater and its tick, the way V5's and V8's examples already do

## Status
DONE

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
Built on origin/rpg-pre-v1-fixes c4c03f3c9 (it holds the V4 consumption code and Lane B's run_ledger edits). `RunLedger._diet_breach_examples` (reset with the other lists, capped at MAX_EXAMPLES) gets `{entity_id, tick, kind_group, source, item}` where `_count_diet_breaches` counts; the summary carries `diet_breach_examples`; `_check_diet_gates` appends them after the aggregate `{"consumption": ...}` rows. Counts and verdicts are untouched. The format doc's V4 row was not edited (testing-planner's file): it should mention the new example shape. After the pre-v1 PR squash-merges: `git rebase --onto origin/main c4c03f3c9 rpg-v4-diet-examples`.

## Test Summary
Unit: test_run_ledger (example named, capped at MAX_EXAMPLES while the count is not, reset between runs), test_rpg_gate_metrics (V4 emits the named example beside the aggregate row; violations unchanged). Real kernel: the frozen-name test ::test_a_meat_only_body_that_eats_plant_food_in_a_real_run_fires_the_v4_row now asserts the example carries the seeded wolf's entity_id, tick, kind_group, source and item. 52 passed. Final hash, seed 42, 5000 ticks, base c4c03f3c9 vs branch: frontier db7ade496f4f, urban a44bac862465, crowded 3f9675879f17, identical.

## Files Changed
src/observability/run_ledger.py, src/observability/rpg_gate_metrics.py, tests/unit/observability/test_run_ledger.py, tests/unit/observability/test_rpg_gate_metrics.py, tests/integration/observability/test_v4_counts_a_forbidden_meal_through_the_real_kernel.py

## Completion Summary
V4 examples now name each eater and its tick.
