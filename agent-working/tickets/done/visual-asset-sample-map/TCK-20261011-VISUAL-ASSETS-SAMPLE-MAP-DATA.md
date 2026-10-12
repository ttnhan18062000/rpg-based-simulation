---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA
phase: done
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA

## Title
Sample map: read three real worlds' terrain grid and static objects read-only into sample-map data files

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`.

## Scope
- Pick 3 compiled worlds from `make world-list` (`python3 -m src.worldbuilding.cli list`) that cover a town, a wilderness with several terrains, and a dungeon area. Planner's starting choice: `frontier_living_world`, `swamp_border_world` or `highland_traverse`, and `dungeon_crawl`. Swap a world if it does not cover its role, and say why.
- Build each world's state the way the API does (the world assembly path the server uses; cite it), read-only, then call `StatePresenter.present_map(state)` and `present_static(state)` (`src/api/presenters/state_presenter.py:186`, `:221`). Also read the location and entity kinds a typical run places, from the compiled world/scenario files or `world-inspect` output.
- **Planner finding: `present_map`'s integer codes are per world** (`terrain_code_map`, `state_presenter.py:183`, sorted names of that world's terrains), NOT the fixed Live Map tile codes the registry descriptions cite. Store each cell as the terrain NAME and map names to `terrain.<snake_case>` keys. Record every name without a key as a gap.
- Write one JSON per world under `reports/visual_assets/sample_map/<world>/` (local, gitignored) through a tool `tools/visual_assets_sample_map.py data <world>`: width, height, terrain names per cell, static objects (buildings, resource nodes, chests, regions) and location/entity kinds with counts. Deterministic: same world -> byte-identical file.
- Cite every source file and command in the ticket so the data can be reproduced (lead).

## Out of Scope
- **No activation** (lead guard): no `frontend/` or `src/` edit, no change to how the Live Map draws, nothing wired into the app. `src/` is imported read-only to build a world state and call its presenters; nothing is written into `src/`, the content registries or `data/`.
- The rendered picture is evidence, not a shipped asset: never intake, adopt or put in a release candidate.
- No new art, no registry key, no store or drawing-tool code change, no bound change.
- Waiting on #519: answers correct the gap report only, with no re-render beyond that (lead).

## Acceptance Criteria
- [ ] Three data files, each produced twice byte-identical; the commands and files cited.
- [ ] A terrain-name -> key table, with every unmapped name listed.
- [ ] Location and entity kinds with counts per world. Any kind with no glyph or marker key is listed.
- [ ] `git status` shows nothing written under `src/`, `data/` or the content registries.

## Related Tickets
- Parent: `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`

## Related Docs
- `docs/assets/store_contract.md` (runtime manifest, atlas), `docs/assets/pilot_terrain_key.md`, `docs/assets/surface_rehearsal_result.md`, `docs/assets/icon_style_guide.md`
- `agent-working/tickets/done/TCK-20260821-PRESENT-MAP-STATIC.md` (where `present_map` / `present_static` come from)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` (field-level drop and derive decisions of `present_static`)

## Related Code Areas
- `src/worldbuilding/cli.py`, `src/worldassembly/**`, `src/api/presenters/state_presenter.py` (all read-only), `tools/visual_assets_sample_map.py`

## Assumptions / Open Questions
- If building a state needs a write anywhere outside `reports/` (e.g. `world-compile` writing active state files), STOP and ask asset-planner. Do not run it into the shared checkout.

## Implementation Notes
- Tool: `tools/visual_assets_sample_map.py` (`data <world>`, `data --all`, `keytable`); tests `tests/visual_assets/test_sample_map_data.py` (16). Output only to the gitignored `reports/visual_assets/sample_map/<world>/world_data.json` (the tool refuses any other root; `reports/*` is in `.gitignore`).
- How the state is built (cited): exactly as the API does, `src/api/engine_manager.py:133-136` (`WorldRepository("data/worlds").load_world(id)`, `WorldCompiler.compile(spec, seed=42)`; 42 is the `EngineManager` default seed, `engine_manager.py:25`), then `StatePresenter.present_map` / `present_static` (`src/api/presenters/state_presenter.py:186`, `:221`). Write behaviour checked, not assumed: `compile` writes only when `output_report_path` is given (`src/worldbuilding/compiler.py`, the last lines) and the tool never gives one; `world-compile` (`cli.py handle_compile`) would write `world_compile_report.json` next to the world and `world-list` (`repository.rebuild_index`) rewrites `world_index.json`, so neither is run. A test snapshots `data/worlds` (path, size, mtime) around a build: unchanged. `git status` after the runs shows only the new tool and test.
- Worlds (`make world-list` lists 24): `frontier_living_world` 161x106 (town hall, 2 inns, 2 shops, blacksmith, healer hut next to forest, swamp, road, plain and a dungeon area: cave 1,886 cells, ruin, old mine entrance), `highland_traverse` 211x211 (wilderness with mountain, river, forest, plain; a watchtower), `dungeon_crawl` 101x121 (ruin and forest, 12 sentinels and scouts, no buildings and no resource nodes). Swapped from the planner's list: `swamp_border_world` is not used because it adds no terrain name the frontier world lacks (swamp, forest, plain recur), whereas `highland_traverse` adds mountain and river. `dungeon_crawl` stays but is thin: its "dungeon" is the terrain name `ruin` only (no `dungeon_entrance`, `wall` or `floor` cells); the frontier world supplies the cave and the mine.
- Terrain name -> key (exact rule: lower case, spaces to underscores, key must be registered; a near key is listed and never applied). Mapped: `forest` (4,252 cells) -> `terrain.forest`; `cave` (1,886) -> `terrain.cave`; `mountain` (1,681) -> `terrain.mountain`; `road` (947) -> `terrain.road`; `swamp` (170) -> `terrain.swamp`. UNMAPPED: `PLAIN` (54,661 cells, the compiler's default fill) and `plain` (5,578) (no `terrain.plain`), `river` (1,271), `ruin` (3,362; near `terrain.ruins`, not applied). Findings: the same world has both `PLAIN` and `plain` as separate terrain names (the compiler fills `PLAIN`, region painting uses `plain`), and `ruin` is not `ruins`; both are inputs for the gap report and for rpg-planner (#519), not guesses here.
- Proposed aliases (asset-planner's addition, for RENDER's second view): a SECOND, clearly labelled table `proposed_aliases` in each data file, label "unconfirmed: asset-planner proposal for rpg-planner (#519)": `PLAIN` and `plain` -> `terrain.grassland`, `ruin` -> `terrain.ruins`, `river` -> `terrain.shallow_water`, building `shop` -> `icon.building.store`, place `CAMP` -> `icon.marker.enemy_camp`, `RUIN` -> `icon.marker.ruins`. Each applies only to a name WITHOUT an exact key (an exact key always wins), each target is asserted to be a registered key, and the aliases live only in the data file and the tool: never in the registry's `aliases` (a test asserts it is empty) and no key was added. The exact view stays the primary evidence; every number the page and the gap report quote names which view it comes from. On `river`: `terrain.shallow_water` was proposed (the highland world's region is named "River Ford"); `terrain.water` is the alternative, and it is a proposal either way.
- Findings for rpg-planner (reported, not resolved; cited to #519): the live client draws terrain from a fixed code table (`frontend/src/constants/colors.ts`, 0 FLOOR .. 22 GRAVEYARD) while `present_map` sends per-world sorted indices (`state_presenter.py:174-205`, where `PLAIN` sorts first and becomes 0), and the V2 world vocabulary (`PLAIN`/`plain`/`river`/`ruin`) is not the 23-code set the keys follow. The `PLAIN` / `plain` duplicate is the second row.
- Kinds with counts (each unkeyed kind is a gap): buildings: blacksmith 1 -> `icon.building.blacksmith`, inn 2 -> `icon.building.inn` (frontier; highland 1 each); shop (2 frontier, 1 highland; semantically near `icon.building.store`, not applied), healer_hut, mine_entrance, town_hall, watchtower: no key. Resource-node kinds (frontier 8 kinds, 12 nodes; highland 3): no marker key (`icon.marker.resource_grove` is one grove marker, not applied). Place kinds: CITY, NEST: no key; CAMP (near `icon.marker.enemy_camp`) and RUIN (near `icon.marker.ruins`): not applied. Entity kinds (`e.kind`): alpha, blacksmith, guard, leader, merchant, predator_hunter, raider, scout, sentinel, worker: no `icon.class.*` key (the four class icons are warrior, ranger, mage, rogue). Treasure chests: 0 in all three worlds.
- Determinism: `data --all` run twice, the three files byte-identical (sha256 prefixes 9e96c2c157c3f014, d8746433306f3f13, caa36377b7334ddf); sizes 10,014 / 5,931 / 2,719 B.

## Test Summary
`tests/visual_assets/test_sample_map_data.py`: 16 passed (the proposed aliases only for names without an exact key, unregistered target refused, registry has no alias, labelled in the file; exact mapping rule and near keys not applied, per-family prefixes, RLE, output refused outside the report directory, determinism, `data/worlds` untouched, cell-by-cell equality with the compiled state, kinds counted). Not a guarded file: the proof record is unaffected.

## Files Changed
- `tools/visual_assets_sample_map.py` (new), `tests/visual_assets/test_sample_map_data.py` (new)

## Completion Summary
`tools/visual_assets_sample_map.py` (`data`, `keytable`): the state built exactly as the API builds it, in memory, nothing written outside the gitignored reports; three worlds (`frontier_living_world`, `highland_traverse`, `dungeon_crawl`) read, cells stored by terrain name, names mapped to keys by an exact rule (near keys listed, not applied); 87.9 % of 73,808 cells have no exact key; labelled proposed aliases added at asset-planner's request. Commit `8ca3eabea`.
