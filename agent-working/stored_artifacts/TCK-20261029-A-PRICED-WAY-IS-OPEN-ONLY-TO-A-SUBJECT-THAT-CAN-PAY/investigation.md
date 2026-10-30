---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
artifact_type: investigation
tags: []
---

# Investigation
- Payment law on main = clamp: building_services builds `ResourceTransferIntent(gold_delta=-price)`, `_service_result` (conservation.py:254) has `gold_cost=0`, so only `max(0, gold+delta)` (inventory.py:156) limits it; the meal/bed is delivered and the building credit is `min(gold, price)`. D73's `gold_cost=price` shape is the atomic law (rejects ACTION_EXHAUSTION below price).
- Open tests today are diet-only: ways.py:50, scorers.py:127-131; bed has no price test (scorers.py:93-97, with bed_reach 30). Consumer list: sent to rpg-planner (main f102085e0), accepted.
- Service-side extra: `service_building` requires `keeps_coin(entity)`; scorers do not. Out of the hash-identical scope; finding.
- `eat_update` free-meal diet gate: same predicate (`can_use_inn_meal`).
