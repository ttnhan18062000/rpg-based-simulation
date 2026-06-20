---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13C-RECIPES
artifact_type: investigation
tags: [content, crafting-recipes, economy]
---

# Investigation: TCK-20260619-E13C-RECIPES — Crafting Recipe Expansion

## Current State

`data/content/world/recipes.yaml` has **8 entries**:
- 3 LEGACY-EXPORT: `craft_iron_sword`, `craft_hunter_blade`, `craft_small_potion`
- 5 ADDITIONAL: `craft_iron_shield`, `craft_silvered_blade`, `craft_warding_charm`, `craft_venom_dagger`, `craft_spirit_lantern`

## Item Catalog (data/content/world/items.yaml) — 34 items confirmed

### LEGACY-EXPORT items (19):
rusted_sword, wooden_staff, basic_bow, leather_armor, iron_sword, hunter_blade,
apprentice_staff, small_potion, travel_ration, repair_kit, wood, herb, iron_ore,
beast_fang, wolf_pelt, moon_resin, crystal_shard, goblin_token, ancient_fragment, healing_flower

### ADDITIONAL items (15):
iron_shield, silvered_blade, warding_charm, ember_axe, frost_focus, venom_dagger,
spirit_lantern, steel, silver_ore, spirit_essence, venom_sac, ember_core, frost_shard, shadow_ichor

**Total: 34 items (19+15=34 confirmed)**

## Key Findings

### Items confirmed present — safe to use as recipe outputs
- `steel` — yes (ADDITIONAL material)
- `ember_axe` — yes (ADDITIONAL weapon/fire)
- `frost_focus` — yes (ADDITIONAL trinket/ice)
- `wooden_staff` — yes (LEGACY weapon/magic)
- `basic_bow` — yes (LEGACY weapon/ranged)
- `apprentice_staff` — yes (LEGACY weapon/magic)
- `leather_armor` — yes (LEGACY armor)
- `repair_kit` — yes (LEGACY tool)
- `travel_ration` — yes (LEGACY consumable)
- `shadow_ichor` — yes (ADDITIONAL material/arcane)
- `goblin_token` — yes (LEGACY material/trophy)

### Items NOT in catalog — cannot be used
- `large_potion` — NOT in items.yaml → skip recipe for it
- `tanned_hide` — NOT in items.yaml → skip wolf_pelt refinement chain
- `enhanced_ember_axe` — NOT in items.yaml → skip upgrade step

### Services available (from services.yaml)
- `blacksmith_service` (crafting)
- `healer_service` (healing)
- `arcane_service` (magic)
- `general_store_service` (trade)
- `inn_service`, `guard_post_service`, `mining_service`, `shrine_service`

No `merchant_service` exists → use `general_store_service` for loot-conversion recipes

### gather→craft chain
Chain 1 — Metal progression:
- iron_ore (gatherable resource) → `smelt_iron_to_steel` → steel (blacksmith, 3×iron_ore, cost 20)
- steel + ember_core → `craft_ember_axe` → ember_axe (blacksmith, cost 55)
- Full chain: gather iron_ore → smelt_iron_to_steel → craft_ember_axe

Chain 2 — Alchemy progression:
- herb + healing_flower → `craft_travel_ration` (healer, cost 15) — travel_ration already exists
- herb + crystal_shard → already covered by existing `craft_small_potion` (blacksmith — legacy quirk, preserved)

### Recipe schema (from src/content/schema.py RecipeDefinition)
```
ingredients: Dict[str, int]   # required
required_service: Optional[str]
gold_cost: float (default 0.0)
outputs: Dict[str, int]       # required
required_level: int (default 1)
```

### No `large_potion` or `merchant_service` — adjust plan
- craft_large_potion → skip (item missing)
- craft_from_goblin_tokens → use `general_store_service` instead of `merchant_service`

## Architecture Assessment

- `RecipeDefinition` lives in `src/content/schema.py` (line 299)
- `CatalogRepository.load_all()` in `src/content/repository.py` loads recipes from `data/content/world/recipes.yaml`
- No runtime engine changes needed — this is pure content data expansion
- Each recipe maps independently; chain is implicit (iron_ore→steel→ember_axe)
- `services.yaml` `provided_recipes` list references recipe IDs — update blacksmith_service, arcane_service entries to include new recipes
- All ingredients must be existing item IDs from items.yaml (verified)

## Gap Analysis: Planned 25 recipes

Current 8 + 17 new = 25 total. New recipes:

| Recipe ID | Output | Service | Notes |
|---|---|---|---|
| smelt_iron_to_steel | steel | blacksmith_service | KEY CHAIN STEP |
| craft_ember_axe | ember_axe | blacksmith_service | Chain terminal |
| craft_wooden_staff | wooden_staff | blacksmith_service | Weapon coverage |
| craft_basic_bow | basic_bow | blacksmith_service | Weapon coverage |
| craft_apprentice_staff | apprentice_staff | arcane_service | Arcane weapon |
| craft_frost_focus | frost_focus | arcane_service | Arcane trinket |
| craft_leather_armor | leather_armor | blacksmith_service | Armor coverage |
| craft_repair_kit | repair_kit | blacksmith_service | Tool coverage |
| craft_travel_ration | travel_ration | healer_service | Consumable |
| craft_large_healer_potion | small_potion×2 | healer_service | Use small_potion output |
| craft_from_goblin_tokens | small_potion | general_store_service | Loot conversion |
| process_shadow_ichor | warding_charm | healer_service | Material→charm |
| craft_moon_charm | warding_charm | arcane_service | Alternative path |
| craft_iron_spike | repair_kit | blacksmith_service | Iron utility |
| craft_herb_bundle | travel_ration×2 | healer_service | Bulk consumable |
| craft_beast_trophy | goblin_token×3 | general_store_service | Trophy combine |
| craft_rusted_restore | iron_sword | blacksmith_service | Rusted→iron path |

Wait — `small_potion×2` output: outputs dict maps item_id → count, so `{small_potion: 2}` is valid.
craft_large_healer_potion → outputs {small_potion: 2} (since large_potion missing)

Recount and trim to exactly 25 confirmed valid recipes. Final list in plan.md.
