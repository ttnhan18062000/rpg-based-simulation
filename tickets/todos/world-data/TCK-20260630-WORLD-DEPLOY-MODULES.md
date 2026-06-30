---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260630-WORLD-DEPLOY-MODULES
phase: open
date: 2026-06-30
tags: [world, modules, compositions, content]
---

# TCK-20260630-WORLD-DEPLOY-MODULES

## Title
Deploy 7 unused world modules into compiled worlds

## Status
OPEN

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
- [ ] `data/worlds/frontier_extended/world_compile_report.json` exists with no errors
- [ ] `data/worlds/frontier_living_world/world_compile_report.json` exists with no errors
- [ ] `data/worlds/swamp_border_world/world_compile_report.json` exists with no errors
- [ ] All 7 previously unused modules appear in at least one compiled world
- [ ] `python3 -c "import yaml; ..." data/worlds/*/world.yaml` covers all 20 modules
      (every module_id appears in at least one world)
- [ ] At minimum one 200-tick calibration run committed for each new compiled world

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
- Compile command: `python3 -c "from src.worldbuilding.compiler import WorldCompiler; ..."`
  (verify actual compile API before implementing)
- Verify `forest_warden_grove` and `orc_clan_territory` are already in `frontier_extended`
  composition — they should be; just need to compile the world.
- For modules not in any existing composition (`mountain_pass`, `river_crossing`,
  `nomadic_herd`, `settled_quarter`): check if `frontier_living_world` includes them before
  creating a new composition.

## Test Summary
- Compile test: each new world passes `WorldCompiler.compile()` without errors
- Integration: `pytest tests/integration/worldassembly/ -k frontier_extended` (new test)
- Calibration: 200-tick runs confirm entity_count > 0, region_count > 0 for each new world

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
