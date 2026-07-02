---
ticket_id: TCK-20260619-E13-CONTENT-FOUNDATION
phase: investigation
date: 2026-06-20
---

# Investigation: Content Foundation Layer

## Current Content Snapshot (D07 audit + direct count)

| Category | Count | Gap Risk |
|---|---|---|
| Quest definitions | 4 | 15/15 — critical |
| Terrain module types | 0 | 10/15 |
| Population module types | 0 | 10/15 |
| Crafting recipes | 8 (for 34 items) | 10/15 |
| Scenarios | 8 (all frontier) | 9/15 |

## Quest Definition Schema (TCK-20260614-WORLDMOD-QUEST-SCHEMA — DONE)

Fields: `id`, `type` (escort/hunt/fetch/explore/defend/investigate), `required_participant_tags`,
`required_location_tags`, `reward_budget`, `procedural_hints` (dict), `tags`.

Quest definitions live inside world module YAML under `quest_definitions:` key.
Currently only 3 modules have any: ruins_mystery_quest (2), old_mine_resource_loop (1), forest_deep_ecology (1) = 4 total.

**No extension needed** — `expiry_ticks` and `faction_association` are NOT in the schema (and not required per E13 implementation notes).

## Modules with 0 Quest Definitions (priority targets for E13A)

| Module | Type | Factions |
|---|---|---|
| goblin_camp_conflict | conflict | goblin_raiders, frontier_guild |
| bandit_road_trade_pressure | conflict | bandit_syndicate, merchant_league |
| orc_clan_territory | conflict | orc_clans, frontier_guild |
| scalable_bandit_camp | conflict | bandit_syndicate |
| moon_cult_ruins | danger_zone | moon_cult, spirit_court |
| wolf_den_near_forest | ecology | wolves (no faction) |
| forest_warden_grove | settlement | forest_wardens, spirit_court |
| undead_battlefield | ecology | undead_remnants |
| frontier_village_core | settlement | frontier_guild, merchants |
| trading_company_hub | economy | merchant_league |

## Recipe Schema (data/content/world/recipes.yaml)

Fields: `id`, `outputs` (dict), `ingredients` (dict), `required_service`, `gold_cost`.

8 recipes: blacksmith (5), healer (1), arcane (1), legacy blacksmith for potion (1).
Items with NO recipe: rusted_sword, basic_bow, leather_armor, apprentice_staff, ember_axe,
ember_core, frost_focus, frost_shard, steel, herb, travel_ration, repair_kit, wolf_pelt,
goblin_token, shadow_ichor + all upgraded variants.

**No gather→craft→upgrade chain exists.** Iron_ore appears as an ingredient but has no refining step.
Target gather→craft chain for E13C: iron_ore→steel (refine) + wood→plank (refine) as intermediate materials.

## Module Type Validator

Must verify CatalogValidator in `src/content/validator.py` accepts `terrain` and `population`
module types before authoring E13B modules. If hardcoded allowlist exists, add these types.

## World Compositions Needing Scenarios

| World | Modules | Scenarios (current) |
|---|---|---|
| dungeon_crawl | ruins_mystery_quest, goblin_camp_conflict, old_mine_resource_loop, scalable_bandit_camp | 0 |
| urban_political | frontier_village_core, trading_company_hub, bandit_road_trade_pressure | 0 |
| wilderness_survival | forest_deep_ecology, wolf_den_near_forest, undead_battlefield | 0 |

Need ≥2 per composition = 6 new scenarios minimum.

## Scenario Schema

Fields: `id`, `world_composition`, `focus_modules`, `perspective`, `initial_conditions`.
All in `data/content/simulation_scenarios/frontier_scenarios.yaml` — new file for E13D.
