---
artifact_type: investigation
ticket_id: TCK-20260614-WORLDDAT-COMPOSE
date: 2026-06-15
---

# Investigation: TCK-20260614-WORLDDAT-COMPOSE

## Schema Analysis

`WorldCompositionSpec` (src/worldassembly/schema.py) accepts:
- Required: `schema_version` (must be "worldcomposition.v1"), `world_id`, `name`
- Optional: `description`, `catalog_refs`, `pack_refs`, `module_refs`, `modules` (shorthand), `default_perspectives`, `provided_features`, `global_parameters`, `generation_seed`, `validation_profile`
- `extra="forbid"` — unknown fields cause validation error
- `tags` is NOT valid; `observability_tags` is NOT valid on compositions
- Both `modules` and `module_refs` cannot coexist

`ModuleRefSpec` accepts: `module_id`, `enabled`, `order`, `parameters`, `namespace`

## Module Region Map (collision detection)

| Module | Regions |
|---|---|
| forest_deep_ecology | (none — ecology only) |
| wolf_den_near_forest | near_forest, wolf_den |
| undead_battlefield | haunted_battlefield |
| ruins_mystery_quest | haunted_battlefield |
| frontier_village_core | hometown |
| trading_company_hub | hometown |
| bandit_road_trade_pressure | bandit_road |
| scalable_bandit_camp | bandit_road |
| goblin_camp_conflict | goblin_camp |
| old_mine_resource_loop | old_mine |

**Collision risks:**
- `undead_battlefield` + `ruins_mystery_quest` both use `haunted_battlefield` — CANNOT combine
- `trading_company_hub` + `frontier_village_core` both use `hometown` — CANNOT combine
- `bandit_road_trade_pressure` + `scalable_bandit_camp` both use `bandit_road` — CANNOT combine

## Module requires analysis

Modules with `requires: ["frontier_village_core"]`:
- `wolf_den_near_forest`, `undead_battlefield`, `goblin_camp_conflict`, `old_mine_resource_loop`, `bandit_road_trade_pressure`

The `requires` field is ONLY used for topological ordering (Kahn's sort). Missing `requires` entries in the composition graph are silently skipped. NOT enforced at assembly time.

## Composition Design Decisions

### wilderness_survival
- Uses `forest_deep_ecology` (ecology-only, no regions), `wolf_den_near_forest` (near_forest, wolf_den), `undead_battlefield` (haunted_battlefield)
- No settlement module — `frontier_village_core` intentionally absent
- `wolf_den_near_forest` and `undead_battlefield` have `requires: frontier_village_core` but this is not enforced
- Region IDs: near_forest, wolf_den, haunted_battlefield — NO collisions
- Populations resolve via catalog: wolf_pack_small, undead_battlefield_patrol

### urban_political
- Uses `frontier_village_core` (hometown), `trading_company_hub` (hometown), `bandit_road_trade_pressure` (bandit_road)
- COLLISION: Both `frontier_village_core` and `trading_company_hub` use `hometown` region!
- RESOLUTION: Cannot use both. Use `trading_company_hub` standalone (it provides hometown) + `bandit_road_trade_pressure`
- BUT: `bandit_road_trade_pressure` requires `frontier_village_core` for topological sorting only
- DECISION: Use `frontier_village_core` + `bandit_road_trade_pressure` + `trading_company_hub` triggers hometown collision
- ACTUAL RESOLUTION: Drop `frontier_village_core`, use only `trading_company_hub` (has hometown) + `bandit_road_trade_pressure`
  OR use `frontier_village_core` instead of `trading_company_hub` (both have hometown)
- Ticket explicitly says: `frontier_village_core`, `trading_company_hub`, `bandit_road_trade_pressure`
  The collision means these 3 cannot all be combined without namespace isolation.
- Check if namespace on ModuleRefSpec can isolate: yes, `namespace` prefix isolates region IDs
- Use `namespace: "trading"` on `trading_company_hub` to make its region `trading_hometown` — avoids collision with `hometown`

### dungeon_crawl
- Uses `ruins_mystery_quest` (haunted_battlefield), `goblin_camp_conflict` (goblin_camp), `old_mine_resource_loop` (old_mine), `scalable_bandit_camp` (bandit_road)
- No region collisions
- Quest definitions: ruins_mystery_quest(2) + old_mine_resource_loop(1) = 3 total, ≥ 2 satisfied

## CompileContext faction relationships (urban_political test)

`CompileContext.factions` is populated by `CompileProfileResolver.resolve()` — it registers every faction in `world_spec.factions`. This is sourced from catalog (`CatalogRepository.factions`). All catalog factions get registered regardless of which modules are active.

For `urban_political`, expected factions: `town_council`, `merchant_league`, `bandit_company` (from modules), plus all catalog factions. `len(compile_context.factions) >= 2` is trivially satisfied.

## Quest definitions in AuthoritativeState

`WorldCompiler.compile()` returns `(AuthoritativeState, report_dict)`. The `compiled_quests` list is NOT stored in `AuthoritativeState`. The quests ARE stored in `bundle.world_spec.quest_definitions` (set during resolver.py assembly).

Test assertion: `len(bundle.world_spec.quest_definitions) >= 2` for dungeon_crawl.

## namespace collision resolution for urban_political

Using `namespace: "trading"` on `trading_company_hub` makes its region ID `trading_hometown`. The `bandit_road` from `bandit_road_trade_pressure` — check if relationships reference `hometown` vs prefixed name. The population recipe for merchant_count references `spawn_region: "hometown"` in the module YAML, but with prefix it becomes `trading_hometown`. This is handled by resolver.py line 459: `spawn_region = f"{prefix}{pop.spawn_region}" if pop.spawn_region else ""`.

Faction registrations and relationships resolve from catalog, not from region names — so they remain valid.
