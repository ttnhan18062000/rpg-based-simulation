---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE
phase: done
date: 2026-10-05
tags: [architecture, testing, live-map]
---

# TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

## Title
A committed colour-vision check for a whole draft set, with its pass rule and the whole-map M5 scene predeclared before any redraw

## Status
DONE

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
- [x] The rule and the scene criteria are recorded with the user's own answer and date, and written in the criteria doc
      before any `terrain-v1` file changes in this batch.
- [x] Check tested: a known-close pair fails S1, a known-far pair passes, the `>= 10.0` branch, texture below 2.0, forest
      read from its adopted slot; deterministic (same input, same report).
- [x] Mutant proof: drop the `- 2.0` margin or the vision loop and a test fails for the right reason.
- [x] Baseline on `terrain-v1` recorded as measured.

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
User answers (blocking question, 2026-10-05): S1 `dE_tile >= dE_fill - 2.0` or `>= 10`; all 253 pairs; S2 texture >= 2.0; W03 wording adapted to each terrain, all as proposed. Written into
`docs/assets/pilot_terrain_m5_criteria.md` (sections AM5-S and AM5-W03-SET) before any terrain-v1 file was touched (none was). `tests/visual_assets/set_colour_vision.py` reuses the pilot functions;
forest is its adopted `plain` slot, bush/tree are reported only. Wording follows the pilot: PASS iff S1; "better" when S2 also holds.

## Test Summary
`tests/visual_assets/test_set_colour_vision.py` 10 passed; guards (boundaries, no_ignored_files, py311_fstrings, pilot_colour_vision) 278 passed together. Mutants (margin 0, margin 4, one vision, no floor, texture 0) each fail the expected tests.
Baseline on terrain-v1 (stored artifacts `baseline_terrain_v1.txt`): `FAIL`, 30 of 1012 pair-visions fail S1 (worst -7.97 dungeon_entrance/floor protan), S2 holds everywhere, min dE_tile 1.65.

## Files Changed
docs/assets/pilot_terrain_m5_criteria.md; tests/visual_assets/set_colour_vision.py; tests/visual_assets/test_set_colour_vision.py; agent-working/ (ticket, stored artifacts, monitoring).

## Completion Summary
Rule and scene criteria fixed with the user's answers and committed first; check built and tested; baseline FAIL recorded as measured, the "before" for the redraw ticket. Not done here: any redraw, adoption, the whole-map scene code itself (its layout is predeclared; the rerun ticket builds it).
