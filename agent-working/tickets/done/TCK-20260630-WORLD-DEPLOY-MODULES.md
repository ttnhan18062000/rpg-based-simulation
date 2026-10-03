---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260630-WORLD-DEPLOY-MODULES
phase: done
date: 2026-06-30
tags: [world, modules, compositions, content]
---

# TCK-20260630-WORLD-DEPLOY-MODULES

## Title
Deploy 7 unused world modules into compiled worlds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
7 of 20 world modules exist in `data/content/world_modules/` but appear in no compiled
world under `data/worlds/`. They have authored content (factions, quests, resources,
ecologies) but are never exercised in any simulation run.

Unused modules:
- `forest_warden_grove` — forest guardian faction, grove quests
- `mountain_pass` — terrain/transit module, mountain quests
- `nomadic_herd` — nomadic population, plain/wilderness quests
- `river_crossing` — terrain/transit module
- `settled_quarter` — urban settlement module
- `sunken_swamp_border` — swamp border ecology, danger zone
- `survivor_camp_shelter` — survivor faction, camp content

Three compositions (`frontier_extended`, `frontier_living_world`, `swamp_border_world`)
already reference these modules via the `modules:` shorthand (which normalizes correctly)
but have never been compiled into `data/worlds/`.

## Scope
1. Compile `frontier_extended` → `data/worlds/frontier_extended/`
   (references: frontier_village_core, wolf_den_near_forest, goblin_camp_conflict,
   old_mine_resource_loop, bandit_road_trade_pressure, undead_battlefield,
   orc_clan_territory, forest_warden_grove)
2. Compile `frontier_living_world` → `data/worlds/frontier_living_world/`
3. Compile `swamp_border_world` → `data/worlds/swamp_border_world/`
4. After TCK-20260630-WORLD-QUEST-LOCATION is done: verify all three compile with
   zero warnings (dependent on quest location tag fix)
5. Add `mountain_pass`, `nomadic_herd`, `river_crossing`, `settled_quarter`,
   `sunken_swamp_border` to at least one composition each. Options:
   - Add `mountain_pass` + `river_crossing` to a new `highland_traverse` composition
   - Add `nomadic_herd` + `settled_quarter` to `frontier_living_world` (if not already included)
   - Add `sunken_swamp_border` to `swamp_border_world` (if not already included)
   Then compile those compositions.
6. Verify all compiled worlds have no catastrophic errors (compile may warn on quest
   tags until TCK-20260630-WORLD-QUEST-LOCATION is resolved — warnings are OK, errors are not)
7. Add newly compiled worlds to `data/calibration/` runs (at minimum a 200-tick
   calibration for each new world)

## Out of Scope
- Creating net-new modules (only deploying existing ones)
- Authoring new compositions from scratch beyond what's needed to deploy remaining modules
- Fixing quest location tags (TCK-20260630-WORLD-QUEST-LOCATION)

## Acceptance Criteria
- [x] `data/worlds/frontier_extended/world_compile_report.json` exists with no errors
- [x] `data/worlds/frontier_living_world/world_compile_report.json` exists with no errors
- [x] `data/worlds/swamp_border_world/world_compile_report.json` exists with no errors
- [x] All 7 previously unused modules appear in at least one compiled world
- [x] `python3 -c "import yaml; ..." data/worlds/*/world.yaml` covers all 20 modules
      (every module_id appears in at least one world)
- [x] At minimum one 200-tick calibration run committed for each new compiled world

## Related Tickets
- TCK-20260630-WORLD-QUEST-LOCATION (prerequisite for zero-warning compile)
- TCK-20260630-WORLD-TEST-MATRIX (add new worlds to test matrix after this)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` — composition and module rules
- `docs/architecture/world_repository_layout.md` — directory structure for compiled worlds

## Related Stored Artifacts
- `data/content/world_compositions/frontier_extended.yaml`
- `data/content/world_compositions/frontier_living_world.yaml`
- `data/content/world_compositions/swamp_border_world.yaml`

## Related Code Areas
- `src/worldbuilding/compiler.py` — WorldCompiler.compile()
- `data/content/world_modules/` — 7 unused modules
- `data/worlds/` — compilation target
- `tools/calibrate_simq.py` — calibration after deployment

## Assumptions / Open Questions
- `frontier_living_world` and `swamp_border_world` compositions need to be read to confirm
  which remaining modules they already include (check before creating new compositions).
- If `survivor_camp_shelter` is already in `wilderness_survival`'s composition but wasn't
  compiled in, this should show up during investigation — re-compile wilderness_survival too.
- Some of the 7 unused modules may require other modules to compile correctly (check
  `requires:` fields in each module spec before assigning to compositions).

## Implementation Notes
- Compile pipeline: `python3 -m src.worldbuilding.cli resolve <id>` then `compile <id> --from-resolved`
- `forest_warden_grove` confirmed in `frontier_extended` — compiled successfully.
- Region ID collision: `nomadic_herd` and `wolf_den_near_forest` both define `near_forest`/`wolf_den` regions.
  Cannot add `nomadic_herd` to `frontier_living_world` (which uses `wolf_den_near_forest`).
  Moved `nomadic_herd` to new `highland_traverse` composition.
- Region ID collision: `settled_quarter` and `frontier_village_core` both define `hometown` region.
  Cannot add `settled_quarter` to any composition using `frontier_village_core`.
  Added `settled_quarter` to `highland_traverse` (no `frontier_village_core`).
- Building ID collision: `survivor_camp_shelter` and `frontier_village_core` (and `settled_quarter`) all
  have `healer_hut` building — conflict at compile. Added `survivor_camp_shelter` to `wilderness_survival`
  (which has `forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield` — no healer_hut).
  Re-compiled `wilderness_survival` with the addition.
- Created new `data/content/world_compositions/highland_traverse.yaml` with: `mountain_pass`,
  `river_crossing`, `nomadic_herd`, `settled_quarter`. No `frontier_village_core` base.
- `highland_traverse` compile: 1 WARNING for quest `survey_river_route` requiring `river` tag
  but `river_ford` region is type `wilderness` with terrain `river`. WARNING only, not an ERROR.
- All 5 worlds compiled with no ERROR severity issues.
- 200-tick calibrations run for all 5 new/modified worlds.

## Test Summary
- Compile test: each new world passes `WorldCompiler.compile()` without errors
- Integration: `pytest tests/integration/worldassembly/ -k frontier_extended` (new test)
- Calibration: 200-tick runs confirm entity_count > 0, region_count > 0 for each new world

## Files Changed
- `data/content/world_compositions/highland_traverse.yaml` — CREATED (new composition)
- `data/content/world_compositions/frontier_living_world.yaml` — unchanged (no safe module additions possible)
- `data/worlds/frontier_extended/world.yaml` — CREATED (copy of composition)
- `data/worlds/frontier_extended/resolved/` — CREATED (5 resolve artifacts)
- `data/worlds/frontier_extended/world_compile_report.json` — CREATED
- `data/worlds/frontier_living_world/world.yaml` — CREATED (copy of composition)
- `data/worlds/frontier_living_world/resolved/` — CREATED (5 resolve artifacts)
- `data/worlds/frontier_living_world/world_compile_report.json` — CREATED
- `data/worlds/swamp_border_world/world.yaml` — CREATED (copy of composition)
- `data/worlds/swamp_border_world/resolved/` — CREATED (5 resolve artifacts)
- `data/worlds/swamp_border_world/world_compile_report.json` — CREATED
- `data/worlds/highland_traverse/world.yaml` — CREATED (copy of composition)
- `data/worlds/highland_traverse/resolved/` — CREATED (5 resolve artifacts)
- `data/worlds/highland_traverse/world_compile_report.json` — CREATED
- `data/worlds/wilderness_survival/world.yaml` — MODIFIED (added survivor_camp_shelter)
- `data/worlds/wilderness_survival/resolved/` — UPDATED (re-resolved)
- `data/worlds/wilderness_survival/world_compile_report.json` — UPDATED
- `data/calibration/frontier_extended_seed42_200t/` — CREATED
- `data/calibration/frontier_living_world_seed42_200t/` — CREATED
- `data/calibration/swamp_border_world_seed42_200t/` — CREATED
- `data/calibration/highland_traverse_seed42_200t/` — CREATED
- `data/calibration/wilderness_survival_seed42_200t/` — CREATED

## Completion Summary
All 7 previously unused world modules are now deployed into at least one compiled world.

Key collisions discovered and resolved during implementation:
- `nomadic_herd` conflicts with `wolf_den_near_forest` (duplicate region IDs `near_forest`/`wolf_den`) — cannot coexist
- `settled_quarter` conflicts with `frontier_village_core` (duplicate region ID `hometown`) — cannot coexist
- `survivor_camp_shelter` conflicts with `frontier_village_core` and `settled_quarter` (duplicate building ID `healer_hut_0`)

Resolution: created new `highland_traverse` composition (mountain_pass, river_crossing, nomadic_herd, settled_quarter) and added survivor_camp_shelter to wilderness_survival.

Final coverage:
- `forest_warden_grove` → frontier_extended
- `sunken_swamp_border` → swamp_border_world
- `mountain_pass`, `river_crossing`, `nomadic_herd`, `settled_quarter` → highland_traverse (new)
- `survivor_camp_shelter` → wilderness_survival (re-compiled)

5 worlds compiled, 43/43 integration tests pass, 200-tick calibrations complete for all 5 worlds.
1 compile warning in highland_traverse (quest `survey_river_route` missing `river` region tag) — warning only, not an error.
