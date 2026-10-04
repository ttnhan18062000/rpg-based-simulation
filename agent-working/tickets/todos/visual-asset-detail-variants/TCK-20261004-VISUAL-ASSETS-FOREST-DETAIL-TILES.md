---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES
phase: open
date: 2026-10-04
tags: [architecture, mcp, live-map]
---

# TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES

## Title
Two forest detail tiles (bush, tree) drawn, adopted by the user per slot, released as `pilot/rc-0002`

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Third child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`. Real art for the detail slots of
`terrain.forest`: the pilot tile stays `plain`; add `bush` and `tree`.

## Scope
- Draw two 16 x 16 tiles with the aseprite-pixel-art drawing tools, starting from the pilot tile's palette and ground so
  any mix of `plain` / `bush` / `tree` tiles seamlessly (edges match the plain tile; the detail sits inside the tile).
  Check with a preview of a mixed 4 x 4 arrangement before handing off. A third value is optional; if drawn, it is declared in
  the same registry change below.
- Declare the axis on `terrain.forest` in `visual_assets/catalog/definitions/visual_keys.yaml`
  (`detail: {values: [bush, plain, tree], default: plain}`), moved here from ticket 1: it changes `registry_hash`, so it lands
  together with `pilot/rc-0002`, and before the adoptions (`adopt --detail` needs it). rc-0001 stays valid (`verify`
  tolerates its axis-less entry); its export now refuses on `registry_hash`, so any test that re-exports rc-0001 (the
  fixture-equality test, the rollback drill's retained release) must be re-pointed honestly, with the change named in
  the commit; if a guard can only pass by weakening it, stop and tell the planner.
- Hand off and pass intake per tile (`export_handoff`, `submit_candidate`).
- **Adoption is the user's**, one blocking question per tile, run by the user in their own terminal:
  `adopt <intake_id> --visual-key terrain.forest --detail bush|tree ...`. Never run `adopt` or `revoke` yourself. The
  ticket ends `BLOCKED` on the user if an adoption is not given.
- Build, assemble release `pilot/rc-0002` (rc-0001 stays as the retained previous release for the rollback drill),
  export the runtime manifest, and replace the committed pilot runtime fixture by a fresh export (the equality test
  stays the guard). `verify` clean.
- `docs/assets/pilot_terrain_key.md`: the three slots, their source assets and adoptions.

## Out of Scope
- Variants for other terrains; animation; other scales. Weights. Any `src/` change.

## Acceptance Criteria
- [ ] Each new tile adopted by the user (adoption ids recorded); `verify` clean.
- [ ] `pilot/rc-0002` lists `plain`, `bush`, `tree` for `terrain.forest`; runtime manifest lists every value and the declared `details`.
- [ ] Runtime fixture equals a fresh export; the rollback drill still runs against rc-0001.
- [ ] A mixed-tile preview is attached to the ticket's evidence (stored artifact), showing no seams.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT,
  TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT, TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/drawing_tools.md, docs/assets/pilot_terrain_key.md, docs/assets/retention_and_rollback.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE/

## Related Code Areas
- visual_assets/catalog/, frontend/src/visualAssets/__fixtures__/pilot/

## Assumptions / Open Questions
- The user may reject a tile at the adoption question; redraw and re-submit, never edit store records.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
