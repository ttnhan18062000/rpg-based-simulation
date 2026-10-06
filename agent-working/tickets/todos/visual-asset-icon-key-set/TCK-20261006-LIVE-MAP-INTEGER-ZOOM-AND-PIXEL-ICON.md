---
status: active
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON
phase: open
date: 2026-10-06
tags: [live-map, hud, testing]
---

# TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

## Title
Live Map zoom snaps to whole-number pixel scales, and a pixel icon component that renders at a whole-number scale

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. `GameCanvas.tsx` zooms in steps of `ZOOM_STEP = 0.15` and the overlay canvas uses
`scale(CELL_SIZE * zoom)` with `imageRendering: 'pixelated'`, so 16 px art (terrain-v1 today, icons next) draws at
fractional scales and pixels come out uneven. The research (`research_icon_craft.md`, sizes and web scaling) says
whole-number steps only, accounting for `devicePixelRatio`. The user chose to snap (2026-10-06).

## Scope
- Map zoom levels become a fixed list of scales where one art pixel is a whole number of **device** pixels
  (`CELL_SIZE * zoom * devicePixelRatio` integral, or the nearest such level); wheel and buttons step through the list;
  reset returns to the default level. Check `CELL_SIZE`, `MIN_ZOOM`, `MAX_ZOOM` and the minimap separately (minimap may
  stay as is: say which and why).
- A small `PixelIcon` component (frontend/src/visualAssets/ or components/): given a sprite and its native size, picks
  the largest whole-number scale that fits a requested box at the current `devicePixelRatio`; never fractional.
  Unused by panels in this batch except the preview page (wiring is the next batch).
- Tests (vitest): level list properties (integral at DPR 1, 1.25, 1.5, 2), stepping and clamping, `PixelIcon` scale choice.

## Out of Scope
- `src/`, server rendering. Replacing any panel icon. Changing terrain or border compositing logic.

## Acceptance Criteria
- [ ] Every reachable map zoom level renders art pixels at a whole number of device pixels at DPR 1 and 2 (tested);
      behaviour at fractional DPR stated and tested.
- [ ] Existing frontend tests pass; `npm run build` clean.
- [ ] The user can still zoom smoothly enough to use the map (state the level list in the ticket).

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic)

## Related Docs
- docs/assets/icon_research/research_icon_craft.md (after child 1)

## Related Stored Artifacts


## Related Code Areas
- frontend/src/components/GameCanvas.tsx (ZOOM_STEP, MIN_ZOOM, MAX_ZOOM, overlay transform), frontend/src/visualAssets/

## Assumptions / Open Questions
- Independent of children 2, 3 and 5; may be built in any slot before child 5's preview page.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

