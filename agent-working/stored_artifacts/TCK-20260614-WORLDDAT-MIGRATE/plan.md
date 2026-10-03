# Plan: TCK-20260614-WORLDDAT-MIGRATE

## Objective

Migrate all 10 world module YAML files to the unified schema:
- Remove legacy `schema_version: "worldmodule.v1"` field from all 10 files
- Enrich at least 4 modules with new fields (relationships, quest_definitions, observability_tags)
- Use ONLY catalog IDs that actually exist in the catalog files
- Do NOT add `provided_features` (not a valid WorldModuleSpec field — schema uses `observability_tags`)
- Do NOT change any numeric values

## Per-Module Changes

### Priority Modules (high enrichment)

1. **frontier_village_core.yaml**
   - Remove `schema_version`
   - Add `relationships: ["town_to_merchants", "merchants_to_town"]` (catalog-verified IDs)
   - Add `observability_tags: ["settlement", "trade"]`

2. **goblin_camp_conflict.yaml**
   - Remove `schema_version`
   - Already has correct relationship IDs
   - Add `observability_tags: ["conflict", "faction_pressure"]`

3. **old_mine_resource_loop.yaml**
   - Remove `schema_version`
   - Add `relationships: ["dwarves_to_goblins"]` (catalog-verified)
   - Add `quest_definitions` entry (fetch type for ore retrieval)
   - Add `observability_tags: ["resource", "economy"]`

4. **wolf_den_near_forest.yaml**
   - Remove `schema_version`
   - Already has correct biome IDs and relationship IDs
   - Add `observability_tags: ["ecology", "wilderness"]`

### Remaining 6 Modules (schema_version removal + observability_tags)

5. **bandit_road_trade_pressure.yaml** — Remove `schema_version`, add `observability_tags: ["conflict"]`
6. **forest_warden_grove.yaml** — Remove `schema_version`, add `observability_tags: ["ecology"]`
7. **moon_cult_ruins.yaml** — Remove `schema_version`, add `observability_tags: ["conflict"]`
8. **orc_clan_territory.yaml** — Remove `schema_version`, add `observability_tags: ["conflict"]`
9. **sunken_swamp_border.yaml** — Remove `schema_version`, add `observability_tags: ["conflict"]`
10. **undead_battlefield.yaml** — Remove `schema_version`, add `observability_tags: ["conflict", "danger_zone"]`

## Verification

- `tests/integration/worldassembly/test_real_content_world_modules.py` — 5 tests must still pass
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — must still pass
- `tests/integration/content/test_strict_world_matrix.py` — pre-existing failures remain (not caused by this ticket)
