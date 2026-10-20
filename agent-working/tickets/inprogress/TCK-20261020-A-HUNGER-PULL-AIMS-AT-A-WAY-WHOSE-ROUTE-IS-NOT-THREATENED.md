---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED

## Title
The hunger pull aims at the nearest open way whose route is not threatened, and holds its choice until reached or threatened (SURV-07 amendment, memo row 84)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The v1 gate run on 7b1528861 has one unowned red: V3, crowded_frontier seed 45, raider 27 starved at t1091 with FORAGE, INN_MEAL and SCAVENGE untried. Its hunger project aimed at the town inn from t633 and never changed target; it shuttled on y=40 between walking west and panic retreats from townsfolk on the route, while an open unthreatened forage node was 35-38 tiles east. The owner chose to fix it before v1 (designer shape, memo row 84).

## Scope
- src/ai/goals/safe_route.py and the hunger branch of the active-objective path in intelligence.py: a hunger project whose route is threatened (perceived hostile on or beside it) retargets to the nearest open way whose route is not, keeps it until reached or threatened, and leaves the objective alone when every way is threatened.
- Tests, Bible 04, parity STRAT-285, divergence 2.136, the designer's docs patch (memo row 84, SURV-07 amendment, disclosure N7/N8).

## Out of Scope
- A town inn serving a hostile raider (N8, after v1). Panic from non-acting perceived hostiles (not taken: designer). Counters, timers, remembered-hostile store.

## Acceptance Criteria
- Forced raider-27 case turns to the forage node and eats through the real kernel; the control shuttles.
- Unit tests: re-choice, commitment, all-threatened keeps the nearest, unthreatened never re-chosen.
- Paired measurement reported; V3 crowded 45 = 0.

## Related Tickets
- TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md row 84; docs/world_rules/life-body/survival-needs.md SURV-07; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED/

## Related Code Areas
src/ai/goals/safe_route.py, src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Beside the route is the hostile's own attack reach (combat.range) plus one step of the straight line (designer ruling 2026-10-20); a bent route is judged by its chord.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
