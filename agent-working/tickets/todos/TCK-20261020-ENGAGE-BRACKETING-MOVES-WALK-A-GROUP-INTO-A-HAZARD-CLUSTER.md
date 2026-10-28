---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER

## Title
Seven people under combat-engage projects die to HAZARD in one cluster within 8 ticks: do BRACKETING moves path into hazard tiles?

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced frontier_living_world seed 42 (5000t) on 2026-10-20 for V3 step (ii) (rpg-v3-starvation-threat 29d4d3d07 vs the old gate). It found 10 extra people deaths. None was on the (ii) path: they are trajectory drift from a first divergence at t991, where leader 30 (hunger 99.1) dropped proj_combat_engage_530 under (ii).
Of the 10, seven (ids 8, 10, 1, 2, 4, 11, 9) die by HAZARD in ticks 1281-1288 inside one cluster around (42-45, 43-45). All were on BRACKETING moves under proj_combat_engage_*, with hp 20-120 and hunger 44-64: healthy, not starving. A group walking into a hazard together while bracketing looks like a pre-existing movement defect that the drift exposed. (ii) did not cause it.
Files:
- /mnt/data/scratch-rpg-implementer/v3proof2/trace_b.json, trace_ii.json
- script /mnt/data/scratch-rpg-implementer/v3_trace_an.py

## Scope
- Name the hazard at (42-45, 43-45) on frontier and its declared damage.
- Find out whether BRACKETING / engage movement scores or avoids hazard tiles, compared with ordinary travel (route or terrain cost, D72).
- Find out why several members enter the cluster in the same window: the group following the leader, a shared bracket target, or something else.
- Fix it so that combat movement respects hazards the way travel does, if it doesn't. Measure it as its own step: paired 3 × 42-46, crowded first.

- Second finding (designer 2026-10-20): the group keeps its engagement after its leader leaves. Leader 30 dropped proj_combat_engage_530 at t991 to eat, which is the rule working as written, but the members stayed on proj_combat_engage_* and bracketed on without it. Find out whether a group engagement should end or re-plan when the leader leaves.
- Measure it together with H1 (COMBAT-ENGAGEMENT-HOSTILITY) and the owner's after-v1 hazard-avoidance item (the D75 gap), one measured step, so the three combat-movement changes are not stacked unmeasured.

## Out of Scope
- V3 step (ii) and the hunger/threat gate.

## Acceptance Criteria
- A real-kernel test: a subject on a bracketing move next to a hazard tile does not step into it when a safe alternative exists, or a stated reason why it should.
- The seed-42 (ii) arm no longer loses the 7 people to that cluster, or the remaining deaths are explained.

## Related Tickets
- V3 step (ii) ticket on rpg-v3-starvation-threat
- D72 terrain cost
- H1 TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (measure together)
- the owner's after-v1 hazard-avoidance item (D75 gap)
- disclosure N3 (designer 8e4071cc2) carries this attribution

## Related Docs
- docs/mechanics/02_combat_laws.md (tactical modifiers)
- docs/mechanics/05_world_evolution.md (hazards)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine tactical movement (BRACKETING)
- hazard damage application

## Assumptions / Open Questions
- Is the hazard visible to perception in the bracketing scorer?

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary
