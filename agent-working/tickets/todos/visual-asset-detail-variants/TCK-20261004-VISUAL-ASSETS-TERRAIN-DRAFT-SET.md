---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET
phase: open
date: 2026-10-04
tags: [architecture, mcp, live-map]
---

# TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

## Title
Draft one 16 x 16 tile for every Live Map terrain code as draft set `terrain-v1`, no adoption

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User, 2026-10-04: "draft all the assets now", review only when a full batch is done (for example full map tiles).
Terrain first: one draft per `TILE_NAMES` code, kept in draft set `terrain-v1` for a later whole-set review.

## Scope
- Register one visual key per terrain code in `visual_keys.yaml` (`terrain.<name>`, family `terrain`, description naming
  the tile code and its fallback colour), all `optional: true` so no release needs them before adoption. `terrain.forest`
  keeps its adopted slots. Keys are registered by hand in the reviewed file, as the registry requires.
- Draw each tile with the drawing tools, sharing one palette family so the set reads as one style; tiles of the same
  terrain repeat seamlessly; neighbouring terrains read apart in the colour-vision simulation the pilot used (`W05`
  method), checked on the preview page before keeping. The existing forest slots are part of the set as references,
  not redrawn.
- Hand off, intake, `draft keep` each into `terrain-v1`. No `adopt`, no `adopt-set`, no release.
- Store a screenshot of the preview page with the full set and a short style note (palette, light direction) as evidence.

## Out of Scope
- Adoption (the user's, later, by `adopt-set` after their review). Entities, buildings, items (later sets).
  Detail variants for other terrains. Animation (lava, water) beyond a single frame.

## Acceptance Criteria
- [ ] `draft verify` clean; `terrain-v1` has a draft for every `TILE_NAMES` code (forest reuses its adopted slots).
- [ ] The preview page shows the whole set with no fallback cells; screenshot stored.
- [ ] Catalog `verify` clean; no release or runtime fixture changed by this ticket.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION,
  TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE (both before)

## Related Docs
- docs/assets/drawing_tools.md, docs/assets/pilot_terrain_m5_criteria.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES/

## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/drafts/

## Assumptions / Open Questions
- The style may change once the RPG's art direction settles; drafts are cheap to replace (`draft keep --replace`).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
