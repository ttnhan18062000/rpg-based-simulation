---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
phase: active
date: 2026-10-29
tags: []
---

# TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY

## Title

One admission rule for ways, scorers and services: a way is open to a subject iff the service would actually deliver it now (working title ONE-ADMISSION-RULE-FOR-WAYS-SCORERS-AND-SERVICES; the id is kept because the owner's dispatch go, #715 6485905808, names it)

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found by the D73 (#781) traces from rpg-implementer-2, on tree 58c0821dc (src = 7cfd2cc0c). Files: /mnt/data/scratch-rpg-implementer-2/d73/trace2/.
- ways_in_reach (src/ai/goals/ways.py:50) adds INN_MEAL when inn_in_reach and can_use_inn_meal hold.
- can_use_inn_meal (src/engine/appraisal.py:86) checks only the diet, never gold.
- starvation_record._judged_ways (src/observability/starvation_record.py:75) returns the same map. So V3 counts INN_MEAL as open for a subject with gold 0, when the meal costs 5.
- EatScorer separately returns NO_AFFORDABLE_WAY below the price, so the decision code and the judge disagree.
- Gate run 40734781335 shows the two new V3 fails: urban s42 scout 17 and urban s46 hero 22.

rpg-designer ruling (2026-10-29). Sources: survival-needs.md SURV-06 l.335-350, and the SURV-07 amendment of memo row 27, l.750-790: "whether a way is open is judged for the subject (a meal it cannot pay for is not open to it; AGENCY-03)."
- A price-aware "open" is the correct meaning, not a gate workaround.
- Change the SHARED definition, not the judge alone. AGENCY-03 allows one meaning of "open".
- This is its own ticket. It lands BEFORE D73 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1), because it changes decision inputs.

## Scope
- First, before any code: list every consumer of ways_in_reach and can_use_inn_meal (at least scorers.py, building_services.py, domain/core_actions.py, starvation_record.py, ways.py), and say what each does with a way that is closed by price. Send the list to rpg-designer through rpg-planner.
- INN_MEAL is open only if gold >= the meal price. The inn bed is open only if gold >= REST_PRICE_GOLD. Read both prices from the same source the inn charges (src/engine/service_prices.py / building_services). No new constant. Rough rest and home stay free.
- V3 judge verdict, so a relabel cannot turn the gate green. The judge records, next to the ways, the opening steps in reach and whether each was tried: work_in_reach, and any forage way the subject's kind has.
  - A starvation where the meal was closed by price, but an opening step the subject could take was in reach and never taken, is still a FAIL: "opening step untried" (row 27: the pull goes to the step).
  - Only "no open way AND no step it can take" is SURV-06's poverty outcome, which is not a fail.
- FOLDED IN (rpg-designer, 2026-10-29): TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR. An unaffordable inn bed is not open, so the fatigue goal stops naming it, and a subject with no home in bed_reach rests in place (rough rest, Bible 04 l.40). That is the same definition change, so it gets one paired run.
  - (a) f400's acceptance carries over as a named test: a broke, tired subject with no home in reach does not walk to the inn bed, and rests in place.
  - (b) The consumer list marks the fatigue/bed consumers separately from the hunger/meal ones, so the paired run can attribute a change to the bed or the meal.
- Paired run, 3 gate worlds x s42-46 x 5000t, against its parent (decision 76). The free meal is still ON, so the effect may be small. The run shows it.

- Non-atomic payment check (rpg-designer, 2026-10-29): a subject that earns 6 gold and loses 5 with no meal stays hungry. The paired run must show no non-atomic payment. The tests include a ledger check that flags gold going down with no service delivered. Evidence: TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL (the t587 case, base urban s46 worker 4).

- Reach bounds (rpg-designer, 2026-10-29). For each reach field (inn_in_reach, work_in_reach, the forage way), the consumer list states the distance bound it actually applies, if any, measured against SURV-06/07's "within reach" (the bed has an explicit SLEEP_DEBT.bed_reach). A field with no bound is a semantic defect in this same shared definition. It is in scope here if small; otherwise it goes back to rpg-designer as a finding.
- Note for the consumer list (2026-10-29, worker 1 trace c1610/w1c/): inn_in_reach returned inn 20003 on every tick, including from 11 tiles away at (38,24). Check whether "in reach" is a real proximity test or just "an inn exists". Whether a priced way counts as open depends on both.

## Out of Scope
- Removing the free meal (D73).
- Making a broke subject actually earn: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO.

## Acceptance Criteria
- The consumer list has been ruled on by rpg-designer before any code changes.
- The named f400 test (a) passes.
- Unit tests: below the price is closed, at the price is open, above is open, for both meal and bed. Undeclared diet keeps the legacy behaviour.
- The judge and EatScorer agree on open/closed for the same subject and tick (one test through the real kernel).
- The V3 verdict has "opening step untried" as a FAIL and poverty as a non-fail, with tests for both.
- Bible 04 and the parity ledger are updated. The divergence class is Bug Fix, citing row 27 and AGENCY-03.
- Paired run with no unowned STOP. The two urban fails stay fails unless the trace shows work was out of reach.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (D73, #781; lands after this ticket)
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
- TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR
- TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06, SURV-07 row-27 amendment)
- docs/mechanics/04_strategic_cognition.md (Standing Needs Escalate)
- docs/guidelines/intentional_divergences.md 2.150

## Related Stored Artifacts

## Related Code Areas
- src/ai/goals/ways.py, src/engine/appraisal.py, src/observability/starvation_record.py, src/ai/goals/scorers.py, src/engine/building_services.py, src/engine/domain/core_actions.py, src/engine/service_prices.py

## Assumptions / Open Questions
- Sequence: before D73. Independent of :1610. Not dispatched.

## Implementation Notes

### DESIGNER RULING 2026-10-29. This SUPERSEDES Scope and Acceptance Criteria wherever they differ.
On main the service clamps the price (EAT_PRICE_GOLD and REST_PRICE_GOLD are charged as min(price, gold held), and the meal or bed is still delivered). So a broke subject IS fed and bedded on main. The original "INN_MEAL open only if gold >= price" assumed atomic payment and would encode a world that does not exist yet. The old title, "A priced way is open only to a subject that can pay", is now the consequence on the D73 stack, not this ticket's rule.
- RULE (AGENCY-03 / row 27, "judged for the subject"): a way is open to a subject iff the service would actually deliver it to that subject now.
- ONE shared admission function is used by building_services EAT/REST (building_services.py:64, :67-70) AND by every "open" test: ways.py:50 ways_in_reach, scorers.py:127-131 EatScorer, scorers.py:93-97 FatigueScorer, and starvation_record.py:75 and :214.
  (a) It reads the same payment law the service applies (the clamp today; atomic after D73/N1). There is no second copy of the price rule and no feature-flag string in any consumer.
  (b) An agreement test: for a grid of subjects (gold 0, below price, at or above price; diet yes/no), admission == the service's real outcome, for both EAT and REST. It runs under the clamp law and under the atomic law.
  (c) Main behaviour is unchanged: a paired run on main must be hash-identical, because no consumer's answer changes. A mismatch is a STOP to the designer. This needs the host slot from rpg-planner.
  (d) The flip (D73 or N1 makes payment atomic) needs no edit to any consumer, and the D73 re-measure shows this.
- f400 (bed): it follows the same function. Named test: a broke, tired subject is offered the inn bed iff REST would deliver it. That is live on main (true, it walks to the bed). The D73 case (it rests in place) is pinned through the admission-grid test under the atomic law.
- V3 judge, kept in this ticket: an additive, judge-only typed field. For each opening step in reach, record whether it was tried (dispatched at least once in the record window). Verdicts: untried while a step is takeable = FAIL; no open way and no takeable step = poverty outcome (non-fail). Unit tests cover all three verdicts.
- OUT of this ticket: reach bounds. These move to TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND, which runs after EARN.
- Lane B consumer list (main f102085e0) is accepted as the consumer inventory. core_actions.py:64 eat_update stays as the diet gate on the action side, and it must agree with the admission function's diet branch.
### Implementation (rpg-implementer-2, branch rpg-one-admission)
- `src/engine/service_admission.py`: `admits(entity, action, law=None)`, `PaymentLaw`, the one constant `SERVICE_PAYMENT_LAW = CLAMP`. Read by `building_services.service_delta`, `ways_in_reach`, `EatScorer` and the bed test in `SleepScorer`; the starvation record follows through `ways_in_reach`.
- ATOMIC is exercised by tests only (the constant stays CLAMP). Under ATOMIC it gates `service_delta` only (None below the price). The transfer-carried shape (`gold_cost` plus the effects on the intent, `readiness_update` in the resolver) is left to D73's rebase, because it touches the apply path.
- keeps_coin stays out of `admits` (designer ruling A); a non-xfail test pins the gap and names TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT.
- V3: `StarvationDeathRecord.opening_steps_in_reach()` and `verdict()` (derived; the FAIL set equals the old untried rule, so the gate file is unchanged).
- Divergence 2.150 and parity STRAT-290 (assigned by the lead).

## Test Summary
## Files Changed
## Completion Summary
