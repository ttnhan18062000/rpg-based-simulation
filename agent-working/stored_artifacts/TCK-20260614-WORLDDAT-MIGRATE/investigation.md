# Investigation: TCK-20260614-WORLDDAT-MIGRATE

## All 10 Module Files — Current Fields

| Module | module_type | schema_version | relationships | biomes | ecologies | quest_definitions | notes |
|---|---|---|---|---|---|---|---|
| frontier_village_core | settlement | worldmodule.v1 | (none) | ["frontier_village"] | ["frontier_village_ecology"] | (none) | Has factions: town_council, merchant_league |
| goblin_camp_conflict | conflict | worldmodule.v1 | ["town_to_goblin_warband","goblin_warband_to_town"] | ["goblin_camp"] | ["goblin_camp_ecology"] | (none) | Already has valid relationship IDs |
| old_mine_resource_loop | economy | worldmodule.v1 | (none) | ["old_mine"] | ["old_mine_resource_ecology"] | (none) | Factions: dwarven_mine_clan, wild_beast_pack |
| wolf_den_near_forest | ecology | worldmodule.v1 | ["town_to_wild_beasts","wild_beasts_to_town"] | ["near_forest","wolf_den"] | ["wolf_den_ecology"] | (none) | Already has valid biome IDs and relationships |
| bandit_road_trade_pressure | conflict | worldmodule.v1 | ["town_to_bandits","bandits_to_merchants"] | ["bandit_road"] | ["bandit_road_ecology"] | (none) | Already has valid relationships |
| forest_warden_grove | ecology | worldmodule.v1 | ["forest_wardens_to_wild_beasts"] | ["sacred_grove"] | ["sacred_grove_ecology"] | (none) | Already has valid relationship |
| moon_cult_ruins | conflict | worldmodule.v1 | ["moon_cult_to_town"] | ["moon_cave"] | (none) | (none) | No ecologies field |
| orc_clan_territory | conflict | worldmodule.v1 | ["town_to_orc_clan","orc_clan_to_town"] | ["orc_territory"] | ["orc_territory_ecology"] | (none) | Already has valid relationships |
| sunken_swamp_border | conflict | worldmodule.v1 | [] | ["sunken_swamp"] | [] | (none) | Empty relationships and ecologies |
| undead_battlefield | danger_zone | worldmodule.v1 | ["undead_to_living"] | ["haunted_battlefield"] | ["haunted_battlefield_ecology"] | (none) | Already has valid relationship |

## Catalog Relationship IDs That Actually Exist

From `data/content/social/faction_relationships.yaml`:
- `town_to_wild_beasts`
- `wild_beasts_to_town`
- `town_to_goblin_warband`
- `goblin_warband_to_town`
- `town_to_merchants`
- `merchants_to_town`
- `town_to_bandits`
- `bandits_to_merchants`
- `forest_wardens_to_wild_beasts`
- `dwarves_to_goblins`
- `moon_cult_to_town`
- `town_to_orc_clan`
- `orc_clan_to_town`
- `undead_to_living`

No catalog entry for: `merchant_league_to_town_council` (ticket mentions this as candidate — ABSENT, do not use)

## Catalog Biome IDs That Actually Exist

From `data/content/world/biomes.yaml`:
`frontier_village`, `near_forest`, `wolf_den`, `old_mine`, `goblin_camp`, `moon_cave`, `bandit_road`, `haunted_battlefield`, `sacred_grove`, `volcanic_pass`, `orc_territory`, `frozen_peak`, `sunken_swamp`

No `forest_edge` biome (ticket mentions this as candidate — ABSENT, do not use)

## Schema Constraints

- `WorldModuleSpec` has `extra="forbid"` — adding unknown fields like `provided_features` would cause load failures
- `schema_version` is `Optional[str]` — can remain or be removed
- `observability_tags` is the correct audit tag field (not `provided_features` or `tags`)
- `quest_definitions` uses `QuestDefinition` Pydantic model with fields: `id`, `type`, `required_participant_tags`, `required_location_tags`, `reward_budget`, `procedural_hints`, `tags`, `source_module`

## Migration Plan Per Module

1. **frontier_village_core** — Remove `schema_version`, add `relationships: ["town_to_merchants", "merchants_to_town"]`, add `observability_tags: ["settlement", "trade"]`
2. **goblin_camp_conflict** — Remove `schema_version`, already has valid relationships, add `observability_tags: ["conflict", "faction_pressure"]`
3. **old_mine_resource_loop** — Remove `schema_version`, add `relationships: ["dwarves_to_goblins"]`, add `quest_definitions` (fetch type), add `observability_tags: ["resource", "economy"]`
4. **wolf_den_near_forest** — Remove `schema_version`, already has valid biomes and relationships, add `observability_tags: ["ecology", "wilderness"]`
5. **bandit_road_trade_pressure** — Remove `schema_version`, add `observability_tags: ["conflict"]`
6. **forest_warden_grove** — Remove `schema_version`, add `observability_tags: ["ecology"]`
7. **moon_cult_ruins** — Remove `schema_version`, add `observability_tags: ["conflict"]`, add missing `ecologies` field
8. **orc_clan_territory** — Remove `schema_version`, add `observability_tags: ["conflict"]`
9. **sunken_swamp_border** — Remove `schema_version`, add `observability_tags: ["conflict"]` (no suitable relationship in catalog)
10. **undead_battlefield** — Remove `schema_version`, add `observability_tags: ["conflict", "danger_zone"]`

## Pre-existing Test Failures (not caused by this ticket)

`test_strict_world_matrix.py` has 15 pre-existing failures (duplicate resource ID collision) for `+ moon_cult`, `+ orc_clan`, `+ forest_warden` rows. These are assembly resolver bugs unrelated to YAML migration.
