---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE

## Title
A low-hp subject near a hostile that neither engages nor acts gets a no-op PANIC_RETREAT every 10th tick, and its step toward food one tile away is refused, so it starves (gate V3, frontier_living_world s43 merchant 38)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Main gate run 40653115297 (2c4869d61) has an unowned V3 at frontier_living_world s43: merchant 38 starves at t2518 with every way untried. Cached paired arms show it first appears with step A's R build (358f4cb7f); F4 has no effect and H2 is neutral. Three pure traces on d914bace7 (final hash 10b2e767a9ac equal with and without the probe; files /mnt/data/scratch-rpg-implementer/n15trace/out/trace{,2,3}.json) show:
- t2319-2341: hostile 30 acts on 38 (hp 40 -> 5), CombatRetreat is top, and 38 reaches (31,41).
- From t2342 no hostile acts and none is engaged with 38 (is_engaged, hostile_acts_on and engaged_adjacent_hostile are all False for hostiles 30 and 49). Hunger is the top goal with the inn way open (NeedAccess way_within_reach) until t2454; fatigue and then town_return from t2455.
- Every 10th tick, tactical.py:536-544 (the "pure retreat if hp is very low and engaged" branch of evaluate_entity_intent) is reached with a perceived-hostile list and hp_percent < 0.15. It has no engaged or acts-on gate and no hunger-line yield. retreat_destination returns None, so _destination_or_hold returns the subject's own tile: a no-op ENTITY_MOVE PANIC_RETREAT, which ends at once on the next tick (the task falls back to idle ENTITY_ACT).
- The current hunger project's objective targets (31,40), one tile north, which is unoccupied. candidate_selector.movement_target returns (31,40) on 7 of 19 ticks (t2342-2360), but the position never changes: the step is refused downstream of movement_target. The refusing line and ReasonCode are not traced yet. The stored nav target also flips between (31,40), (31,41) and None.
- 38 dies at t2518 with hunger 100 and hp 0.

## Scope
1. Trace the refusal: the movement phase's resolution for 38 at t2345 (file:line and ReasonCode), and the reset of the stored nav target between panic ticks.
2. Decide and fix, as one measured behaviour step:
   (a) tactical.py:536: what gates the low-hp pure retreat. The name says "engaged", but the code reads only perceived hostiles. Align it with step A's rule (retreat only against a hostile that acts) or with the engagement predicate, and handle a None retreat destination without stamping a no-op move.
   (b) the downstream refusal of the step to (31,40), if it is a defect of its own.
   Any semantic choice in (a), i.e. which predicate gates a low-hp retreat, goes to rpg-designer before code.
3. Measured as a behaviour step (decision 76) against its parent; report fls s43 merchant 38 and V3 on the gate worlds.

## Out of Scope
- The held flight and the REGROUP->RETREAT relabel step (post-M1, row 91).
- D73 (free meal).

## Acceptance Criteria
- A unit or scene test: a low-hp subject with a perceived but non-acting, non-engaged hostile and a reachable eat objective steps toward and eats. Its tactical intent is not a no-op PANIC_RETREAT.
- The refusal reason found in Scope 1 is named in the ticket with file:line.
- Paired step report; frontier_living_world s43 V3 entity 38 gone, or the reason it is not.
- Divergence entry (Bug Fix), Bible 04 / combat rulebook sentence for the low-hp retreat gate, parity entry.
- SimQ criterion (row 82): the outcome is already carried by the movement and task records, so no new event type.

## Related Tickets
- TCK-20261028-N15-KNOWN-V3-STARVATIONS-RECHECK-ON-THE-GATE-AFTER-STEP-A (where it was found)
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md row 91
- docs/mechanics/02_combat_laws.md, docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/n15trace/out/ (scratch, not in the repo)

## Related Code Areas
- src/engine/tactical.py (:214-229 panic, :536-544 low-hp retreat, _destination_or_hold, retreat_destination)
- src/engine/candidate_selector.py (movement_target)
- the movement phase resolution (to be located)

## Assumptions / Open Questions
- Owner question pending (via lead-planner-u24): own the s43 V3 as a scoped known entry until this lands, or hold M1 for the fix.
- Why step A exposes it (hypothesis: before step A, 38's hp never fell below 0.15 here) is untested.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
