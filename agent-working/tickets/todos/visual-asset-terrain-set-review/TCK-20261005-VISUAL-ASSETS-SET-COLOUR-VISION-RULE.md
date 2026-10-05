---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE
phase: open
date: 2026-10-05
tags: [architecture, testing, live-map]
---

# TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

## Title
A committed colour-vision check for a whole draft set, with its pass rule and the whole-map M5 scene predeclared before any redraw

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
First child of `TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW`. The pilot's `W05` check
(`tests/visual_assets/pilot_colour_vision.py`) is defined for one tile against five named neighbours. The draft-set ticket
reused its functions in a scratch run over all terrain pairs and found 30 tight pair-vision cases, with an ad hoc
"under dE 10" filter and no committed rule. Before anything is redrawn, the rule the redraw and the M5 rerun are judged by
must be fixed, approved and committed, so it cannot be tuned to the result.

## Scope
- **Check:** a deterministic, tested function next to `pilot_colour_vision.py` (reuse its Machado simulation, Lab and
  CIE76 code; no copy) that, for a draft set plus adopted reference slots, computes for every unordered terrain pair and
  each vision (normal, protan, deutan, tritan): `dE_tile` between the two tiles' mean colours, `dE_fill` between the two
  flat fills (`TILE_COLORS`, the asserted copy), and each tile's L* texture. Forest uses its adopted `plain` slot; its
  bush/tree slots are reported too.
- **Rule (proposed; the user approves or changes it by blocking question before it is written down as fixed):**
  - S1 (no worse, per pair-vision): `dE_tile >= dE_fill - 2.0`, or `dE_tile >= 10.0` (two tiles at least 10 apart stay
    told apart even if the fills were further apart).
  - S2 (texture cue): every tile `texture >= 2.0` in every vision.
  - Set result `PASS` if S1 holds for every pair-vision; `FAIL` naming every failing pair-vision otherwise. "better" /
    "same" as in the pilot rule. Same honesty note as the pilot: the flat-fill baseline is hue-only, not colour-vision safe.
  - Ask the user also: all 253 pairs (proposed: yes, conservative and layout-free) or only pairs that can neighbour.
- **Whole-map scene for the M5 rerun:** predeclare in `docs/assets/pilot_terrain_m5_criteria.md` (new dated section, the
  pilot sections unchanged) a deterministic layout using every Live Map terrain code with forest cells mixing
  plain/bush/tree through `pickDetail`, its image and flat-control canvases, and the W03 criteria C1-C5 adapted to "each
  terrain" (wording approved by the user in the same blocking question as the rule, or a second one).
- **Baseline:** run the committed check on today's `terrain-v1` and record it (expected `FAIL`; it replaces nothing,
  it is the "before" for child 2). Store output in this ticket's stored artifacts.

## Out of Scope
- Redrawing any tile (child 2). Adoption. Changing the pilot's W05 rule or its recorded result.
- An assistive-technology claim.

## Acceptance Criteria
- [ ] The rule and the scene criteria are recorded with the user's own answer and date, and written in the criteria doc
      before any `terrain-v1` file changes in this batch.
- [ ] Check tested: a known-close pair fails S1, a known-far pair passes, the `>= 10.0` branch, texture below 2.0, forest
      read from its adopted slot; deterministic (same input, same report).
- [ ] Mutant proof: drop the `- 2.0` margin or the vision loop and a test fails for the right reason.
- [ ] Baseline on `terrain-v1` recorded as measured.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md (W05 pilot rule, the pilot scene), docs/assets/pilot_terrain_m5_results.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/cvd_pairs.txt

## Related Code Areas
- tests/visual_assets/pilot_colour_vision.py, tests/visual_assets/test_pilot_colour_vision.py,
  frontend/src/visualAssets/terrainDrafts.ts (TERRAIN_DRAFT_KEYS), visual_assets/drafts/terrain-v1/

## Assumptions / Open Questions
- Thresholds 2.0 / 10.0 are proposals from the scratch run, not decided; the user's answer governs.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
