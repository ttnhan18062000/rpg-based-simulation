---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13C-RECIPES
artifact_type: plan
tags: [content, crafting-recipes, economy]
---

# Plan: TCK-20260619-E13C-RECIPES — Crafting Recipe Expansion

## Goal
Expand `data/content/world/recipes.yaml` from 8 to 25 entries.
Author the first complete gather→craft→upgrade chain (iron_ore → steel → ember_axe).

## Constraints
- Only existing item IDs from items.yaml (34 items, verified)
- Only existing service IDs from services.yaml
- No new item definitions
- No engine changes
- Mark all new entries `# STATE: ADDITIONAL`

## Confirmed Item IDs Available for Recipes
Materials (gatherable): iron_ore, wood, herb, healing_flower, wolf_pelt, beast_fang,
moon_resin, crystal_shard, ancient_fragment, goblin_token, silver_ore, spirit_essence,
venom_sac, ember_core, frost_shard, shadow_ichor

Craftable outputs (items): wooden_staff, basic_bow, leather_armor, repair_kit,
travel_ration, apprentice_staff, frost_focus, ember_axe, steel, small_potion,
iron_sword, iron_shield, warding_charm, silvered_blade, venom_dagger, spirit_lantern,
rusted_sword, hunter_blade

## Confirmed Service IDs
- blacksmith_service
- healer_service
- arcane_service
- general_store_service

## 25 Final Recipes (8 existing + 17 new)

### Existing (8) — unchanged
1. craft_iron_sword (LEGACY-EXPORT)
2. craft_hunter_blade (LEGACY-EXPORT)
3. craft_small_potion (LEGACY-EXPORT)
4. craft_iron_shield (ADDITIONAL)
5. craft_silvered_blade (ADDITIONAL)
6. craft_warding_charm (ADDITIONAL)
7. craft_venom_dagger (ADDITIONAL)
8. craft_spirit_lantern (ADDITIONAL)

### New (17) — all ADDITIONAL

**Metal chain (AC required):**
9.  smelt_iron_to_steel: iron_ore×3 → steel (blacksmith_service, cost 20)
10. craft_ember_axe: steel×1 + ember_core×1 → ember_axe (blacksmith_service, cost 55)

**Weapons:**
11. craft_wooden_staff: wood×2 → wooden_staff (blacksmith_service, cost 15)
12. craft_basic_bow: wood×2 + beast_fang×1 → basic_bow (blacksmith_service, cost 20)
13. craft_apprentice_staff: wood×1 + crystal_shard×1 → apprentice_staff (arcane_service, cost 35)
14. craft_frost_focus: frost_shard×2 + crystal_shard×1 → frost_focus (arcane_service, cost 65)

**Armor/tools:**
15. craft_leather_armor: wolf_pelt×2 + wood×1 → leather_armor (blacksmith_service, cost 30)
16. craft_repair_kit: iron_ore×1 + wood×1 → repair_kit (blacksmith_service, cost 25)

**Consumables:**
17. craft_travel_ration: herb×1 + healing_flower×1 → travel_ration (healer_service, cost 15)
18. craft_healer_bundle: healing_flower×2 + herb×1 → small_potion×2 (healer_service, cost 20)

**Material/alchemy:**
19. craft_moon_elixir: moon_resin×1 + herb×2 → small_potion×2 (healer_service, cost 25)
20. process_shadow_ichor: shadow_ichor×1 + herb×1 → warding_charm×1 (healer_service, cost 30)

**Faction/loot conversion:**
21. craft_from_goblin_tokens: goblin_token×3 → small_potion×1 (general_store_service, cost 5)
22. trade_beast_fangs: beast_fang×2 → travel_ration×2 (general_store_service, cost 0)

**Advanced arcane:**
23. craft_spirit_ward: spirit_essence×1 + moon_resin×1 → warding_charm×1 (arcane_service, cost 40)
24. craft_ancient_blade: ancient_fragment×2 + iron_ore×1 → silvered_blade×1 (arcane_service, cost 70)

**Iron utility:**
25. smelt_rusted_sword: rusted_sword×1 + iron_ore×1 → iron_sword×1 (blacksmith_service, cost 15)

Total: 25 recipes

## Implementation Steps

### Step 1: Expand data/content/world/recipes.yaml
Add 17 new recipe entries (items 9-25 above), each marked `# STATE: ADDITIONAL`.
File: `data/content/world/recipes.yaml`

### Step 2: Update data/content/world/services.yaml
Add new recipe IDs to `provided_recipes` lists where applicable:
- blacksmith_service: add smelt_iron_to_steel, craft_ember_axe, craft_wooden_staff,
  craft_basic_bow, craft_leather_armor, craft_repair_kit, smelt_rusted_sword
- arcane_service: add craft_apprentice_staff, craft_frost_focus, craft_spirit_ward, craft_ancient_blade
- healer_service: add craft_travel_ration, craft_healer_bundle, craft_moon_elixir, process_shadow_ichor
- general_store_service: add provided_recipes field with craft_from_goblin_tokens, trade_beast_fangs
File: `data/content/world/services.yaml`

### Step 3: Write unit tests
New file: `tests/unit/content/test_recipe_catalog_expansion.py`
Tests: count, chain validation, ingredient/output/service integrity.

### Step 4: Verify catalog loads
Run: `python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"`

### Step 5: Run scoped tests
`pytest tests/unit/content/test_recipe_catalog_expansion.py -v`

## Acceptance Criteria Map
- AC1 (≥25 entries): Steps 1+3
- AC2 (gather→craft chain): Step 1 recipes 9+10
- AC3 (CatalogRepository loads): Step 4
- AC4 (test passes): Step 5

## Deviations
_None anticipated._

## Scope Guards
- Do NOT add new item IDs
- Do NOT modify src/ files (no engine changes)
- Do NOT change LEGACY-EXPORT recipes
