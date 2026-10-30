---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
artifact_type: plan
tags: []
---

# Plan: one admission function (designer ruling 2026-10-29 supersedes the ticket Scope)

## Design
1. New `src/engine/service_admission.py` (engine layer; ai/observability import it, as they import appraisal today).
   - `PaymentLaw` (str Enum: `CLAMP`, `ATOMIC`) and ONE module constant `SERVICE_PAYMENT_LAW = PaymentLaw.CLAMP`. This is the single place the law lives; D73 / N1 flips it (or replaces it) and no consumer changes.
   - `service_charge(action, law=None) -> ChargeTerms(gold_delta, gold_cost)`: CLAMP = `gold_delta=-price, gold_cost=0` (today's intent: resolver clamps via `max(0, gold + delta)`); ATOMIC = `gold_cost=price, gold_delta=0` (the D73 shape, `_service_result` rejects with ACTION_EXHAUSTION below price). Price from `service_prices.py` only.
   - `admits(entity, action, law=None) -> bool`: EAT = `can_use_inn_meal(entity)` and payment ok; REST = payment ok. Payment ok = CLAMP: always; ATOMIC: `gold >= price`.
2. `building_services.service_delta` builds REST/EAT charges from `service_charge` (so service and admission read one law) and refuses via `admits` instead of its own `can_use_inn_meal` test. Behaviour on main unchanged.
3. Consumers call `admits(entity, "EAT")`: `ways.ways_in_reach` (INN_MEAL), `EatScorer`. `admits(entity, "REST")`: `FatigueScorer` bed. `starvation_record` gets it through `ways_in_reach` (:75/:214 need no edit beyond the new field below). `eat_update` (core_actions.py:64) keeps its diet gate and a test pins it to `admits`' diet branch.
4. V3 judge: additive typed `OpeningStepTried(kind, takeable, tried)` tuple on `StarvationDeathRecord` (`opening_steps_in_reach`), `tried` = the step's action dispatched at least once in the record window (same `_attempted` bookkeeping). Verdict helper `starvation_verdict(record)`: `UNTRIED_STEP` (FAIL) if any takeable step is untried and no way was attempted/delivered; `POVERTY` (non-fail) if no open way and no takeable step. Where the V3 gate reads the record it counts UNTRIED_STEP as a FAIL; gate/baseline files are not edited.
5. Docs: Bible 04 (Standing Needs: a way is open iff the service delivers), parity ledger entry, intentional_divergences (Bug Fix, row 27 / AGENCY-03), mechanisms.yaml untouched (planner owns).

## Not done / flagged
- `service_building` also requires `keeps_coin` (the trait); the scorers do not. Adding it to `admits` would change main behaviour and break the hash-identity gate, so it is NOT in `admits`; flagged to planner as a finding.
- Reach bounds out (TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND).

## Gate
Paired run on main, 3 gate worlds x s42-46 x 5000t: hash-identical or STOP to planner. Needs the slot.
