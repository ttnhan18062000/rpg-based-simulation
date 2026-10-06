---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET
phase: open
date: 2026-10-06
tags: [architecture, hud, testing]
---

# TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET

## Title
Draw the icon key set as draft set icons-key-v1, with a preview page and the sheet rule result, ready for the owner's adopt-set

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 5 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. With the style guide (child 1), keys (child 2), palette and rule (child 3) committed, draw the key
set so the user can judge the style on a few icons before the whole set is drawn.

## Scope
- Draw with the Aseprite MCP tools only, our own pixels (reference-only outside art; record any reference looked at
  as title/author/source/licence in the draft's provenance or notes; no AI generators): every key from child 2.
  Follow `docs/assets/icon_style_guide.md` and `pixel_art_technique.md` (silhouette first, palette from child 3,
  `lint_sprite` clean or every finding explained).
- Keep them as draft set `icons-key-v1` (`draft keep`), the same flow as terrain-v1.
- Preview page (extend the draft harness): contact sheet at 1x and 2x; the location plate+glyph over the darkest and
  brightest terrain-v1 tiles and on a small map scene at whole-number zoom (child 4); the tier ladder in greyscale and
  the three simulated visions next to the colour version; buff/debuff pair likewise; each icon beside its fallback.
- Run child 3's check; record the result as measured. A FAIL is reported, not tuned away (redraw only with the
  planner's say-so).
- Hand the user the exact `adopt-set` command (absolute venv interpreter path) and the preview command; then wait.

## Out of Scope
- Adoption. Panel wiring. Any icon outside the key set.

## Acceptance Criteria
- [ ] Every child-2 key has a draft in `icons-key-v1`; `lint_sprite` results recorded.
- [ ] Sheet rule result recorded as measured (I1-I3).
- [ ] Preview page shows every view listed in Scope; the user has the commands.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION, TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES, TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE, TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

## Related Docs
- docs/assets/icon_style_guide.md, docs/assets/icon_criteria.md (after children 1 and 3)

## Related Stored Artifacts


## Related Code Areas
- visual_assets/drafts/, visual_assets/store/drafts.py, frontend/src/visualAssets/DraftHarness.tsx

## Assumptions / Open Questions
- If the draft harness assumes 16x16 tiles, extending it for 24 and 8 is in scope; report the size of that change to the planner first.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

