---
ticket_id: TCK-20260619-E13B-MODULE-TYPES
phase: investigation
date: 2026-06-20
---

# Investigation: TCK-20260619-E13B-MODULE-TYPES — New Module Types (Terrain + Population)

## Key Finding: No Code Change Required

`REGISTERED_MODULE_TYPES` in `src/worldmodules/schema.py` (line ~44) already includes
both `"terrain"` and `"population"`. The `validate_module_type` field validator accepts them.
No allowlist expansion needed.

## Schema Constraints (from src/worldmodules/schema.py)

WorldModuleSpec fields that are validated at load time:
- `module_type`: must be in REGISTERED_MODULE_TYPES (already includes terrain/population)
- `regions[].type`: any string accepted (RegionRecipeSpec.type)
- `regions[].terrain`: any string accepted
- `quest_definitions[].type`: Literal["escort","hunt","fetch","explore","defend","investigate"]
- `extra="forbid"` → no unknown top-level keys allowed

## Catalog Reference Constraints (from test_real_world_modules_reference_graph_edges_exist)

The integration test checks populations, resources (keys), buildings (keys), and factions
against the catalog. Biomes and ecologies are NOT validated at test time.

### Valid factions:
arcane_circle, bandit_company, dragon_cult, dwarven_mine_clan, forest_wardens,
goblin_warband, hero_guild, merchant_league, moon_cult, neutral, orc_clan,
spirit_court, swamp_tribe, town_council, undead_remnants, wild_beast_pack

### Valid populations:
bandit_ambush_group, dragon_cult_elite_cell, forest_warden_patrol,
frontier_village_population, goblin_raiding_party, merchant_caravan,
moon_cult_apprentice_circle, old_mine_spider_cluster, orc_clan_warband,
sacred_grove_guardians, swamp_ambush_party, swamp_tribe_patrol,
undead_battlefield_patrol, wolf_pack_small

### Valid resources:
crystal_outcrop, ember_core_cluster, frost_shard_cluster, healing_flower_patch,
herb_patch, iron_vein, moon_resin_tree, silver_vein, spirit_wisp, venom_nest, wood_node

### Valid buildings:
blacksmith, healer_hut, inn, mage_tower, mine_entrance, shop, shrine, town_hall, watchtower

### Valid biomes (for reference only, not test-validated):
bandit_road, frontier_village, frozen_peak, goblin_camp, haunted_battlefield,
moon_cave, near_forest, old_mine, orc_territory, sacred_grove, sunken_swamp,
volcanic_pass, wolf_den

## Module Design Decisions

### mountain_pass.yaml (terrain)
- biome: frozen_peak (existing — mountain/cold theme)
- ecology: none (no cold mountain ecology exists; leave ecologies: [])
- factions: none (neutral terrain per ticket spec)
- populations: none (no mountain pop exists in catalog)
- resources: iron_vein (mining) + frost_shard_cluster (altitude/cold)
- grid_bounds: [80, 80, 120, 120] (per ticket instruction for non-overlap)
- quests: explore_mountain_route (explore), hunt_mountain_predator (hunt)

### river_crossing.yaml (terrain)
- biome: near_forest (closest to river/water without a dedicated river biome)
- ecology: none
- factions: none (neutral terrain, river connection)
- populations: none
- resources: herb_patch (freshwater plants — food proxy; healing_flower_patch also valid)
- buildings: watchtower (monitoring the crossing)
- grid_bounds: [130, 30, 160, 70]
- quests: survey_river_route (explore)

### nomadic_herd.yaml (population)
- biome: none (nomadic — no fixed biome)
- factions: wild_beast_pack (closest neutral/nomadic faction in catalog)
- populations: wolf_pack_small (closest herd-like existing population)
- resources: none (loot drops not modeled in module resources)
- grid_bounds: [60, 130, 100, 170]
- quests: track_nomadic_herd (hunt)

### settled_quarter.yaml (population)
- biome: frontier_village (settlement biome — appropriate)
- factions: merchant_league (per ticket spec)
- populations: frontier_village_population (settlement population)
- resources: none
- buildings: blacksmith, healer_hut, inn, shop (service density per ticket spec)
- grid_bounds: [170, 80, 210, 120]
- quests: fetch_settlement_supplies (fetch), escort_settled_trader (escort)

## Normalizer Behavior

The normalizer (`src/worldmodules/normalizer.py`) converts populations list → population_refs tuple,
biomes → biome_refs, ecologies → ecology_refs. The resolver then maps these to catalog entries.
The test only validates factions/populations/resources/buildings against the catalog.
