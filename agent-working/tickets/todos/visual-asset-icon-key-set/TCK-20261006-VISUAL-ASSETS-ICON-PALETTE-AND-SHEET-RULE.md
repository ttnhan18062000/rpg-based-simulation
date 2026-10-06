---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE
phase: open
date: 2026-10-06
tags: [architecture, testing, hud]
---

# TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE

## Title
An icon palette from the terrain colours, and a sheet-level colour-vision and shape rule predeclared before any icon art

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. The user chose a palette based on terrain-v1 plus ramps and a small accent set, checked across the
whole sheet. `lint_sprite`'s `value_separation` only checks inside one sprite; nothing checks that two tiers, two
states or a buff/debuff pair differ by more than hue. As with AM5-S, the rule must be fixed before the art exists.

## Scope
- **Palette:** a committed palette file (format the drawing tools can load, e.g. for `remap_palette`) derived from the
  adopted terrain-v1 colours (exact RGB, verified; not Aseprite's palette-from-sprite) plus 3-4 step ramps
  (`make_ramp`) and an accent set (at most 8 colours) for tiers and statuses. Record its derivation.
- **Check:** a deterministic, tested function next to `tests/visual_assets/set_colour_vision.py` (reuse its Machado
  simulation, Lab and CIE76 code; no copy) over a set of icon sprites and named **must-differ groups** (the 8 tiers;
  buff vs debuff frame; plate+glyph vs the darkest and brightest terrain tiles).
- **Rule (proposed; the user approves or changes it by blocking question before it is written down as fixed):**
  - I1 shape: within each must-differ group, every pair differs in alpha silhouette (1-bit) by at least N pixels
    (proposal: 4 at 8x8, 8 at 16x16) — the non-hue cue.
  - I2 value: in greyscale and each of protan/deutan/tritan, every pair's mean-luma or dE difference is at least a
    threshold (proposal from a measured baseline on synthetic sprites).
  - I3 marker contrast: plate outline vs every terrain-v1 tile has L* difference >= threshold in all four visions.
  Thresholds are proposals; the user's answer governs. Write the rule into a new dated section of a criteria doc
  (`docs/assets/icon_criteria.md`).

## Out of Scope
- Drawing icons (child 5). Changing AM5-S or terrain-v1.

## Acceptance Criteria
- [ ] The rule recorded with the user's own answer and date, committed before any icon art in this batch.
- [ ] Check tested: an identical-silhouette pair fails I1, a recoloured-only pair fails I1, a shape-distinct pair
      passes; an I2 boundary; an I3 low-contrast plate fails; deterministic.
- [ ] Mutant proof: drop a vision from the loop or the I1 threshold and a test fails for the right reason.
- [ ] Palette file committed; its colours traced to the terrain-v1 sources.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE (pattern)

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md (AM5-S), docs/assets/pixel_art_technique.md (rules 3, 11)

## Related Stored Artifacts


## Related Code Areas
- tests/visual_assets/set_colour_vision.py, tests/visual_assets/pilot_colour_vision.py, visual_assets/drawing/technique

## Assumptions / Open Questions
- I1's pixel thresholds are guesses until measured on synthetic sprites; measure first, then ask.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

