---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION

## Title
Once hunger is past its consequence line and taking health, starvation is itself a present threat to life: the hunger escalation is no longer dropped while another threat holds; goal selection weighs it (SURV-07 amendment, memo row 83, step two of the V3 fix).

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The v1 gate's V3 (frontier_living_world seed 42, merchant 37, starved at t4081 beside inn 20003). Step one (a49896e1c, a panic with no destination is not taken) removed the freeze but left V3 red: the merchant never selected a hunger goal, because `_escalated_unless_threatened` (src/ai/goals/scorers.py) returns the raw hunger (100) while any present threat holds, and town_return (155-161), fatigue and combat_retreat outscore raw hunger. Owner (2026-10-20), through the designer: fix V3 before v1. Memo row 83, SURV-07 amendment in docs/world_rules/life-body/survival-needs.md (designer fixup c942a35d8), Bible docs/mechanics/04_strategic_cognition.md section 1.

## Scope
- scorers.py: a hunger-only gate `_hunger_escalated_unless_threatened`: at hunger >= STARVING_LINE (95, where health starts to go; src/engine/starvation.py) the escalated pull is kept under a present threat, so the hunger goal competes in goal selection at its escalated value against the appraised threat's goals; below the line the old gate stands. Sleep is unchanged. No timer.
- Tests: unit (scorer keeps the pull at 100, drops it at 80; a wounded subject below the line still flees; a desperate subject with a hunter really attacking does not stand and eat) and a real-kernel merchant-37 case with a negative control.
- Mechanics Bible 04 section 1 and parity STRAT-284; an intentional divergence entry.
- Measured on top of step one: paired 3 worlds x 42-46, 5000t, plus V3 on frontier 42.

## Out of Scope
- The in-reach meal that needs no hunger project (after v1).
- Sleep escalation under a threat.

## Acceptance Criteria
- Merchant-37 forced case eats through the real kernel (negative control does not).
- Crowded_frontier stop line checked first; if it fires, STOP and report to the owner.
- V3 on frontier 42 reported.

## Related Tickets
- TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL (step one)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-07 amendment), docs/plans/systemic_world/owner_decision_memo.md row 83, docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261019-STARVATION-PAST-ITS-LINE-IS-A-PRESENT-THREAT-WEIGHED-IN-GOAL-SELECTION/

## Related Code Areas
src/ai/goals/scorers.py, src/engine/starvation.py, src/ai/goals/present_threat.py

## Assumptions / Open Questions
- "Past its consequence line and taking health" is read as hunger >= STARVING_LINE (95), the line where hp loss starts.

## Implementation Notes
Two call sites (EatScorer, _hunger_without_open_way) use the new gate.

## Test Summary
tests/unit/ai/test_starvation_is_a_present_threat_weighed_in_goal_selection.py (5) and tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py (2) pass. Paired runs (3 worlds x seeds 42-46 x 5000 ticks) against 864f7b281: stop lines not fired; frontier seed 42 people deaths 20 -> 29 (mean +2.0, SE 1.76) is reported in docs/guidelines/intentional_divergences.md 2.135. Gate V3 frontier_living_world seed 42: 0 violations.

## Files Changed
src/ai/goals/scorers.py, tests/unit/ai/test_starvation_is_a_present_threat_weighed_in_goal_selection.py, tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py, docs/mechanics/04_strategic_cognition.md, docs/parity_ledger/strategic_cognition.yaml (STRAT-284), docs/guidelines/intentional_divergences.md (2.135).

## Completion Summary
Past the starvation line a present threat keeps the hunger goal; a threat acting on the subject still pre-empts it tactically. Landed as built per designer ruling; the closing-hunter blind window is disclosed (v1 row C5).
