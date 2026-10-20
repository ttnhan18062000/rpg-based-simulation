---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001
phase: open
date: 2026-10-19
tags: [architecture, testing]
---

# TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001

## Title
`icon_lookalikes.all_icon_sprites()` returns r0001 art for the 7 revised icon keys; find which consumers mean "adopted now" and point them at the current art

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by asset-implementer on 2026-10-19 in `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`. The entity silhouette sheet took its comparison glyphs from `icon_lookalikes.all_icon_sprites()`, and it showed `icon.item.tool` as the pre-D21 wrench. The adopted `item.tool` is r0002 (hammer and tongs, adopted 2026-10-08), and so is `class.rogue`. The sheet fixed itself by overlaying `icon_owner_fixes_draft_set.proposed_sprites()`. Several consumers use the r0001 art on purpose (`old = ...`, `before = ...` in `tests/visual_assets/test_icon_compliance.py` and `visual_assets/review/icon_compliance.py`). Others may mean "the art adopted now" and so check stale art: `tests/visual_assets/test_icon_recognition.py:13`, `tests/visual_assets/test_icon_lookalikes.py:55`, `tests/visual_assets/test_icon_silhouette_sheet.py:27,39` and `visual_assets/review/icon_compliance.py:253,314,497`.

## Scope
- Classify every consumer as "r0001 on purpose" or "means the current adopted art", with file:line.
- Add one accessor for the current adopted art (r0001 overlaid with the adopted revisions), with a name that says so, and point the "current" consumers at it. Leave the on-purpose r0001 consumers on the old accessor; rename it if that makes its meaning clear.
- A test pins that the current accessor equals the store's adopted pixels for every icon key.

## Out of Scope
- No redraw, no adoption, no registry change.

## Acceptance Criteria
- [ ] The consumer classification is in investigation.md.
- [ ] The current-art accessor exists and is pinned against the store's adopted pixels by a test.
- [ ] The tests that change still pass (scoped `tests/visual_assets/`, after asking lead for a slot).

## Related Tickets
- `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS` (where it was found)
- the icon owner-fixes batch (r0002 revisions, adopted 2026-10-08)

## Related Docs
- `docs/assets/icon_style_guide.md` (D21, the item.tool row)

## Related Stored Artifacts
- None yet

## Related Code Areas
- `visual_assets/review/icon_lookalikes.py`, `visual_assets/review/icon_owner_fixes_draft_set.py`, `visual_assets/review/icon_compliance.py`, `tests/visual_assets/test_icon_*.py`

## Assumptions / Open Questions
- Is a guarded file in scope? The visual_assets conftest is guarded, but these modules are not. If the fix touches a guarded file, it needs the Aseprite proof refresh.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
