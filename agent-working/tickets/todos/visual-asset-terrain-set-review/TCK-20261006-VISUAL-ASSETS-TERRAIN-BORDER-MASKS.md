---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS
phase: open
date: 2026-10-06
tags: [architecture, mcp, live-map]
---

# TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS

## Title
Draw the shared border masks, keep them in terrain-v1, and show the whole map with borders on the preview page

## Status
OPEN

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
- [ ] Masks kept in `terrain-v1`; `draft verify`, catalog `verify` clean; the 4 px cap test passes on every mask.
- [ ] Preview page shows borders with an on/off toggle; screenshots stored.
- [ ] `AM5-S` still PASS (or the change is reported as measured).
- [ ] Nothing adopted.

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

## Test Summary

## Files Changed

## Completion Summary
