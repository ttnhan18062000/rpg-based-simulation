---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260630-WORLD-DEPLOY-MODULES
artifact_type: investigation
tags: [world, modules, compositions, compile, assembly]
---

# Investigation

## Ticket
TCK-20260630-WORLD-DEPLOY-MODULES — Deploy 7 unused world modules into compiled worlds

---

## 1. Module Coverage in Existing Compositions

Checked all three stub compositions against the 7 target modules:

| Module | frontier_extended | frontier_living_world | swamp_border_world |
|---|---|---|---|
| forest_warden_grove | YES | no | no |
| sunken_swamp_border | no | no | YES |
| mountain_pass | no | no | no |
| nomadic_herd | no | no | no |
| river_crossing | no | no | no |
| settled_quarter | no | no | no |
| survivor_camp_shelter | no | no | no |

After compiling the 3 stub compositions: **5 modules still uncovered**:
- `mountain_pass`
- `nomadic_herd`
- `river_crossing`
- `settled_quarter`
- `survivor_camp_shelter`

---

## 2. Module `requires:` Dependencies

Checked each of the 7 target modules for hard dependencies:

| Module | requires | Safe to add standalone? |
|---|---|---|
| forest_warden_grove | `frontier_village_core`, `wolf_den_near_forest` | Yes — both present in frontier_extended |
| sunken_swamp_border | `frontier_village_core` | Yes — present in swamp_border_world |
| mountain_pass | (none) | Yes |
| nomadic_herd | (none) | Yes |
| river_crossing | (none) | Yes |
| settled_quarter | (none) | Yes |
| survivor_camp_shelter | (none) | Yes |

All 5 remaining uncovered modules have no `requires:` hard dependencies — they can be freely added to any composition.

---

## 3. Compile Pipeline (WorldCompositionSpec path)

Source: `docs/world/compiler_contract.md`, `src/worldbuilding/cli.py`

The composition compile pipeline is a two-phase process:

**Phase 1: Resolve**
- `python3 -m src.worldbuilding.cli resolve <world_id>`
- Reads `data/worlds/<world_id>/world.yaml` (must be `worldcomposition.v1`)
- Calls `WorldAssemblyResolver.assemble(composition)` → `ResolvedWorldBundle`
- Writes to `data/worlds/<world_id>/resolved/`:
  - `world.resolved.yaml` — normalized WorldSpec
  - `compile_context.json` — role/faction semantic mappings
  - `provenance_manifest.json` — audit trail
  - `assembly_report.json` — phase-by-phase log
  - `validation_report.json` — schema/context validation results

**Phase 2: Compile**
- `python3 -m src.worldbuilding.cli compile <world_id> --from-resolved`
- Loads `resolved/world.resolved.yaml` + `resolved/compile_context.json`
- Calls `WorldCompiler.compile(spec, seed, output_report_path, context)`
- Writes `data/worlds/<world_id>/world_compile_report.json`

**Pre-requisite:** The composition YAML at `data/content/world_compositions/<name>.yaml` must be
copied/linked to `data/worlds/<name>/world.yaml` before resolving. Existing compiled worlds
(e.g. `dungeon_crawl`) follow this exact pattern.

---

## 4. Confirmed from existing world structure

Examined `data/worlds/dungeon_crawl/`:
- `world.yaml` — `worldcomposition.v1` (composition spec is the source of truth)
- `resolved/` — contains all 5 sidecar files from the resolve phase
- `world_compile_report.json` — compile output

---

## 5. Plan for uncovered modules

Strategy for the 5 uncovered modules:

**Option A — Modify `frontier_living_world`**: Add `nomadic_herd`, `settled_quarter`, `survivor_camp_shelter` (no `requires:` conflicts — frontier_living_world already has `frontier_village_core` for `settled_quarter`'s `biomes: frontier_village`)

**Option B — New `highland_traverse` composition**: Add `mountain_pass` + `river_crossing`. These are terrain/transit modules with no faction dependencies. Create `highland_traverse` with `frontier_village_core` as base + these two terrain modules. This avoids polluting `frontier_living_world` with incompatible biomes (`frozen_peak`, `near_forest`).

Decision:
- Modify `frontier_living_world.yaml`: add `nomadic_herd`, `settled_quarter`, `survivor_camp_shelter`
- Create new `highland_traverse.yaml`: add `frontier_village_core`, `mountain_pass`, `river_crossing`

This fully covers all 7 unused modules in compiled worlds.

---

## 6. Calibration

`tools/calibrate_simq.py` loads from `data/worlds/<name>/resolved/world.resolved.yaml` when it exists,
then runs the engine for N ticks. Usage:

```bash
python3 tools/calibrate_simq.py --name <world_id> --seed 42 --ticks 200 --output "data/calibration/<world_id>_seed42_200t"
```

---

## 7. Key Questions Resolved

1. Which of the 7 unused modules appear in `frontier_living_world` and `swamp_border_world`?
   - `frontier_living_world`: none
   - `swamp_border_world`: `sunken_swamp_border` only

2. After compiling 3 stubs — are all 7 covered?
   - No. 5 remain uncovered: `mountain_pass`, `nomadic_herd`, `river_crossing`, `settled_quarter`, `survivor_camp_shelter`

3. Is there a CLI for compilation?
   - Yes: `python3 -m src.worldbuilding.cli resolve <id>` then `compile <id> --from-resolved`
   - Also accessible via `make world-resolve WORLD=<id>` and `make world-compile WORLD=<id>` (but Makefile compile doesn't pass `--from-resolved` so needs manual override)

4. Do any of the 5 uncovered modules have `requires:` dependencies?
   - None of the 5 have `requires:` — safe to add to any composition.
