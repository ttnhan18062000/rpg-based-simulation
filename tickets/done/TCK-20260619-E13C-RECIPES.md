---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13C-RECIPES
phase: done
date: 2026-06-20
tags: [content, crafting-recipes, economy, phase-1]
---

# TCK-20260619-E13C-RECIPES

## Title
Epic 1.3C · Crafting Recipe Expansion

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
D07 F3: 8 crafting recipes for 34 items (Gap Risk 10/15). Most items have no production path. No gather→craft→upgrade chain exists. This ticket expands recipes from 8 to 25+ and authors the first complete gather→craft→upgrade chain.

## Scope

Expand `data/content/world/recipes.yaml` from 8 to 25+ entries.

### Required: Complete gather→craft chain (E13 acceptance criterion)

Chain 1 — Metal progression:
```
iron_ore (gather) → [refine] steel (craft: smelt_iron_to_steel, blacksmith, cost 20)
steel + ember_core → ember_axe (craft: craft_ember_axe, blacksmith, cost 55)
```
Note: `steel` is already a catalog item. Confirmed from `data/content/world/items.yaml`.

Chain 2 — Alchemy progression:
```
herb + healing_flower (gather) → travel_ration (craft: craft_travel_ration, healer, cost 15)
healing_flower×2 + herb → small_potion×2 (craft: craft_healer_bundle, healer, cost 20)
moon_resin + herb×2 → small_potion×2 (craft: craft_moon_elixir, healer, cost 25)
```

### Recipe coverage targets (fill uncovered item categories)

**Weapons (currently missing recipes):**
- `craft_wooden_staff`: wood×2 → wooden_staff (blacksmith, cost 15)
- `craft_basic_bow`: wood×2 + beast_fang → basic_bow (blacksmith, cost 20)
- `craft_apprentice_staff`: wood + crystal_shard → apprentice_staff (arcane, cost 35)
- `craft_frost_focus`: frost_shard×2 + crystal_shard → frost_focus (arcane, cost 65)
- `craft_ember_axe`: steel + ember_core → ember_axe (blacksmith, cost 55)

**Armor/protection:**
- `craft_leather_armor`: wolf_pelt×2 + wood → leather_armor (blacksmith, cost 30)
- `craft_repair_kit`: iron_ore + wood → repair_kit (blacksmith, cost 25)

**Consumables:**
- `craft_travel_ration`: herb + healing_flower → travel_ration (healer, cost 15)
- `craft_healer_bundle`: healing_flower×2 + herb → small_potion×2 (healer, cost 20)
- `craft_moon_elixir`: moon_resin + herb×2 → small_potion×2 (healer, cost 25)

**Materials/refined:**
- `smelt_iron_to_steel`: iron_ore×3 → steel (blacksmith, cost 20) — key chain step

**Faction drops → useful items:**
- `craft_from_goblin_tokens`: goblin_token×3 → small_potion (general_store_service, cost 5)
- `trade_beast_fangs`: beast_fang×2 → travel_ration×2 (general_store_service, cost 0)

**Arcane:**
- `craft_spirit_ward`: spirit_essence + moon_resin → warding_charm (arcane, cost 40)
- `craft_ancient_blade`: ancient_fragment×2 + iron_ore → silvered_blade (arcane, cost 70)

**Iron utility:**
- `smelt_rusted_sword`: rusted_sword + iron_ore → iron_sword (blacksmith, cost 15)
- `process_shadow_ichor`: shadow_ichor + herb → warding_charm (healer, cost 30)

## Out of Scope
- New item definitions (use existing 34 items only — do not add items)
- Dynamic recipe discovery
- Recipe failure/success rates

## Acceptance Criteria
- `data/content/world/recipes.yaml` has ≥ 25 entries ✓ (exactly 25)
- At least one complete gather→craft chain: raw material (iron_ore) → intermediate (steel) → final item (ember_axe) ✓
- `python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"` passes ✓
- `tests/unit/content/test_recipe_catalog_expansion.py` — 12 tests pass ✓

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (parent epic)
- TCK-20260619-E13B-MODULE-TYPES (settled_quarter module adds blacksmith_service — enabling recipes)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (crafting laws reference)
- `docs/parity_ledger/town_resource.yaml` (TOWN-172 added)
- `docs/audits/D07_content_depth.md` (F3 count resolved — 25 recipes)

## Related Code Areas
- `data/content/world/recipes.yaml` (expanded from 8 to 25)
- `data/content/world/services.yaml` (provided_recipes updated for all 4 service types)
- `src/content/repository.py` (`CatalogRepository.load_all()`)
- `tests/unit/content/test_recipe_catalog_expansion.py` (new)

## Assumptions / Open Questions
- `large_potion` not in items.yaml → skipped, used small_potion×2 output instead
- `tanned_hide` not in items.yaml → wolf pelt refinement chain skipped
- `merchant_service` does not exist → used `general_store_service` for loot-conversion recipes
- Recipe engine supports multi-step chains implicitly (each recipe maps independently)

## Implementation Notes
- Each recipe references only existing item IDs from `data/content/world/items.yaml` (verified)
- All new entries marked `# STATE: ADDITIONAL`
- services.yaml `provided_recipes` updated for blacksmith_service, healer_service, arcane_service, general_store_service
- No engine code changes required — pure content data expansion

## Test Summary
12 tests in `tests/unit/content/test_recipe_catalog_expansion.py` — all pass:
- test_recipe_count_at_least_25
- test_gather_craft_chain_iron_to_steel
- test_gather_craft_chain_steel_to_ember_axe
- test_full_gather_craft_chain_connected
- test_all_recipe_ingredients_are_valid_items
- test_all_recipe_outputs_are_valid_items
- test_all_recipe_services_exist
- test_service_coverage_all_types
- test_no_duplicate_recipe_ids
- test_all_recipes_have_required_fields
- test_craft_small_potion_is_preserved
- test_catalog_repository_loads

## Files Changed
- `data/content/world/recipes.yaml` — expanded from 8 to 25 entries (+17 new)
- `data/content/world/services.yaml` — added `provided_recipes` to general_store_service; expanded lists for blacksmith_service, healer_service, arcane_service
- `tests/unit/content/test_recipe_catalog_expansion.py` — new (12 tests)
- `docs/parity_ledger/town_resource.yaml` — added TOWN-172

## Completion Summary
Expanded `data/content/world/recipes.yaml` from 8 to 25 entries covering all 4 service types (blacksmith, healer, arcane, general_store). Implemented the key metal progression chain: `iron_ore×3 → steel` (smelt_iron_to_steel) → `steel + ember_core → ember_axe` (craft_ember_axe). Added alchemy chain (herb/healing_flower → consumables), weapon coverage (wooden_staff, basic_bow, apprentice_staff, frost_focus), armor (leather_armor), tools (repair_kit), loot-conversion (goblin_token→potion, beast_fang→ration), and advanced arcane recipes. All 25 recipes verified against items.yaml (no unknown IDs). services.yaml updated with full provided_recipes lists. Parity ledger entry TOWN-172 added. 12 unit tests pass.
