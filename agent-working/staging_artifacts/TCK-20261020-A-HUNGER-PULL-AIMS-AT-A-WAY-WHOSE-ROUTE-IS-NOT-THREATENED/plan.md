---
status: active
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED
tags: []
---

# plan - TCK-20261020-A-HUNGER-PULL-AIMS-AT-A-WAY-WHOSE-ROUTE-IS-NOT-THREATENED

1. src/ai/goals/safe_route.py: retarget_if_threatened (perceived hostiles via perceived_hostiles, route = straight walk, beside = ROUTE_BESIDE_TILES, open ways = inn in reach + open opening steps).
2. intelligence.py: in the active-project branch, a hunger project calls it before the completion checks; the result retargets the same project (typed ObjectiveState).
3. Tests, Bible 04, parity STRAT-285, divergence 2.136, designer's memo row 84 / SURV-07 / N7-N8 patch.
4. Paired measurement (asked of rpg-planner first).
