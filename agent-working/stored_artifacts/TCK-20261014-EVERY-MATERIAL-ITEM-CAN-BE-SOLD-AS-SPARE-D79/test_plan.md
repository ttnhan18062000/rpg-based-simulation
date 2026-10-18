---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79
artifact_type: test_plan
tags: []
---

# test_plan - TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79

- A material the old list never named (stone, ancient_core) sells whole; a catalog material sells by category alone; an item with no category fails bootstrap; an unknown item is not sold; the sale module names no item and has no SELLABLE_MATERIALS.
- Regression: tests/unit/world/test_sell_is_a_chosen_act.py, test_economy_contract.py, tests/unit/resource, test_registry_bridge.py.

## Proof Plan
- Level: unit plus paired simulation measurement.
- Proof kind: behavioural test and paired audit_mode runs.
- Oracle source: Mechanics Bible 03 section 4 (EXCH-02) and owner ruling D79.
- Expected effect: a MATERIAL item sells as spare; a categoryless item fails compile; the paired runs show no change where the sell path is dormant.
- Selected commands: `python -m pytest tests/unit/world/test_every_material_item_sells_as_spare.py tests/unit/world/test_sell_is_a_chosen_act.py -q`.
