---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13D-SCENARIOS
artifact_type: plan
tags: [content, scenarios, world-compositions, phase-1]
---

# Plan: TCK-20260619-E13D-SCENARIOS

## Ordered Steps

### Step 1 — Author dungeon_crawl scenarios (2 scenarios)
File: `data/content/simulation_scenarios/dungeon_crawl_scenarios.yaml`

Use actual schema (NO entity_count/seed/tick_limit in initial_conditions).
Use `hero_guild_perspective` (canonical — dungeon_crawl default_perspectives includes it).

Scenario 1: `dungeon_crawl_delve`
- focus_modules: [ruins_mystery_quest, goblin_camp_conflict]
- perspective: hero_guild_perspective
- initial_conditions: dungeon_threat_level: "medium", ruin_access: "open"

Scenario 2: `dungeon_crawl_desperate_descent`
- focus_modules: [scalable_bandit_camp, old_mine_resource_loop]
- perspective: hero_guild_perspective
- initial_conditions: dungeon_threat_level: "high", bandit_danger_scale: 4

AC mapped: "dungeon_crawl has ≥2 scenarios"

### Step 2 — Author urban_political scenarios (2 scenarios)
File: `data/content/simulation_scenarios/urban_political_scenarios.yaml`

Scenario 3: `urban_political_trade_war`
- focus_modules: [trading_company_hub, bandit_road_trade_pressure]
- perspective: merchant_league_perspective
- initial_conditions: trade_route_pressure: "high", bandit_activity: "medium"

Scenario 4: `urban_political_faction_struggle`
- focus_modules: [frontier_village_core, bandit_road_trade_pressure]
- perspective: hero_guild_perspective
- initial_conditions: bandit_activity: "high", town_guard_strength: "medium"

AC mapped: "urban_political has ≥2 scenarios"

### Step 3 — Author wilderness_survival scenarios (2 scenarios)
File: `data/content/simulation_scenarios/wilderness_survival_scenarios.yaml`

Scenario 5: `wilderness_survival_long_hunt`
- focus_modules: [forest_deep_ecology, wolf_den_near_forest]
- perspective: hero_guild_perspective
- initial_conditions: wolf_hunger_pressure: "medium_high", intrusion_distance_to_den: "near"

Scenario 6: `wilderness_survival_warden_escort`
- focus_modules: [undead_battlefield]
- perspective: hero_guild_perspective
- initial_conditions: undead_activity: "medium", shrine_support: "low"

Note: forest_warden_grove is NOT in wilderness_survival composition — use undead_battlefield.

AC mapped: "wilderness_survival has ≥2 scenarios"

### Step 4 — Write integration test file
File: `tests/integration/scenarios/test_content_foundation.py`

Three tests per ticket spec:
1. `test_all_world_compositions_have_two_scenarios` — schema-only, no simulation
2. `test_quest_starts_in_urban_political` — 400-tick kernel run on urban_political
3. `test_crafting_chain_completes` — SKIPPED (settled_quarter not in any composition)

Pattern: follow test_balance_regression.py (_build_kernel, try/finally: kernel.shutdown())

### Step 5 — Run tests
```bash
pytest tests/integration/scenarios/test_content_foundation.py::test_all_world_compositions_have_two_scenarios -x -v
pytest tests/unit/ -x -v -m "not slow"
```

### Step 6 — Finalize ticket and artifacts

## Scope Guards
- No new world compositions
- No engine code changes
- No new item or module definitions
- Only data/content/simulation_scenarios/ YAML files + test file

## Deviations
- Ticket suggested `entity_count`/`seed`/`tick_limit` in initial_conditions — NOT used;
  actual schema uses semantic condition keys matching existing scenarios.
- Ticket suggested `warrior`/`scout`/`merchant`/`hunter` perspectives — NOT valid;
  using canonical perspective IDs from perspectives.yaml.
- `wilderness_survival_warden_escort` uses undead_battlefield module instead of
  forest_warden_grove (which is not in the wilderness_survival composition).
