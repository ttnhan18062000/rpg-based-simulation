---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL
tags: []
---

# plan - TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL

## Plan
1. tactical.py: compute panic_destination once; take the panic branch only if it is not None or _has_tactical_hostiles(entity, neighbors).
2. New tests (3): merchant-37 eats; a real destination still flees; a held panic beside a real tactical hostile keeps the freeze.
3. Measure paired 3 worlds x 42-46 vs origin/main, plus V3 on frontier 42; report the crowded_frontier stop line.
Scope guard: the two other retreat sites are not touched.
