---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON
phase: done
date: 2026-10-06
tags: [live-map, hud, testing]
---

# TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

## Title
Live Map zoom snaps to whole-number pixel scales, and a pixel icon component that renders at a whole-number scale

## Status
DONE

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
- agent-working/stored_artifacts/TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON/ (plan, investigation, test_plan, mutant_proof.txt)

## Related Code Areas
- frontend/src/components/GameCanvas.tsx (ZOOM_STEP, MIN_ZOOM, MAX_ZOOM, overlay transform), frontend/src/visualAssets/

## Assumptions / Open Questions
- Independent of children 2, 3 and 5; may be built in any slot before child 5's preview page.
- Corrected after re-checking against what landed (told to the planner before building): the AM5-W08 isolation test forbids any app file importing `src/visualAssets` and any `visualAssets` file importing outside it, so `PixelIcon` and the zoom code live in `src/components`, `src/hooks` and `src/lib`, not in visualAssets. Child 5's preview page (inside visualAssets) needs its own small copy of the fit function plus an equality test, as `cell.ts` does for `CELL_SIZE`.

## Implementation Notes
- Levels are `n / devicePixelRatio` for integer `n >= 1` inside the old range [0.5, 3.0] (`zoomLevels`), plus ONE overview level at the bottom (below). **Level list:** DPR 1: 0.5 (overview), 1x, 2x, 3x. DPR 1.25: 0.5 (overview), 0.8, 1.6, 2.4. DPR 1.5: 0.5 (overview), 0.667, 1.333, 2.0, 2.667. DPR 2: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0 (0.5 is already an art level, nothing added). DPR 3: 0.5 (overview), then 0.667 to 3.0 in thirds. Wheel and the +/- buttons step one level; reset goes to the level nearest 1.0 (exactly 1.0 at DPR 1 and 2).
- **Overview level (user decision after the first review, 2026-10-06, blocking question asked by the planner: "Flat-colour overview: keep 0.5x as an overview level that draws plain terrain colours instead of pixel art, so it stays crisp"):** when the range minimum is below the first art level, the zoom nearest it at which a cell (16 x zoom) is a whole number of device pixels is added at the bottom: 0.5 at DPR 1, 1.25 and 1.5 (8, 10, 12 device px per cell; the planner expected 0.4 or 0.6 at 1.25, but 0.5 already gives a whole cell), 9 / (16 x 1.1) at DPR 1.1. `isOverviewZoom(zoom, dpr)` is true where one art pixel is not a whole number of device pixels (at least 1). The Live Map draws flat fills at every level today, so nothing changes visibly; the wiring batch's art path must use it to draw the fill. The pan snap applies there too. Done as an amend of the first commit (SHA in the planner message).
- **Behaviour for the owner gate:** 0.5x is back at DPR 1, as plain colours; art levels start at 1x.
- State holds the *requested* zoom; the zoom in force is its nearest level, so a devicePixelRatio change (browser zoom, another display) re-snaps by itself (`useDevicePixelRatio`, matchMedia resolution query).
- The pan offset is drawn on whole device pixels (`snapToDevicePixel`), because a fractional translate makes art pixels uneven again at fractional DPR; the stored pan is unchanged. At DPR 1 the offset equals the mouse distance.
- The overlay canvas (1 px per tile scaled by 16 x zoom) is whole at every level too (tested).
- **Minimap stays as is** (its own zoom step of 0.3 and scale of 2 px per tile): it is an overview drawn from colours, not art, and nothing in this batch puts icons on it. Say so again if icons ever reach it.
- `PixelIcon` (src/components/PixelIcon.tsx): `src`, `native`, `box`, `label`; scale = max(1, floor(box x dpr / native)); `data-scale`, `imageRendering: pixelated`, never fractional; not used by any panel (wiring is the next batch).
- The 6 `react-hooks/refs` lint errors in GameCanvas.tsx are pre-existing (same 6 at HEAD); the new files are lint-clean.

## Test Summary
- vitest, whole frontend: 25 files, 310 passed (the isolation test and the production build included). New: `src/test/pixelScale.test.ts` (19), `PixelIcon.test.tsx` (6), `GameCanvas.zoom.test.tsx` (21: buttons, wheel, overlay, panning, the overview level, DPR change at 1, 1.25, 1.5, 2). `npm run build` clean.
- Mutants (unsnapped zoom, unsnapped pan, old 0.15 step, DPR-1 levels, overview level dropped, overview not a whole cell, isOverviewZoom ignoring fractional art pixels, overview duplicated at DPR 2) are each caught (`mutant_proof.txt`).

## Files Changed
- frontend/src/lib/pixelScale.ts, hooks/useDevicePixelRatio.ts, components/PixelIcon.tsx, components/GameCanvas.tsx, test/{pixelScale,PixelIcon,GameCanvas.zoom} tests, docs/assets/icon_style_guide.md, ticket and stored artifacts.

## Completion Summary
Live Map zoom and pan snap to whole device pixels; `PixelIcon` renders at a whole-number scale; no panel uses it yet.
