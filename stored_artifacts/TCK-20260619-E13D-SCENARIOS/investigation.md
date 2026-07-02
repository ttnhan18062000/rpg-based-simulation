---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13D-SCENARIOS
artifact_type: investigation
tags: [content, scenarios, world-compositions, phase-1]
---

# Investigation: TCK-20260619-E13D-SCENARIOS

## Scenario YAML Schema (authoritative)

Inspected `data/content/simulation_scenarios/frontier_scenarios.yaml`.

Actual schema fields per document:
```yaml
- id: "<scenario_id>"
  world_composition: "<world_id>"
  focus_modules: [<module_id>, ...]
  perspective: "<perspective_id>"
  initial_conditions:
    <world_specific_key>: <value>
    ...
```

**CRITICAL**: `initial_conditions` does NOT use `entity_count`, `seed`, or `tick_limit`.
It uses world-specific semantic fields (e.g., `wolf_hunger_pressure: "medium_high"`,
`goblin_resource_pressure: "medium"`, `caravan_value: "high"`).
The ticket's suggested `initial_conditions` fields are NOT the actual schema.

**CRITICAL**: `perspective` uses faction-based IDs from `data/content/social/perspectives.yaml`,
NOT entity archetype tags. Valid IDs:
- `hero_guild_perspective`
- `merchant_league_perspective`
- `wild_beast_pack_perspective`
- `goblin_warband_perspective`
- `undead_remnants_perspective`
- `swamp_tribe_perspective`

The ticket's suggested perspectives (`warrior`, `scout`, `merchant`, `hunter`) are invalid.

## World Composition Module IDs

- `dungeon_crawl`: ruins_mystery_quest, goblin_camp_conflict, old_mine_resource_loop, scalable_bandit_camp
- `urban_political`: frontier_village_core, trading_company_hub, bandit_road_trade_pressure
- `wilderness_survival`: forest_deep_ecology, wolf_den_near_forest, undead_battlefield

## Current Scenario State

Only `data/content/simulation_scenarios/frontier_scenarios.yaml` exists (8 scenarios,
all using `frontier_living_world` or `frontier_extended` or `swamp_border_world`).
`dungeon_crawl`, `urban_political`, `wilderness_survival` each have 0 scenarios.

## E13A Status (quest defs)

DONE. Added 30 quest definitions to 10 modules including `frontier_village_core`,
`trading_company_hub`, `bandit_road_trade_pressure`. These are the modules in
`urban_political` composition. Quest test may be runnable.

## E13C Status (recipes)

DONE. 25 recipes in `data/content/world/recipes.yaml`. Full chain:
iron_ore×3 → steel → steel+ember_core → ember_axe. BUT `settled_quarter`
module is NOT in any world composition — `test_crafting_chain_completes`
MUST be skipped (no world has blacksmith_service in a named composition).

## Integration Test Context

- Test pattern follows `test_balance_regression.py`:
  `WorldRepository("data/worlds")` → `repo.load_world(world_id)` → `WorldCompiler.compile(spec, seed=SEED)` → `Kernel(profile, state, rng)` → tick loop → `kernel.shutdown()` in finally.
- The compiled worlds in `data/worlds/` have only top-level keys (schema_version, world_id, name, description, provided_features, module_refs, generation_seed) — no pre-compiled quests.
- Quest activation depends on runtime engine.
- `test_quest_starts_in_urban_political`: E13A is done so urban_political modules have quest_definitions. BUT quest runtime activation needs to be verified. Marking as potentially runnable but using a safe assertion pattern (quest_status_counts).

## Kernel Profile

Follows `test_balance_regression.py` exactly:
- HardwareClass.CLASS_B, max_ram_mb=2048, max_cpu_percent=100.0, max_worker_count=1
- max_queue_depth=2000, max_replay_buffer_kb=0, max_observability_budget_percent=0.0
- max_tick_budget_ms=500.0

## Files to Produce

1. `data/content/simulation_scenarios/dungeon_crawl_scenarios.yaml` — 2 scenarios
2. `data/content/simulation_scenarios/urban_political_scenarios.yaml` — 2 scenarios
3. `data/content/simulation_scenarios/wilderness_survival_scenarios.yaml` — 2 scenarios
4. `tests/integration/scenarios/test_content_foundation.py` — 3 tests
