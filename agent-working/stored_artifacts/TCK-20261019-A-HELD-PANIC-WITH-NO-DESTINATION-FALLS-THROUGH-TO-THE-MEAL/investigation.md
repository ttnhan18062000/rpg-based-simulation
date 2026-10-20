---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL
tags: []
---

# investigation - TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL

## Finding
Merchant 37 (frontier_living_world seed 42) at (41,31), hp 7-14/85, gold 0, hunger 100, beside inn 20003 at (40,31), with predator_hunter 45 adjacent but one-sided. In tactical.py the `emotion.is_fleeing and threats` branch returns a PANIC_RETREAT before in_place_survival_update (tactical.py:249) and before the arrival branch (`if not hostiles`, tactical.py:253). `retreat_destination` returned None: `containing_region` is None at (41,31) (hometown ends at x=40, trading_hometown starts at x=45) and 37 has no home_region_id, so `_destination_or_hold` holds. Scenario: /mnt/data/scratch-rpg-implementer/v3_pin.py. The flee flag turns on between hp 16 and 19 of 85; at hp >= 19 the same merchant eats through the arrival.
Existing order with a real tactical hostile (healthy hero, hostile monster adjacent): it ATTACKS; a wounded hero with a strong hostile: PANIC_RETREAT. So the fall-through must keep the freeze when a real tactical hostile exists, or it would turn freezing into attacking.
