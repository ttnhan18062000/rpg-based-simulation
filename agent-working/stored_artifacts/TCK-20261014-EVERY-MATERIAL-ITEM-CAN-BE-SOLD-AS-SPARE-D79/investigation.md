---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79
artifact_type: investigation
tags: []
---

# investigation - TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79

`SELLABLE_MATERIALS` (src/engine/shop_sale.py) named eight items, four of which exist in `data/content/world/items.yaml`; the rest of the MATERIAL items (stone, silver_ore, pelts, fangs, essences, shards) could never be sold. The category in content already decides each item's kind (`ItemRegistry.bootstrap`: weapon, armor, consumable, currency, else MATERIAL). All 40 catalog items declare categories. `iron_sword` on the old list is a WEAPON, so the spare-gear rule is kept by kind, not by name. `tool` and `trinket` items resolve to MATERIAL by the bootstrap fall-through and so now sell; disclosed.

Measurement (audit_mode, frame pacing off, pinned governor, seeds 42-46, 5000 ticks, three worlds, base 6de6b7038 vs 020480b66): zero accepted SHOP_SELL and WAGE transfers in all 30 runs; deaths, alive, worker deaths and starvation deaths identical per world. The sell path is dormant in the gate worlds (TOWN-202 support boundary). A mid-run tally of transfers by source (NODE, COMBAT, INHERIT, TOWN_SERVICE, CARRIED_FOOD) shows no SELL or WAGE attempt either.
