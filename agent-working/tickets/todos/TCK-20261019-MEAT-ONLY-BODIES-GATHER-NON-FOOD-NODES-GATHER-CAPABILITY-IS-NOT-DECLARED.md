---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-MEAT-ONLY-BODIES-GATHER-NON-FOOD-NODES-GATHER-CAPABILITY-IS-NOT-DECLARED
phase: open
date: 2026-10-19
tags: []
---

# TCK-20261019-MEAT-ONLY-BODIES-GATHER-NON-FOOD-NODES-GATHER-CAPABILITY-IS-NOT-DECLARED

## Title
A meat-only body gets a `harvesting` goal at a non-food node: harvesting is open to every body; it must be open only to a kind that declares the capability (D56).

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the v1 gate's V4 hits (frontier_living_world seeds 44 and 45, run 39212800104 on 864f7b281). A wolf (seed 44, entity 49, kind alpha) and a spider (seed 45, entity 32, kind predator_hunter), both bodies whose diet is exactly meat, gather a non-food herb node. V4 itself was a false positive of an item-blind key (fixed by TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION, which counts consumption); this ticket is the underlying rule gap.

Origin: `HarvestScorer.score` (src/ai/goals/scorers.py:19-49) scores the nearest resource node at 50/distance, and its only diet gate is `_may_gather` (scorers.py:52-54): "a food item the subject's diet cannot eat is not gathered; **anything that is not food is gathered as before**". Herb is not food (`food_class("herb")` is None), so a meat-only body passes, the goal wins when nothing scores 20 or more above it (intelligence.py ~1584-1613), a `harvesting` project is made, and `interaction.py:157-166` completes the node transfer for any body. Wolf 49's project started at tick 732 (no project at tick 712, hunger 22, so not a hunger goal).

## Scope
- Replace `_may_gather`'s "anything that is not food" with a declared gather capability on the kind, read from content (D56: no species names in code), so harvesting is open only to a body whose kind declares it.
- Measure as its own step after v1, one variable, paired against v1 (D76).

## Out of Scope
- The V4 metric (done in TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION).
- The other dead name-checked rules (D78 list in v1_disclosure.md).

## Acceptance Criteria
- A kind that does not declare the capability never receives a `harvesting` goal at any node; a kind that declares it still does; no species name appears in the scorer.
- The before and after numbers below are re-measured on the same seeds.

## Before-numbers (from the traces, no extra run)
- Seed 44 (frontier_living_world, 5000t): wolf 49 completed 8 accepted node transfers of herb at ticks 745, 774, 851, 895, 950, 994, 1049, 1093, alternating a `harvesting` project (objective harvesting_10009) and `resolve_blocker` (blocker_node_10009), node 10009; harvesting begins at tick 732. These were the only meat-only node transfers in the run.
- Seed 45: spider 32 completed 4, at ticks 977, 1011, 1058, 1066, node 10001 (herb).
- Not measured: the number of ticks spent walking to and channelling the node (the probe logged completions only). The re-measure should add "meat-only node-INTERACT ticks" so before and after compare.

## Related Tickets
- TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION, TCK-20261014-EVERY-COMPILED-LIVING-BODY-RESOLVES-TO-A-DECLARED-DIET-OR-THE-WORLD-DOES-NOT-COMPILE (D74)

## Related Docs
- docs/plans/systemic_world/v1_disclosure.md; /mnt/data/scratch-rpg-implementer/v1_gate_fails_A.md (trace)

## Related Stored Artifacts
None.

## Related Code Areas
src/ai/goals/scorers.py (HarvestScorer, _may_gather), src/systems/strategic_systems/intelligence.py (goal selection, blocker_node), src/engine/interaction.py.

## Assumptions / Open Questions
- Where the gather capability is declared (body model or species content) is the designer's call.

## Implementation Notes
None yet.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
