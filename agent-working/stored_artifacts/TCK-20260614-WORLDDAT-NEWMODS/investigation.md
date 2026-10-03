---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDDAT-NEWMODS
artifact_type: investigation
tags: [worldmodules, data, content, new-modules]
---

# Investigation — TCK-20260614-WORLDDAT-NEWMODS

## Catalog IDs Confirmed Available

### Biomes (data/content/world/biomes.yaml)
- `frontier_village`, `near_forest`, `wolf_den`, `old_mine`, `goblin_camp`, `moon_cave`
- `bandit_road`, `haunted_battlefield`, `sacred_grove`, `volcanic_pass`, `orc_territory`
- `frozen_peak`, `sunken_swamp`

### Ecologies (data/content/world/ecologies.yaml)
- `wolf_den_ecology`, `frontier_village_ecology`, `goblin_camp_ecology`
- `old_mine_resource_ecology`, `bandit_road_ecology`, `haunted_battlefield_ecology`
- `dragon_cult_volcanic_ecology`, `orc_territory_ecology`, `sacred_grove_ecology`

### Populations (data/content/entities/populations.yaml)
- `wolf_pack_small`, `frontier_village_population`, `goblin_raiding_party`
- `merchant_caravan`, `forest_warden_patrol`, `bandit_ambush_group`
- `old_mine_spider_cluster`, `undead_battlefield_patrol`, `orc_clan_warband`
- `sacred_grove_guardians`, `moon_cult_apprentice_circle`, `swamp_tribe_patrol`
- `swamp_ambush_party`, `dragon_cult_elite_cell`

### Entity Archetypes (data/content/entities/entity_archetypes.yaml)
- `hungry_wolf`, `alpha_wolf`, `goblin_scout`, `goblin_raider`, `goblin_archer`, `goblin_warlord`
- `village_worker`, `frontier_guard`, `traveling_merchant`, `village_blacksmith`, `apprentice_mage`
- `forest_ranger`, `cave_spider`, `bandit_scout`, `orc_brute`, `undead_sentinel`
- `spirit_guardian`, `dragon_cult_champion`, `lizardfolk_scout`, `lizardfolk_shaman`, `swamp_troll`

### Faction Relationships (data/content/social/faction_relationships.yaml)
- `town_to_wild_beasts`, `wild_beasts_to_town`
- `town_to_goblin_warband`, `goblin_warband_to_town`
- `town_to_merchants`, `merchants_to_town`
- `town_to_bandits`, `bandits_to_merchants`
- `forest_wardens_to_wild_beasts`
- `dwarves_to_goblins`
- `moon_cult_to_town`
- `town_to_orc_clan`, `orc_clan_to_town`
- `undead_to_living`

### Buildings (data/content/world/buildings.yaml)
- `shop`, `town_hall`, `blacksmith`, `inn`, `watchtower`, `healer_hut`, `mine_entrance`, `shrine`, `mage_tower`

### QuestDefinition Types (src/worldbuilding/schema.py Literal)
- `escort`, `hunt`, `fetch`, `explore`, `defend`, `investigate`

## Key Schema Findings

### WorldModuleSpec (src/worldmodules/schema.py)
- `extra="forbid"` — strictly no unknown fields
- Tag field is `observability_tags: List[str]` (NOT `tags`)
- Provides field is `provides: List[str]` (NOT `provided_features`)
- `quest_definitions: List[QuestDefinition]` — valid, added by WORLDMOD-QUEST-MOD
- `parameters: List[ModuleParameterSpec]` — valid, added by WORLDMOD-PARAMS
- `population_recipes: List[PopulationRecipeSpec]` — uses role/count/faction/spawn_region
- `populations: List[str]` — catalog population IDs (used by existing modules)

### RegionRecipeSpec (src/worldbuilding/recipe.py)
- `hazard_level: Optional[float]` — accepts ONLY float, NOT string expressions
- String expressions only valid on `count` fields (PopulationRecipeSpec, ResourceRecipeSpec, BuildingRecipeSpec)
- For `scalable_bandit_camp`, use fixed float for hazard_level, string expression only for population count

## Design Decisions

### forest_deep_ecology
- Uses `biomes: ["near_forest", "sacred_grove"]` and `ecologies: ["wolf_den_ecology", "sacred_grove_ecology"]`
- No recipe fields — ecology-first design
- Single quest of type `explore`

### ruins_mystery_quest
- Uses catalog populations: `undead_battlefield_patrol` (undead ruins fit)
- 2 quest_definitions of type `investigate`
- Standalone (no requires)
- Biome: `haunted_battlefield` (ruins/ruin terrain fits)

### trading_company_hub
- Uses population_recipes with `count: "{merchant_count}"`
- building_recipes for trading post
- relationships: `["town_to_merchants", "merchants_to_town"]`

### scalable_bandit_camp
- parameters: `danger_scale`, type integer, default 2, min 1, max 5
- population_recipes with `count: "{danger_scale} * 3"`
- hazard_level: fixed `2.0` (float — NOT a string expression)
- Uses catalog archetype: `bandit_scout` (confirmed in entity_archetypes.yaml)
