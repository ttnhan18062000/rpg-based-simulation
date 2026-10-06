---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET
phase: open
date: 2026-10-07
tags: [architecture, hud, testing]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

## Title
Draw icon set v2 as draft set icons-v2 against the adopted key set, extend the icon preview page, record the rule result

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. Draw every v2 key in the style the owner adopted (`icons-key-v1`, `docs/assets/icon_style_guide.md`,
palette `icons-v1`), following child 1's glyph choices.

## Scope
- Aseprite MCP tools, own pixels, palette `icons-v1` only, no outside art copied, no AI generators. Submit intakes from
  the WORKTREE CLI (the MCP server runs from the main checkout; see the key-set batch). Keep as draft set `icons-v2`.
- Prototype against the fixed rule before drawing is allowed (design feedback); thresholds never move.
- Extend `rehearsal-icons.html` / `IconHarness` to show v2 next to the adopted key set (one contact sheet per family,
  1x and 2x, dark and light panels, fallbacks), location glyphs on the plate over darkest and brightest terrain,
  rarity next to tier badges, the colour-vision columns labelled as approximation, and the recorded rule result.
- Run the rule; record as measured. A FAIL is reported to the planner before any redraw.
- Review doc `docs/assets/icon_set_v2_review.md` with honest findings and the adopt-set template (licence a placeholder);
  remind the owner that `adopt-set` needs their own terminal (no TTY refusal) and the preview URL `http://[::1]:5173/rehearsal-icons.html`.

## Out of Scope
- Adoption, wiring, any change to the adopted key set's pixels.

## Acceptance Criteria
- [ ] Every v2 key drafted in `icons-v2`; lint and rule recorded.
- [ ] Preview page shows every view; the owner has the commands.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS, TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC, TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS, TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET (precedent)

## Related Docs
- docs/assets/icon_style_guide.md, icon_criteria.md, icon_key_set_review.md

## Related Stored Artifacts


## Related Code Areas
- visual_assets/drafts/, frontend/src/visualAssets/IconHarness.tsx, iconScene.ts, __fixtures__/icondraft/

## Assumptions / Open Questions
- About 24 icons; if drawing reveals that a family's glyph choice cannot pass the rule, stop and ask the planner.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

