---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
artifact_type: test_plan
tags: []
---

# Test plan
1. Grid (`tests/unit/engine/test_service_admission.py`): gold {0, price-1, price, price+5} x diet {prepared yes, no, undeclared} x action {EAT, REST} x law {CLAMP, ATOMIC}: `admits` == the real outcome of running `service_delta` + the real `ResourceTransactionResolver` (delivered effect and no gold change without delivery).
2. No non-atomic payment (ledger): under ATOMIC, gold falls iff the service is delivered; flags any gold decrease with no service.
3. Named f400: broke tired subject offered the inn bed iff REST would deliver (CLAMP: offered; ATOMIC: rests in place, no target).
4. Judge and EatScorer agree on open/closed for the same subject and tick through the real kernel (`tests/integration/...`).
5. `eat_update` diet gate equals `admits` diet branch.
6. V3 verdict: UNTRIED_STEP fails, POVERTY is non-fail, a tried step / delivered meal passes. Record JSON round-trips with the new field.
7. Scoped existing suites: unit/observability starvation + gate metrics, unit/engine (biological needs, service reach, carcass), unit/world, architecture, integration/scenarios.
8. Paired run hash-identical on main (slot from planner).
