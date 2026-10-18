---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79
artifact_type: investigation
tags: []
---

# investigation - TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79

## Findings

- `MarketSystem.get_item_base_value` held a hardcoded name table and consulted the registry only for items off the table; `get_item_kind` parsed item names. Both violate D56/D79 (code reads no names).
- The registry already carries `ItemDefinition.value` and `ItemKind` for every catalog item (40 shipped items all declare `base_value`), so the table is redundant for every gate world.
- `grass_cover` declares 0; the old `value > 0` guard hid that behind 10. It now prices at the market floor (1 gold).
- `src/content/schema.py` gave `base_value` a default; making it required is hash-neutral because every shipped item declares one.
- The registry's built-in no-catalog fallback items (iron_ore, wood, WOOD, herb, bread, healing_potion, iron_sword, steel_sword, iron_plate, leather_armor, wooden_staff, iron_dagger, wooden_club, gold_coin, gold, ore, ORE, stone, ancient_core) are code-held item data, not run in the gate worlds; disclosed, removal is its own step after v1.

## Measurement

30 paired audit_mode runs (3 worlds x seeds 42-46 x 5000 ticks): all 15 pairs have an identical final digest; no item sold in any run (sell path dormant in the gate worlds). Base-vs-base repeat of frontier 42 identical; the final tip matches the measured arm on seed 42 in all three worlds.

## Pre-existing issue noticed

`tests/unit/worldassembly/test_corpus_diversity.py::test_generated_frontier_3_42_extended_population_stability` is marked only `slow`, so conftest's 60 s medium budget can kill it (it needs ~270-350 s). It passes with `--resource-budget off`. Not caused by this change.
