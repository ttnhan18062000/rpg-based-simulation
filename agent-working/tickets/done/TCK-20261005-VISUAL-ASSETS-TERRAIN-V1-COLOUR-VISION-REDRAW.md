---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW
phase: done
date: 2026-10-05
tags: [architecture, mcp, live-map]
---

# TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW

## Title
Redraw the terrain-v1 drafts that fail the set colour-vision rule, and re-measure

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Second child of `TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW`. With the rule fixed and the baseline recorded by
`TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE`, redraw the drafts behind the failing pair-visions so the set can be
reviewed and adopted as a whole.

## Scope
- **Planner decision, 2026-10-05 (not a user rule): re-tint all 22 drafts**, mean-to-fill target about 0, with the same designs. Reason, from subset enumeration: no subset of the 16 tiles that
  appear in failing pair-visions passes (correcting all 16 leaves shallow_water/wall failing; 17 still fails), because every corrected tile moves the pairs it drifted with. Only all 22 passes.
- Method: keep each tile's drawing; shift every pixel that uses the tile's own five ramp colours (d2 d1 b l1 l2) by one RGB offset so the 16 x 16 mean equals the flat fill. Accents, texture and light direction
  unchanged. The generator change (offset rule) is committed in the stored artifacts so the result is reproducible.
- Report for each tile: old and new mean-to-fill dE, any channel clipped at 0 or 255 and the resulting mean-to-fill (list any tile still above about 1 dE), and S2 texture after the shift.
- Replace through `store intake` then `draft keep --set terrain-v1 --replace`; `draft verify` and catalog `verify` clean; nothing adopted.
- Re-run the committed check; record the result as measured, with the before/after pair table. If it still fails, stop and tell the planner; never loosen the rule here.
- Evidence for the user's review: a before/after sheet of all 22 (old and new preview side by side), the new 2 x 2 repeat sheet and a fresh preview-page screenshot (watch dungeon_entrance's opening and farmland).
- Result wording (here and in child 4): with mean == fill, S1 holds by construction (`dE_tile == dE_fill`), so a PASS means "no worse than the flat fills", nothing more; the tiles add only the S2 texture cue.
  Keep the pilot's caveat that the flat-fill baseline is hue-only and not colour-vision safe.

## Out of Scope
- Forest's adopted slots (never redrawn). Adoption, `adopt-set`, releases. 
- Changing the rule, the thresholds or the flat fills.

## Acceptance Criteria
- [x] Every redrawn draft replaced via `--replace`; `draft verify` and catalog `verify` clean; nothing adopted.
- [x] Set check result after the redraw recorded as measured, with the before/after pair table.
- [x] Each redrawn tile: seamless repeat shown, mean-to-fill distance stated.
- [x] `test_terrain_draft_set.py` still passes unchanged in intent (22 drafts, nothing adopted).

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md (the set rule), docs/assets/store_contract.md (draft sets)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/ (tile_generator.py, style note in the ticket)

## Related Code Areas
- visual_assets/drafts/terrain-v1/, visual_assets/store/drafts.py (`--replace`)

## Assumptions / Open Questions
- Old replaced drafts: `draft keep --replace` removes the old entry after the new record is in place; say what remains
  in the gitignored quarantine.

## Implementation Notes
Planner decision 2026-10-05 (not a user rule): all 22 re-tinted, because no subset passes (see Scope). `tile_retint.py` (stored artifacts) applies one RGB offset to each tile's own ramp pixels, refined against 8-bit rounding and clipping; `retint_draw.py` draws via the library and packages handoffs; each went through `store intake` and `draft keep --set terrain-v1 --as <key> --replace` (22 PASSED intakes, forest untouched, nothing adopted).
Old and new mean-to-fill per tile: `retint_report.txt` (all now <= 0.62 dE; lava 13.1 -> 0.40 and snow 1.41 -> 0.14 had a clipped channel, resolved by the refine loop; none above 1 dE). Texture after the shift: min L* std 5.36 (graveyard); dungeon_entrance 9.6 -> 11.8, farmland 14.7 -> 17.4.
Set check after (`after_terrain_v1.txt`): **PASS**, 0 of 1012 pair-visions fail S1, S2 holds for every tile and vision (before: FAIL, 30 failing). Honest reading: with mean == fill, S1 holds by construction (dE_tile == dE_fill within rounding, worst margin -1.3), so the PASS means "no worse than the flat fills", nothing more; the tiles add only the S2 texture cue. The flat-fill baseline is hue-only, not colour-vision safe. The forest bush/tree closeness (protan 1.3-1.8 dE to other tiles) is unchanged and informational.
Visual risk for the user's review: dungeon_entrance (opening) and farmland (largest offsets, +26.6 red and +32.1 green); the before/after sheet shows the drawings and palette family unchanged.
Left in the gitignored quarantine: the 22 replaced intakes; workspace sprites `tdraft_<name>_a` and the new `_b` stay in the local cache.

## Test Summary
`draft verify`: drafts ok; catalog `verify`: store ok; `tests/visual_assets`: 1533 passed (foreground, 2 GB cap), `test_terrain_draft_set.py` unchanged. Set check re-run: PASS (0/1012 failing), recorded with the before table of the rule ticket.

## Files Changed
visual_assets/drafts/terrain-v1/ (22 entries replaced, draft_set.json); agent-working/ (ticket, stored artifacts incl. tile_retint.py, retint_draw.py, make_sheets.py, retint_report.txt, after_terrain_v1.txt, before_after_sheet.png, repeat_sheet_after.png, terrain_v1_preview_page_after.png).

## Completion Summary
All 22 terrain-v1 drafts re-tinted to their flat fills with the same designs and replaced; `draft verify` and `verify` clean; nothing adopted; set check PASS under the approved rule with the honest wording above. The set (draft set hash sha256:87a8cc8d62c7...) is ready for the owner's review on the preview page and `adopt-set`.
