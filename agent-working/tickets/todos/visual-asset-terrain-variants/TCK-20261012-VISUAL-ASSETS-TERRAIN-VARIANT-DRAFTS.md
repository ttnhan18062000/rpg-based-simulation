---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS
phase: open
date: 2026-10-12
tags: [architecture, testing, mcp]
---

# TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS

## Title
Terrain variants: detail axes on seven terrain keys, about 14 drawn variants, owner review folder and adopt-set

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. The art itself.

## Scope
- **Owner-only step 1 (blocking question, neutral fixed-order options):** the detail values per key. Start from the planner's split below; the owner may change counts or terrains.
Planner's proposed split (14 tiles; the owner decides the values in child 3's blocking question):
  - `terrain.grassland` (60,239 sample cells via the alias): 4 new values -> `base` + 4 = 5
  - `terrain.mountain`, `terrain.cave`, `terrain.ruins`, `terrain.swamp`, `terrain.shallow_water`: 2 new values each -> `base` + 2 = 3 each
  - `terrain.forest` keeps its 3; `terrain.road` gets none (a road wants connecting tiles, gap G5, not random variants).
- Add the approved `detail` axes (default `base`) to the keys, per child 1's design.
- Draw the variants with the `aseprite-pixel-art` MCP tools from a session started after the 2026-10-11 restart: the first `new_sprite` confirms the server pin. If it still refuses, STOP and tell asset-planner, and do not drive the api around it this time without asking. Follow `docs/assets/pixel_art_technique.md` and the existing tile palettes. A variant must read as the same terrain at 1x and break up repetition (one feature, not a new terrain). Lint clean or justified.
- Make one draft set; intake PASS for each; measure each against the bounds.
- **Owner review folder:** `~/Work/asset-review/terrain-variants-v1/`. Large labelled PNG canvases: each key's base plus its variants side by side, and a 16x16-cell sample patch tiled with the client's pick (the sample-map renderer), with a README. Not the Vite page.
- **Owner-only step 2:** the owner reviews the WHOLE set and runs `adopt-set` (no per-tile adoption). Redraws on request.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] The owner's detail-value answer recorded; axes added.
- [ ] Every variant intake PASS, measured, in one draft set; the review folder delivered.
- [ ] The owner ran `adopt-set` (adoption id recorded), or the redraws asked for are done and adopted.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/drawing/**` (used), `visual_assets/drafts/`, `visual_assets/catalog/**`, `tools/visual_assets_sample_map_render.py` (used for the review patch)

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

