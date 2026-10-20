---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION

## Title
The gate's V4 counts a consumption outside the eater's diet, not any node transfer by a meat-only body.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The v1 gate (run 39212800104 on 864f7b281) reported V4 hits `meat|NODE|accepted` on frontier seeds 44 (8) and 45 (4). Traced: one wolf (seed 44, entity 49) and one spider (seed 45, entity 32), both meat-only bodies, gathered a non-food herb; the key ignored the item. Designer ruling: V4 is about what a kind EATS (SURV-06, D44).

## Scope
- run_ledger counts, in a new `diet_breaches` tally key, an accepted EAT intent that removes a food item whose class is outside the eater's diet (carried or corpse food). rpg_gate_metrics V4 reads it; the NODE rule is gone; the inn rule is unchanged; the oracle text says so.
- Tests: wolf at a herb node is not a hit; a meat-only body eating plant-class food (wild_berries) is a hit; a refused try and an in-diet corpse meal are not.

## Out of Scope
- The wolf/spider harvesting gap (todo TCK-20261019-MEAT-ONLY-BODIES-GATHER-NON-FOOD-NODES-GATHER-CAPABILITY-IS-NOT-DECLARED).

## Acceptance Criteria
- V4 = 0 on frontier seeds 44 and 45; the final state hash is identical on 3 worlds, seed 42 (an observer-only change).

## Related Tickets
- TCK-20261019-MEAT-ONLY-BODIES-GATHER-NON-FOOD-NODES-GATHER-CAPABILITY-IS-NOT-DECLARED

## Related Docs
- /mnt/data/scratch-rpg-implementer/v1_gate_fails_A.md

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
src/observability/run_ledger.py, src/observability/rpg_gate_metrics.py, src/ai/goals/kind_group.py

## Assumptions / Open Questions
- The harness hash of rpg_gate_metrics.py changes with this edit.

## Implementation Notes
New helper `eats_outside_its_diet` in kind_group.py; `RunLedger._count_diet_breaches`.

## Test Summary
tests/unit/observability/test_rpg_gate_metrics.py and test_run_ledger.py: 38 passed (3 new ledger cases, V4 metric test rewritten); lint-imports 17 kept. Proof: V4 = 0 on frontier seeds 44 and 45 (5000t), was 8 and 4; final state hash identical base vs fix on frontier_living_world, urban_political and crowded_frontier, seed 42, 2000 ticks.

## Files Changed
src/ai/goals/kind_group.py, src/observability/run_ledger.py, src/observability/rpg_gate_metrics.py, tests/unit/observability/test_rpg_gate_metrics.py, tests/unit/observability/test_run_ledger.py.

## Completion Summary
Closed by hand on branch rpg-v4-consumption-check (ticket filed after the code commit 0b266d856, which already cites it).
