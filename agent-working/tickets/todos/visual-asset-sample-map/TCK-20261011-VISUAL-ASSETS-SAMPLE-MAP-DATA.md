---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA
phase: open
date: 2026-10-11
tags: [architecture, testing]
---

# TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA

## Title
Sample map: read three real worlds' terrain grid and static objects read-only into sample-map data files

## Status
OPEN

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


## Test Summary


## Files Changed


## Completion Summary

