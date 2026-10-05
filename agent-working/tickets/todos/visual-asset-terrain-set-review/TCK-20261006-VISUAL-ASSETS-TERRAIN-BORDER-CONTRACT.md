---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT
phase: open
date: 2026-10-06
tags: [architecture, live-map]
---

# TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT

## Title
Layered terrain borders: a priority order, a shared fringe-mask key family and a pure client compositor (contract and code, no final art)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Third child of `TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW`. Reviewing `terrain-v1` on the preview page on
2026-10-06, the user found that the borders between different terrains "look weird": each 16 px cell is one terrain,
so textures stop abruptly along square, stair-stepped edges. The user chose, by blocking question, the layered
fringe approach used by Battle for Wesnoth (each terrain has a layer; where two meet, the higher one draws a ragged
fringe of its own texture onto the lower one), with **one shared set of mask shapes** applied to every terrain's own
texture, so there is no per-pair art. The user also chose to hold `adopt-set` until borders exist and to review the
whole map once, with borders.

## Scope
- **Priority order (user approves by blocking question before it is fixed):** propose one total order over the 23
  terrain codes, and a short rule for it (proposal: liquids and voids lowest (water, shallow_water, lava, floor, cave),
  then ground (desert, farmland, grassland, snow, swamp, volcanic, road...), then vegetation (forest, jungle), and the
  built/hard-edged codes (wall, town, bridge, ruins, dungeon_entrance, camp, sanctuary, graveyard) marked
  **`crisp`**: they neither draw a fringe nor receive one, so they keep a clean edge, like walls in most tile games).
  Equal priority never happens (total order). Write it in the criteria doc's new dated section and in code as one table.
- **Compositor (pure, client):** `borderOverlays(codeAt, x, y, order, masks)` returns, for a cell, the ordered list
  `(neighbourCode, maskId, rotation)` to draw over the cell's base tile: for each of the 4 sides and 4 diagonal
  corners whose neighbour ranks higher (and neither is `crisp`), the matching edge or outer-corner mask; when two
  adjacent sides share the same higher neighbour, an inner-corner mask instead of two edges. The fringe's pixels are
  the neighbour tile's pixels at the same in-cell coordinates (tiles repeat seamlessly, so the fringe continues the
  neighbour's pattern). Draw order: lower-ranked neighbours first. Variant pick per mask through `pickDetail`'s hash
  (same FNV-1a contract, a separate key string), so borders are deterministic per `(x, y)`.
- **Masks as assets:** a new registered key family, proposed `border.edge`, `border.outer_corner`,
  `border.inner_corner`, each a 16x16 1-bit alpha shape authored for one orientation (north, north-east), rotated by the
  client in 90-degree steps, with a `detail` axis for 2-3 variants. Masks are art through the normal store gates
  (intake, draft set, adopt-set), not code constants. Record in an ADR row and `store_contract.md`. Check that draft
  sets accept a non-terrain family in `terrain-v1` (or say what is needed); tell the planner before building if not.
- **Fallback:** a missing mask means no fringe for that side (today's hard edge); classify borders as `decorative`
  under `docs/assets/fallback_safety.md`. The role's preserved fact ("this cell is X") is never changed: a fringe covers
  at most the outer 4 px of a cell (cap enforced in the compositor and checked on every mask at intake time by a test),
  so the cell centre always shows its own terrain.
- **Criteria (user approves in the same or a second blocking question, before any mask art):** a new dated section in
  `docs/assets/pilot_terrain_m5_criteria.md` adding `C6 borders` to `AM5-W03-SET` ("where two terrains meet, the
  border reads as a natural transition or a clean built edge, not as a cut or a glitch") and stating that the
  `AM5-S` rule is unchanged (it measures tile means; fringes are outside it, stated as such).
- Test-only placeholder masks (generated in the test, never committed as assets) to exercise the compositor.

## Out of Scope
- Final mask art (next ticket). Adoption. Live Map changes. Per-pair transition tiles. Animated borders.
- Changing tiles, the fills, the `AM5-S` rule or the approved W03-SET criteria C1-C5.

## Acceptance Criteria
- [ ] Priority order and `crisp` set approved by the user (own answer, dated), written in the criteria doc and as one code table with a test equal to the doc.
- [ ] C6 approved and recorded in a new dated section; C1-C5 and `AM5-S` unchanged.
- [ ] Compositor tests: no overlay between equal codes; higher-ranked neighbour fringes onto lower only; `crisp` neither gives nor takes; inner corner replaces two edges; draw order; same `(x, y)` gives the same overlays every run; a missing mask gives no overlay; the 4 px cap holds.
- [ ] Mutant proof: reverse the order comparison, or drop the `crisp` check, and a test fails for the right reason.
- [ ] Mask key family registered (optional keys), ADR row and `store_contract.md` updated; catalog `verify` clean.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS (next)

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/store_contract.md, docs/assets/fallback_safety.md,
  docs/architecture/visual_asset_foundation_adr.md
- Reference: Wesnoth terrain layers and transitions (https://wiki.wesnoth.org/Terraingraphicswml)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW/terrain_v1_preview_page_after.png (the hard borders the user saw)

## Related Code Areas
- frontend/src/visualAssets/ (terrainDrafts.ts, pickDetail.ts, DraftHarness.tsx), visual_assets/catalog/definitions/visual_keys.yaml,
  visual_assets/store/contracts/

## Assumptions / Open Questions
- The order and `crisp` set are proposals; the user's answer governs.
- The 4 px cap is a proposal (a quarter of the cell); ask with the order if it seems wrong.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
