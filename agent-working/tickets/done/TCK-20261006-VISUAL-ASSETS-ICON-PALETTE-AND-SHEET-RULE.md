---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE
phase: done
date: 2026-10-06
tags: [architecture, testing, hud]
---

# TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE

## Title
An icon palette from the terrain colours, and a sheet-level colour-vision and shape rule predeclared before any icon art

## Status
DONE

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
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE/ (plan, investigation, test_plan, baseline_measurements.txt, mutant_proof.txt)

## Related Code Areas
- tests/visual_assets/set_colour_vision.py, tests/visual_assets/pilot_colour_vision.py, visual_assets/drawing/technique

## Assumptions / Open Questions
- I1's pixel thresholds are guesses until measured on synthetic sprites; measure first, then ask. Done: baselines measured, one blocking question asked, answers recorded in docs/assets/icon_criteria.md (2026-10-06).
- Resolved by the user's answer: E and D may share a silhouette (classes in a group); I2 measures the interior mean (an 8x8 badge is more than half outline).

## Implementation Notes
- Palette `visual_assets/palettes/icons-v1.json` (52 colours) is exactly `icon_palette.build_palette()` (tested): 23 terrain fills (each checked against its adopted tile, forest 2.42 off), 7 four-step ramps from terrain seeds (`make_ramp`, base_index 1), 8 accents.
- Rule in `tests/visual_assets/icon_sheet_rule.py` (reuses `pilot_colour_vision`); thresholds are the user's answers: I1 3/6 px, I2 L* 6, I3 L* 12; E and D may share a silhouette.
- Finding reported: the style guide's dark-outline policy cannot hold for plates (a dark rim reaches 6.0 L* against the floor tile). The guide's outline row now makes plates the exception (mid-light `plate_rim`).
- Confirmed (planner's question): the numbers the user saw in the blocking question were already INTERIOR-mean numbers (best 8-step ladder 8.74, today's chips 0.25 to 1.6, buff vs debuff 12 to 29). The whole-sprite run (ladder about 1.4, chips 0.06 to 1.6) was measured earlier and never shown, so the user answered the measure the rule uses.
- Mutant C (I3 over normal vision only) was not caught at first; a test was added (see mutant_proof.txt).

## Test Summary
- `pytest tests/visual_assets/test_icon_sheet_rule.py`: 21 passed; whole `tests/visual_assets`, `tests/docs`, `tests/static`: 1708 passed, 2 skipped, 1 xfailed.
- Mutants A-F caught for the right reasons (`mutant_proof.txt`).

## Files Changed
- visual_assets/palettes/icons-v1.json, tests/visual_assets/{icon_palette,icon_sheet_rule,icon_sheet_synthetic,test_icon_sheet_rule}.py, docs/assets/icon_criteria.md, docs/assets/icon_style_guide.md, ticket and stored artifacts.

## Completion Summary
Palette icons-v1 (52 colours, derivation in code) and the sheet rule I1-I3 committed with the user's thresholds (3/6 px, L* 6, L* 12; E and D may share a silhouette) before any icon art. Style guide amended: plates take a mid-light rim.
