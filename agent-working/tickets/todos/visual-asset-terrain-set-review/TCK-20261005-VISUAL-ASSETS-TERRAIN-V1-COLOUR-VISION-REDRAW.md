---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW
phase: open
date: 2026-10-05
tags: [architecture, mcp, live-map]
---

# TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW

## Title
Redraw the terrain-v1 drafts that fail the set colour-vision rule, and re-measure

## Status
OPEN

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
- Redraw only the drafts that appear in a failing pair-vision of the baseline (expected: `dungeon_entrance` first, then
  farmland or grassland, desert or ruins, volcanic for the forest pair; the baseline decides, not this list).
- Same method as the set (the generator in the draft-set ticket's stored artifacts, or the drawing tools): same palette
  family and light direction, 16 x 16, seamless repeat, each tile's mean stays a faithful stand-in for its flat fill
  (the fallback is the fill; state the mean-to-fill distance for each redrawn tile).
- Replace through `store intake` then `draft keep --set terrain-v1 --replace`; `draft verify` and catalog `verify` clean.
- Re-run the committed check; record the result as measured. If a pair cannot pass without breaking fill
  faithfulness, stop and tell the planner (it may be a rule question for the user), never loosen the rule here.
- Fresh preview-page screenshot and 2 x 2 repeat sheet of the redrawn tiles as evidence.

## Out of Scope
- Forest's adopted slots (never redrawn). Adoption, `adopt-set`, releases. Tiles that pass (not touched).
- Changing the rule, the thresholds or the flat fills.

## Acceptance Criteria
- [ ] Every redrawn draft replaced via `--replace`; `draft verify` and catalog `verify` clean; nothing adopted.
- [ ] Set check result after the redraw recorded as measured, with the before/after pair table.
- [ ] Each redrawn tile: seamless repeat shown, mean-to-fill distance stated.
- [ ] `test_terrain_draft_set.py` still passes unchanged in intent (22 drafts, nothing adopted).

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

## Test Summary

## Files Changed

## Completion Summary
