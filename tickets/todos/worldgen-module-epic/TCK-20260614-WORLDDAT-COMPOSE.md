---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDDAT-COMPOSE
phase: open
date: 2026-06-14
tags: [worldmodules, data, compositions, archetypes]
---

# TCK-20260614-WORLDDAT-COMPOSE

## Title
New world archetype compositions demonstrating distinct play patterns

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The 3 existing compositions (`frontier_living_world`, `frontier_extended`, `swamp_border_world`) all follow a similar pattern: settlement core + conflict threat modules. After new modules are available (TCK-20260614-WORLDDAT-NEWMODS), new compositions can demonstrate genuinely different world archetypes — wilderness survival, urban political, and dungeon crawl — and serve as integration test targets for the full pipeline.

## Scope
Write 3 new compositions in `data/content/world_compositions/`:

1. **`wilderness_survival.yaml`** — `schema_version: "worldcomposition.v1"`, no settlement module
   - Modules: `forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield` (or similar danger modules)
   - `provided_features: ["deep_wilderness", "ecology_module", "survival"]`
   - `global_parameters: {topology_width: 256, topology_height: 256}`
   - Uses `module_refs` (structured) form, not shorthand `modules` list
   - High danger, low population

2. **`urban_political.yaml`** — settlement-heavy, faction relationship dense
   - Modules: `frontier_village_core`, `trading_company_hub`, `bandit_road_trade_pressure`
   - `trading_company_hub` ref includes `parameters: {merchant_count: 6}`
   - `provided_features: ["settlement", "trade_hub", "trade_route", "faction_pressure"]`
   - Low danger, high faction relationship density

3. **`dungeon_crawl.yaml`** — quest-dense, danger-heavy, ecology-sparse
   - Modules: `ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`
   - `scalable_bandit_camp` with `parameters: {danger_scale: 4}`
   - `provided_features: ["dungeon", "quest_seeding", "conflict", "faction_pressure"]`
   - No settlement modules; `default_perspectives: ["hero_guild_perspective"]` if catalog supports it

All compositions must use `module_refs` (structured form) to demonstrate parameter injection.

## Out of Scope
- Runtime simulation tuning
- Scenario definitions referencing these compositions (TCK-20260614-WORLDSCEN-PERSPECTIVES)

## Acceptance Criteria
- All 3 compositions load as valid `WorldCompositionSpec`
- All 3 assemble via `WorldAssemblyResolver.assemble()` to a valid `ResolvedWorldBundle`
- All 3 compile via `WorldCompiler.compile()` to a valid `AuthoritativeState`
- `dungeon_crawl` compiled world has at least 2 `QuestDefinition` entries in `quest_definitions`
- `urban_political` compiled world has at least 2 resolved faction relationships in `CompileContext`
- Each composition can run 10 simulation ticks without error (`make sim WORLD=wilderness_survival TICKS=10`)
- `make lane-strict-matrix` passes with the 3 new compositions included

## Related Tickets
- TCK-20260614-WORLDDAT-NEWMODS (prerequisite — new modules must exist)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite — urban_political uses parametric trading_company_hub)
- TCK-20260614-WORLDSCEN-PERSPECTIVES (follows — scenario layer references these)

## Related Code Areas
- `data/content/world_compositions/` — new YAML files
- `tests/integration/worldassembly/test_real_content_world_compositions.py`
- `tests/integration/content/test_strict_world_matrix.py`

## Test Summary
- Extend `test_real_content_world_compositions.py` for each new composition
- Extend `test_strict_world_matrix.py` matrix rows for the 3 new archetypes
- Smoke-test: each compiles + ticks 10 without error

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
