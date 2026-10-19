---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE

## Title
The Live Map colours terrain by a fixed 0..22 code table, but /api/v1/map numbers terrain per world, alphabetically, so tiles are likely mis-coloured. The live API world also ignores the authored spawn list and sends no places.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
- `StatePresenter.terrain_code_map` (src/api/presenters/state_presenter.py:174) assigns codes 0..n-1 over the sorted terrain strings PRESENT in the world, and /api/v1/manifest exposes that mapping (terrain_types).
- The frontend paints with `TILE_COLORS` (frontend/src/constants/colors.ts), a fixed table for codes 0..22 (FLOOR, WALL, WATER, TOWN, ...), in useCanvas.ts:71, and does not appear to read the manifest for terrain.
- Separately:
  - src/api/engine_manager.py:131-160 spawns 1 hero plus 9 goblins on a diagonal and ignores the world's authored spawn list;
  - `present_static` returns `locations: []` (state_presenter.py:282), so places never reach the map.

## Scope
1. Verify with a running server on one world (e.g. sandbox_world) whether tile colours match terrain. Screenshot or tile probe.
2. If confirmed: the frontend colours by terrain STRING via the manifest's terrain_types (or the API sends strings). One mapping source; no second hand-kept table.
3. Separately decide (with rpg-designer):
   - whether the live server spawns the authored world;
   - whether places are presented.
   File these as children if they are larger.

## Out of Scope
Art and assets (asset domain, #519).

## Acceptance Criteria
Tile colour follows terrain meaning for any world; a test pins the code-to-meaning path end to end.

## Related Tickets
TCK-20260821-PRESENT-MAP-STATIC; TCK-20260825-METADATA-API-BACKEND-MISSING; issue #519.

## Related Docs
docs/audits/D28_live_map_functional_correctness.md; docs/plans/live_map_scaling_roadmap.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/api/presenters/state_presenter.py; src/api/routes/manifest.py; src/api/engine_manager.py; frontend/src/constants/colors.ts; frontend/src/hooks/useCanvas.ts; frontend/src/hooks/useSimulation.ts.

## Assumptions / Open Questions
VERIFIED 2026-10-13 (rpg-implementer-3, real API app in-process on sandbox_world and dungeon_crawl): tiles were mis-coloured (forest drawn as WALL, plain as WATER, swamp as TOWN); no frontend path remapped codes through the manifest. Mixed case PLAIN/plain: PLAIN is the compiler's default fill (src/worldbuilding/compiler.py:480) and plain comes from content; the engine keys TERRAIN_COST by upper-case names (a lower-case forest tile misses its 1.5 cost: a separate upstream finding, reported to rpg-planner), so the case is not changed at the source (it would move pathing and state hashes) and is folded in the single code-map builder. The spawn (hero + 9 goblins, authored entities ignored) and locations: [] are the designer's questions (D69 tickets). Tier recorded as hotfix: a presenter fold, a frontend lookup and tests.

## Implementation Notes
Backend: StatePresenter.terrain_code_map folds case (one terrain, one code; every raw string keeps its key). Frontend: constants/terrainPalette.ts builds a palette from the manifest terrain_types (code -> display name -> colour by meaning, derived from the single hand-kept TILE_NAMES/TILE_COLORS table plus aliases plain/grass/ruin/river); unknown terrain draws magenta, never FLOOR; the hover name reads the manifest; GameCanvas takes manifest and useCanvas redraws the grid when it arrives. For asset-planner (left alone): the visualAssets pilot/draft copies TILE_COLORS_COPY / TILE_NAMES_COPY in pilotScene.ts and terrainDrafts.ts (and mapScene.ts) still key by the fixed code table, and src/test pins them to colors.ts TILE_COLORS/TILE_NAMES, which stay exported for that reason.

## Test Summary
tests/api/test_live_map_terrain_codes_resolve_through_the_manifest.py (3): for sandbox_world and dungeon_crawl every tile code resolves through /manifest to the terrain the compiled engine holds; one terrain has one code whatever its case. frontend/src/test/terrainPalette.test.ts (6). Full vitest 365 passed; tsc clean; tests/api manifest and metadata groups pass except test_metadata_api.py::test_resources_real_fields_from_catalog, which fails the same way on the base (rpg-single-pr).

## Files Changed
src/api/presenters/state_presenter.py; frontend/src/constants/terrainPalette.ts; frontend/src/hooks/useCanvas.ts; frontend/src/components/GameCanvas.tsx; frontend/src/App.tsx; tests as above.

## Completion Summary
Done: the live map colours terrain by its meaning from the manifest.
