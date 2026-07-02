---
ticket_id: TCK-20260619-E13B-MODULE-TYPES
phase: plan
date: 2026-06-20
---

# Plan: TCK-20260619-E13B-MODULE-TYPES — New Module Types (Terrain + Population)

## Summary

Author 4 new world module YAML files. No code changes required — `terrain` and `population`
are already in `REGISTERED_MODULE_TYPES` in `src/worldmodules/schema.py`.

## Steps

### Step 1 — Author mountain_pass.yaml (terrain)
File: `data/content/world_modules/mountain_pass.yaml`
- module_type: terrain
- biome: frozen_peak
- factions: [] (neutral)
- resources: iron_vein, frost_shard_cluster
- 2 quest definitions: explore_mountain_route (explore), hunt_mountain_predator (hunt)
- grid_bounds: [80, 80, 120, 120]
AC: loads cleanly, module_type=terrain

### Step 2 — Author river_crossing.yaml (terrain)
File: `data/content/world_modules/river_crossing.yaml`
- module_type: terrain
- biome: near_forest
- factions: [] (neutral)
- resources: herb_patch
- buildings: watchtower
- 1 quest definition: survey_river_route (explore)
- grid_bounds: [130, 30, 160, 70]
AC: loads cleanly, module_type=terrain

### Step 3 — Author nomadic_herd.yaml (population)
File: `data/content/world_modules/nomadic_herd.yaml`
- module_type: population
- factions: wild_beast_pack
- populations: wolf_pack_small
- 1 quest definition: track_nomadic_herd (hunt)
- grid_bounds: [60, 130, 100, 170]
AC: loads cleanly, module_type=population

### Step 4 — Author settled_quarter.yaml (population)
File: `data/content/world_modules/settled_quarter.yaml`
- module_type: population
- biome: frontier_village
- factions: merchant_league
- populations: frontier_village_population
- buildings: blacksmith, healer_hut, inn, shop
- 2 quest definitions: fetch_settlement_supplies (fetch), escort_settled_trader (escort)
- grid_bounds: [170, 80, 210, 120]
AC: loads cleanly, module_type=population

### Step 5 — Update MODULE_MATRIX in integration test
File: `tests/integration/worldassembly/test_real_content_world_modules.py`
- Add mountain_pass, river_crossing, nomadic_herd, settled_quarter to MODULE_MATRIX

### Step 6 — Run tests
```bash
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/unit/worldmodules/test_modules.py \
       tests/unit/worldmodules/test_schema_unified.py -x -v
```
Also run: `python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"`

### Step 7 — Update D07 audit doc
File: `docs/audits/D07_content_depth.md`
- Update module type distribution table: terrain 0→2, population 0→2
- Mark F2 as RESOLVED with reference to this ticket

## Scope Guards
- No new biome/ecology YAML files unless strictly required
- No changes to schema, validator, or repository (no code changes needed)
- No compositions referencing these modules (E13D scope)

## AC Mapping
| AC | Steps |
|---|---|
| 4 YAML files exist and load | 1–4 |
| python3 load_all() passes | 6 |
| make world-validate passes | 6 |
| terrain ≥ 2, population ≥ 2 | 1–4 verified in tests |

## Deviations
_None yet._
