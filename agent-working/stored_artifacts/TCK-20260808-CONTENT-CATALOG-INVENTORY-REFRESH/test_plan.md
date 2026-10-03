---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [content, world, documentation]
---

# Test Plan — TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH

## New tests — `tests/tools/test_content_inventory.py`

1. `test_all_categories_present` — the generator's own output has an entry for every category
   D07 tracks (no silent omission).
2. `test_counts_are_real_not_placeholder` — spot-check 3 categories (Items, Factions, Recipes)
   against a direct, independent re-count of their real source files (not tautological
   computed-vs-computed).
3. `test_world_modules_and_compositions_counted_by_file` — `world_modules`/
   `world_compositions` counts match real `glob` counts of their directories.

## Regression guard

`pytest tests/tools/test_content_inventory.py -q`
