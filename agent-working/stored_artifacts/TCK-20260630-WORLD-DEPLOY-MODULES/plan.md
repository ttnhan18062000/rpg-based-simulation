---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260630-WORLD-DEPLOY-MODULES
artifact_type: plan
tags: [world, modules, compositions, compile, plan]
---

# Plan

## Ticket
TCK-20260630-WORLD-DEPLOY-MODULES — Deploy 7 unused world modules into compiled worlds

---

## Summary

Compile 3 existing stub compositions and 1 new composition to cover all 7 unused modules.
Then run 200-tick calibration for each new compiled world.

---

## Steps

### Step 1: Set up `frontier_extended` world directory
- Create `data/worlds/frontier_extended/`
- Copy `data/content/world_compositions/frontier_extended.yaml` → `data/worlds/frontier_extended/world.yaml`
- Resolve: `python3 -m src.worldbuilding.cli resolve frontier_extended`
- Compile: `python3 -m src.worldbuilding.cli compile frontier_extended --from-resolved`
- Covers: `forest_warden_grove`

### Step 2: Modify `frontier_living_world` composition + compile
- Edit `data/content/world_compositions/frontier_living_world.yaml`: add `nomadic_herd`, `settled_quarter`, `survivor_camp_shelter` to `modules:` list
- Create `data/worlds/frontier_living_world/`
- Copy modified yaml → `data/worlds/frontier_living_world/world.yaml`
- Resolve + compile
- Covers: `nomadic_herd`, `settled_quarter`, `survivor_camp_shelter`

### Step 3: Set up `swamp_border_world` world directory
- Create `data/worlds/swamp_border_world/`
- Copy `data/content/world_compositions/swamp_border_world.yaml` → `data/worlds/swamp_border_world/world.yaml`
- Resolve + compile
- Covers: `sunken_swamp_border`

### Step 4: Create new `highland_traverse` composition + compile
- Create `data/content/world_compositions/highland_traverse.yaml` with:
  - `frontier_village_core` (base settlement)
  - `mountain_pass` (terrain/transit)
  - `river_crossing` (terrain/transit)
- Create `data/worlds/highland_traverse/`
- Copy yaml → `data/worlds/highland_traverse/world.yaml`
- Resolve + compile
- Covers: `mountain_pass`, `river_crossing`

### Step 5: Verify all 7 unused modules covered
- Run coverage check script
- Assert zero uncovered modules from target set

### Step 6: Run 200-tick calibration for each new world
- `python3 tools/calibrate_simq.py --name frontier_extended --seed 42 --ticks 200 --output data/calibration/frontier_extended_seed42_200t`
- `python3 tools/calibrate_simq.py --name frontier_living_world --seed 42 --ticks 200 --output data/calibration/frontier_living_world_seed42_200t`
- `python3 tools/calibrate_simq.py --name swamp_border_world --seed 42 --ticks 200 --output data/calibration/swamp_border_world_seed42_200t`
- `python3 tools/calibrate_simq.py --name highland_traverse --seed 42 --ticks 200 --output data/calibration/highland_traverse_seed42_200t`

### Step 7: Run integration test suite
- `pytest tests/integration/worldassembly/ -v --timeout=120`

---

## Coverage Matrix After Plan

| Module | Covered by |
|---|---|
| forest_warden_grove | frontier_extended |
| sunken_swamp_border | swamp_border_world |
| mountain_pass | highland_traverse (new) |
| river_crossing | highland_traverse (new) |
| nomadic_herd | frontier_living_world (modified) |
| settled_quarter | frontier_living_world (modified) |
| survivor_camp_shelter | frontier_living_world (modified) |

---

## Files to Create/Modify

| File | Action |
|---|---|
| `data/content/world_compositions/frontier_living_world.yaml` | MODIFY — add 3 modules |
| `data/content/world_compositions/highland_traverse.yaml` | CREATE — new composition |
| `data/worlds/frontier_extended/world.yaml` | CREATE — copy from compositions |
| `data/worlds/frontier_extended/resolved/*` | CREATE — resolve output |
| `data/worlds/frontier_extended/world_compile_report.json` | CREATE — compile output |
| `data/worlds/frontier_living_world/world.yaml` | CREATE — copy from compositions |
| `data/worlds/frontier_living_world/resolved/*` | CREATE — resolve output |
| `data/worlds/frontier_living_world/world_compile_report.json` | CREATE — compile output |
| `data/worlds/swamp_border_world/world.yaml` | CREATE — copy from compositions |
| `data/worlds/swamp_border_world/resolved/*` | CREATE — resolve output |
| `data/worlds/swamp_border_world/world_compile_report.json` | CREATE — compile output |
| `data/worlds/highland_traverse/world.yaml` | CREATE — copy from compositions |
| `data/worlds/highland_traverse/resolved/*` | CREATE — resolve output |
| `data/worlds/highland_traverse/world_compile_report.json` | CREATE — compile output |
| `data/calibration/frontier_extended_seed42_200t/` | CREATE — calibration output |
| `data/calibration/frontier_living_world_seed42_200t/` | CREATE — calibration output |
| `data/calibration/swamp_border_world_seed42_200t/` | CREATE — calibration output |
| `data/calibration/highland_traverse_seed42_200t/` | CREATE — calibration output |

---

## Risk Assessment

- `settled_quarter` uses `biomes: frontier_village` and `frontier_village_population` — both present in catalog from other modules. Low risk.
- `nomadic_herd` defines a `near_forest` and `wolf_den` region — same region IDs might conflict if `wolf_den_near_forest` module is also present. frontier_living_world has `wolf_den_near_forest`, which also defines a `wolf_den` region. Potential region ID collision. If conflict arises, move `nomadic_herd` to `highland_traverse` instead.
- `survivor_camp_shelter` has no factions/populations defined — minimal content, should compile cleanly.
