---
artifact_type: plan
ticket_id: TCK-20260614-WORLDDAT-COMPOSE
date: 2026-06-15
---

# Plan: TCK-20260614-WORLDDAT-COMPOSE

## Files to Create

1. `data/content/world_compositions/wilderness_survival.yaml`
2. `data/content/world_compositions/urban_political.yaml`
3. `data/content/world_compositions/dungeon_crawl.yaml`

## Files to Modify

4. `tests/integration/worldassembly/test_real_content_world_compositions.py` — add 3 new test functions

## Composition Designs

### wilderness_survival
- module_refs: forest_deep_ecology (order 0), wolf_den_near_forest (order 1), undead_battlefield (order 2)
- provided_features: deep_wilderness, ecology_module, survival
- global_parameters: topology_width: 256, topology_height: 256
- No region collisions — ecology-only + distinct wilderness regions

### urban_political
- module_refs: frontier_village_core (order 0), trading_company_hub with namespace "trading" (order 1), bandit_road_trade_pressure (order 2)
- trading_company_hub uses namespace to avoid hometown collision with frontier_village_core
- parameters: merchant_count: 6 on trading_company_hub
- provided_features: settlement, trade_hub, trade_route, faction_pressure

### dungeon_crawl
- module_refs: ruins_mystery_quest (order 0), goblin_camp_conflict (order 1), old_mine_resource_loop (order 2), scalable_bandit_camp (order 3)
- scalable_bandit_camp parameters: danger_scale: 4
- provided_features: dungeon, quest_seeding, conflict, faction_pressure
- default_perspectives: hero_guild_perspective

## Test Strategy

Three parametrized-style test functions (not using @pytest.mark.parametrize to allow targeted assertions per composition):

1. `test_wilderness_survival_composition` — load + assemble
2. `test_urban_political_composition` — load + assemble, assert compile_context.factions >= 2
3. `test_dungeon_crawl_composition` — load + assemble, assert world_spec.quest_definitions >= 2

WorldCompiler.compile() is called as `WorldCompiler.compile(bundle.world_spec, 42, context=bundle.compile_context)`.
Returns `(state, report)` tuple — unpack accordingly.
