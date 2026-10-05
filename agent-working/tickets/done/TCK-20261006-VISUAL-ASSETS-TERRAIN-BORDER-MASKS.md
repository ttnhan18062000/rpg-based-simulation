---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS
phase: done
date: 2026-10-06
tags: [architecture, mcp, live-map]
---

# TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS

## Title
Draw the shared border masks, keep them in terrain-v1, and show the whole map with borders on the preview page

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Fourth child of `TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW`. With the contract, order and compositor from
`TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`, draw the real masks so the user can review the whole map with
borders once and then adopt the set (user, 2026-10-06).

## Scope
- Draw the masks with the drawing tools (Aseprite in batch mode): edge, outer corner, inner corner, 2-3 variants each,
  16x16 1-bit alpha, ragged pixel-art edge (no straight line along the cell edge, no single stray pixels), within the
  4 px cap. Hand off, intake, `draft keep` into `terrain-v1`, so one `adopt-set` covers tiles and masks.
- Preview page draws the fringes over the draft map (the flat canvas stays flat, as the control); a toggle for
  "borders on / off" so the user can compare.
- Evidence: preview-page screenshots with borders on and off, a close-up sheet of a few borders (grass/desert,
  water/grass, forest/grassland, a `crisp` edge such as town/grassland), and the masks' own sheet at 8x.
- Re-run the set check (`AM5-S`; expected unchanged, since it reads tile means) and the compositor tests on the real masks.

## Out of Scope
- Adoption (the user's, after this ticket). Live Map. Changing the order, the `crisp` set or the cap (contract ticket).

## Acceptance Criteria
- [x] Masks kept in `terrain-v1`; `draft verify`, catalog `verify` clean; the 4 px cap test passes on every mask.
- [x] Preview page shows borders with an on/off toggle; screenshots stored.
- [x] `AM5-S` still PASS (or the change is reported as measured).
- [x] Nothing adopted.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT (previous)

## Related Docs
- docs/assets/store_contract.md, docs/assets/pilot_terrain_m5_criteria.md

## Related Stored Artifacts
- None yet.

## Related Code Areas
- frontend/src/visualAssets/ (DraftHarness.tsx, terrainDrafts.ts), visual_assets/drafts/terrain-v1/

## Assumptions / Open Questions
- None beyond the contract ticket's.

## Implementation Notes
Nine masks (edge, outer_corner, inner_corner x v1-v3), generator and drawing driver in the stored artifacts, handed off, `store intake` (all PASSED) and `draft keep --set terrain-v1 --as border.<kind> --detail <v>` (source asset ids `border_<kind>_<v>`); nothing adopted. Contract details (4 px cap, orientations, depth-2 ends) are in the criteria doc and the mask generator's docstring.
**Render match (planner condition):** `rendering.compare_preview` with the real sandboxed Aseprite renderer on all 31 entries: 31 of 31 `MATCH`, `rendered_pixel_hash` equal to each entry's `pixel_hash` (9 masks and 22 tiles as control; table in `render_match_terrain_v1.txt`). Rendering and intake untouched.
Preview page: `borderRender.ts` composes fringes with the contract's compositor over the draft map and `DraftHarness` has a "Show terrain borders" toggle (on by default, with a status line "Borders on: N map cells carry a fringe"); the flat canvas stays flat. With the exported set: 140 cells carry a fringe. Evidence: `map_borders_on_1x.png`, `map_borders_off_1x.png`, `preview_page_borders_on.png`, `preview_page_borders_off.png`, `border_closeups_off_left_on_right.png` (desert/swamp, water/swamp, forest/desert, town (crisp)/mountain, grassland/snow, mountain/grassland), `masks_sheet_8x.png`.
AM5-S rerun: byte-identical report to the re-tint ticket (PASS, 0 of 1012); `draft_tiles` now reads only `terrain.` entries because the rule is about tiles. Fringes are outside AM5-S. Honest wording unchanged: PASS means no worse than the flat fills.
Set hash with masks (draft export): sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2. The 9 mask intakes and the 22 replaced tile intakes of the earlier ticket remain in the gitignored quarantine.

Planner question (close-up row 4, right panel): the reddish patch at the top right is Camp (code 4), not volcanic. Camp is `crisp`, so it neither gives nor takes a fringe: the road/camp boundary is correctly straight. Checked with `borderOverlays` on the crop (cols 22-28, rows 4-7): the only overlays are mountain (rank 13) fringing onto road cells (27,6) outer corner and (27,7) west edge; volcanic (code 21) is not in that crop. Expected behaviour, no bug.

## Test Summary
`tests/visual_assets` 1541 passed (foreground, 2 GB cap); `vitest src/visualAssets` 213 passed; `tsc -b` and `eslint src/visualAssets` clean; `draft verify` ok; catalog `verify` ok; render match 31/31.

## Files Changed
visual_assets/drafts/terrain-v1/ (9 mask entries, draft_set.json); frontend/src/visualAssets/{borderRender.ts,DraftHarness.tsx,__tests__/borderRender.test.ts,__tests__/draftHarness.test.tsx}; tests/visual_assets/{test_border_masks.py,test_terrain_draft_set.py,set_colour_vision.py}; docs/assets/pilot_terrain_m5_criteria.md (contract v1 details); agent-working/.

## Completion Summary
The nine border masks are kept in `terrain-v1` beside the 22 re-tinted tiles, so one `adopt-set` covers both; they match the store's own Aseprite render (31/31); the preview page draws borders with an on/off toggle; evidence stored; AM5-S unchanged; nothing adopted. Next is the owner gate: the user reviews the whole map with borders and runs `adopt-set` themselves.
