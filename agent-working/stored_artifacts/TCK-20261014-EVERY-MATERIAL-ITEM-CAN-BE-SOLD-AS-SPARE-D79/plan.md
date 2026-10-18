---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79
artifact_type: plan
tags: []
---

# plan - TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79

1. `spare_quantity` reads the item's registry kind: MATERIAL sells whole; WEAPON and ARMOR sell beyond the last (or equipped) unit; nothing else sells (food keeps its surplus rule). `SELLABLE_MATERIALS` is removed.
2. `ItemRegistry.bootstrap` raises for a catalog item with no categories (the compile error).
3. Tests: `tests/unit/world/test_every_material_item_sells_as_spare.py`.
4. Measure alone under audit_mode (paired, base-vs-base self-check); divergence entry; parity TOWN-202 evidence.
