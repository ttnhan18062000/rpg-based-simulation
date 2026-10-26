---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1

## Title
Parked after v1: the hunger pull aims at the nearest open way whose route is not threatened by a live perceived hostile (built, measured once, not landed)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This change was built for raider 27 (crowded_frontier s45, V3 at t1091). Lane A's probe at d805aeaa7 then showed what actually happened: raider 27's PANIC_RETREAT shuttle came from the tactical pass reading CORPSES as threats (tactical.py `_perceived_threats` has no alive filter). Workers 3 and 2 and guard 11 had died of HAZARD before about t905. The premise "non-acting perceived hostiles on the route" was those corpses.

The designer's ruling (2026-10-20): fix the corpse-threat hard bug alone before v1. The safe-route change is still right for LIVE hostiles on a route, but no gate world has an evidenced case for it, so it is parked. It returns before v1 as its own second step only if V3 crowded 45 is still red after the corpse fix. Otherwise it waits until after v1 and is measured against v1.

## Scope
- Branch rpg-hunger-safe-route: built at 2481edcb4, measured at d805aeaa7.
  - src/ai/goals/safe_route.py; the active-objective path in intelligence.py (around lines 1260-1541).
  - The route test: a perceived live hostile within its combat.range + MOVE_STEP_TILES (1) of the chord. Retarget the existing project; hold until reached or threatened; all-threatened keeps the nearest.
  - Tests: tests/unit/ai/test_hunger_route_retarget.py (6) and tests/integration/observability/test_hungry_raider_turns_to_an_unthreatened_way_through_the_real_kernel.py (2).
  - Docs on that branch: Bible 04 §1, parity STRAT-285, divergence 2.136.
  - Working ticket on that branch: TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED.
- When picked up:
  - rebase onto the corpse fix (or v1);
  - re-pin the forced tests so they no longer depend on live townsfolk standing where corpses lay;
  - re-measure paired against v1 (seeds 42-46, D76);
  - get a new designer docs patch. The earlier patch (row 84, the SURV-07 amendment, N7) was withdrawn.
- This step also needs a real case with a live hostile on the route, or the owner's acceptance without one.

## Out of Scope
- The corpse-threat fix (Lane A's own ticket, before v1).
- HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE.

## Acceptance Criteria
- A gate-world case (or a named live-hostile scenario) where the safe-route change alters the outcome.
- A paired D76 reading against v1 with no unexplained drift.
- Docs from the designer's new patch.

## Related Tickets
- TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED (on the rpg-hunger-safe-route branch)
- TCK-20261019-RECORD-BASELINE-V1
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md (row 84, to be rewritten by the designer)
- docs/mechanics/04_strategic_cognition.md §1

## Related Stored Artifacts
- The first paired run (7b1528861 vs d805aeaa7, seeds 42-46): /mnt/data/scratch-rpg-implementer/paired_hs/run.log. Deaths showed no drift; crowded had a worker STOP, one entity on s45, not traced; V3 crowded 45 stayed 1.
- The probe: /mnt/data/scratch-rpg-implementer/probes_hs/out/ (r27_diag, r27_trig, r27_src, r27_bv)

## Related Code Areas
- src/ai/goals/safe_route.py (branch only)
- src/ai/intelligence.py active-objective path

## Assumptions / Open Questions
- The worker 1 STOP on crowded s45 in the first paired run was never traced. Re-check it when this is re-measured.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
