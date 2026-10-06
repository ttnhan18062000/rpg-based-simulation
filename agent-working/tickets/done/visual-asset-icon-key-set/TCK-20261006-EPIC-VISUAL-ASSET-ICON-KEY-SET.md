---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET
phase: done
date: 2026-10-06
tags: [architecture, hud, live-map, planning]
---

# TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET

## Title
Icon key set: research-backed style decision, icon key families, an icon palette and sheet colour-vision rule, integer map zoom, and a key-icon draft set for the owner's adopt-set

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The user (2026-10-06) lifted the asset pause **for icons only** and asked for deep research first (comparable games,
asset packs, styles). Three research reports were produced and synthesised. Research (planner scratchpad, copied into the repo by child 1): `research_games.md`, `research_icon_craft.md`, `research_packs_palettes.md`, `icon_research_synthesis.md`.

User decisions (blocking questions, 2026-10-06, after the research): style **B + tier badges** (16x16 map glyph
  on a shared per-category plate, 24x24 panel icons, an 8x8 tier badge whose shape escalates, status frames that differ
  in shape with up/down chevrons); palette **terrain-v1 base + 3-4 step ramps + a small accent set**, checked sheet-wide;
  outside art **reference only** (recorded as title/author/source/licence), **no AI generators**; map zoom **snaps to
  whole-number scales**.

Today the UI uses Lucide line icons and emoji as placeholders (`BuildingPanel.tsx` BUILDING_ICONS, `ClassHallPanel.tsx`
CLASS_ICONS, `GameCanvas.tsx` LOCATION_TYPE_ICONS); grades E..SSS and loot rarity are shown by colour only (GRADE_COLORS,
RARITY_COLORS), which breaks the project rule "no critical distinction is hue-only".

This batch locks the style with a small **key set** (about 5 icons plus the tier ladder) that the user reviews and adopts
as one set. The rest of the icons and their wiring into the UI panels are a later batch, after adoption.

## Scope
Children (order and gates in `SEQUENCE.md`):
1. `TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION`: research into the repo, ADR D20, an icon style guide.
2. `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`: register the key set's visual keys with fallbacks.
3. `TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE`: the palette and a sheet-level colour-vision/shape rule,
   user-approved and committed before any icon art.
4. `TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON`: whole-number map zoom; a pixel icon component.
5. `TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`: draw the key set as draft set `icons-key-v1`, preview page, rule result.
6. **Owner gate (no ticket):** the user reviews the preview page and runs `adopt-set` themselves.
7. `TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION` (only if adopted): record the adoption, re-point guards,
   refresh the handoff snapshots, close the batch.

## Out of Scope
- Any `src/` change, simulation or API change. Adoption by an agent (`adopt`, `adopt-set`, `revoke` are the user's).
- The remaining icons (other locations, buildings, classes, item types, statuses, UI tabs) and wiring icons into
  `BuildingPanel`, `ClassHallPanel`, `InspectPanel`, `LootPanel`, `GameCanvas` markers: next batch.
- Entities, buildings as map sprites, animation. Charter signing, AM-M6. Any release candidate.

## Acceptance Criteria
- [ ] All children done or explicitly deferred by the user; `SEQUENCE.md` status line states the outcome.
- [ ] Every gate result recorded as measured (rules never reworded to pass).

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (done; the draft-set + adopt-set + colour-vision-rule pattern)

## Related Docs
- docs/architecture/visual_asset_foundation_adr.md (D11, D12, D17, D19), docs/assets/store_contract.md, docs/assets/pixel_art_technique.md, docs/assets/fallback_safety.md, docs/assets/pilot_terrain_m5_criteria.md (AM5-S)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE/

## Related Code Areas
- visual_assets/, tests/visual_assets/, frontend/src/visualAssets/, frontend/src/components/GameCanvas.tsx

## Assumptions / Open Questions
- Each child is re-checked against what actually landed before it starts.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

