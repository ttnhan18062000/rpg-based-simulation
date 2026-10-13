---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-A-HELD-GATHERER-ON-A-REGROWING-PATCH-IS-NEVER-RELEASED-TO-EAT
phase: done
date: 2026-10-12
tags: []
---

# TCK-20261012-A-HELD-GATHERER-ON-A-REGROWING-PATCH-IS-NEVER-RELEASED-TO-EAT

## Title
A subject holding a HARVEST/INTERACT on a node that still has charges is never released to decide EAT, so a grazer gathers grass while its hunger climbs.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1 (food-way validity; should land before the M0 baseline v1)

## Request Summary
`_survival_action_ends` ends a held WORK/SLEEP/REST but not a held HARVEST/INTERACT on a node with charges. On a regrowing cover patch the grazer is never released.
- LB-S22 trace: a grazer holding 2-4 grass for 150 ticks (76-226), hunger 77.6 -> 92.6, no meal.
- 9 runs: grass gathered 56.0/104.7/80.3 vs meals 12.0/17.7/5.7 (21/17/7%).
This is the same shape as the held-move need wake (2.106) and the hunger wake (2.115).

## Scope
- A held HARVEST/INTERACT is released when hunger >= SURV-07 ESCALATION_ONSET and the subject carries food it can eat (diet gate), so the brain decides EAT. Reuse the need-wake cadence, with no new constant.
- Decide with rpg-planner: release on any pressing need, or only when carried food can meet it. Default: only when carried food exists.
- Tests: a grazer with grass and hunger past onset eats within a cadence; a sated gatherer keeps gathering; a gatherer with no edible carried food keeps gathering.
- Measure with the paired protocol: grass meals / grass gathered, plant-eater survival, starvation.

## Out of Scope
Herd births (ECOL-03).

## Acceptance Criteria
Grass meals per gathered grass rises materially; no starvation with carried edible food.

## Related Tickets
2.106 need wake; 2.115 hunger wake; the grazing PR (D59).

## Related Docs
SURV-06, SURV-07.

## Related Stored Artifacts
Lane A probes/hunting_grazing_measurement.txt.

## Related Code Areas
`_survival_action_ends`; scheduler `_is_need_woken`; the harvest action.

## Assumptions / Open Questions
None.

## Implementation Notes
The release is in the scheduler's need wake (_is_need_woken), not _survival_action_ends: a held INTERACT is not a survival action. Divergence 2.120, PROG-134, Bible 04 paragraph. The no-progress hold is a separate draft ticket.

## Test Summary
tests/unit/engine/test_pressing_hunger_releases_a_held_gatherer.py (4); wake and eat tests (140 passed). Paired 20-run measurement in 2.120.

## Files Changed
src/engine/scheduler.py; tests/unit/engine/test_pressing_hunger_releases_a_held_gatherer.py; docs 2.120, Bible 04, PROG-134.

## Completion Summary
Grazers held on a regrowing patch are released to eat once they carry grass (held-INTERACT ticks of plant-eaters 8177 to 4442). Empty-pocket no-progress holds remain, as a later ticket.
