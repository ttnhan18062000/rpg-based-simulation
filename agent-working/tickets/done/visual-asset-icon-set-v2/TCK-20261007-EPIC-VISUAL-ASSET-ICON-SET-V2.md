---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2
phase: done
date: 2026-10-07
tags: [architecture, hud, planning]
---

# TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2

## Title
Icon set v2: the remaining location, building, class, rarity and item-family icons as a second draft set for the owner's adopt-set, drawn against the adopted key set, no app wiring

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
After the icon key set (PR #388, `icons-key-v1` adopted, ADR D20) the user asked for the next icon batch. User decisions (blocking questions, 2026-10-07, after PR #388 merged): the next icon batch is **draw only, no
wiring**: using adopted art in the live app is gated (AM-M6 is NO-GO until the owner signs its charter, and AM-M6
covers one forest tile only; HUD icons are broad rollout, beyond it). Families: **map locations (5), buildings +
classes (8), rarity badges (3), item families (~8)**.

The planning brainstorm (`docs/brainstorm/render-and-art/visual-system-planning.md` section 15) sets the bar:
"Do not create an icon merely because an enum exists." Every icon here replaces a placeholder the UI shows today
(emoji, Lucide, or colour only), except item families, which need a mapping decision first.

## Scope
Children (order and gates in `SEQUENCE.md`):
1. `TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS`: item-family mapping, rarity badge ladder, glyph choices; user-approved before any key or art.
2. `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`: register every v2 key in one change; assemble the next release candidate (user approval).
3. `TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS`: extend the sheet rule to the v2 groups, including a 24x24 I1 threshold (user's answer), before any art.
4. `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`: draw draft set `icons-v2`, extend the icon preview page, record the rule result; hand the owner the commands.
5. **Owner gate (no ticket):** the owner reviews and runs `adopt-set` in their own terminal.
6. `TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION` (only if adopted): record the adoption, re-point guards, refresh snapshots, close.

## Out of Scope
- Any import of adopted art into the app (`frontend/src/components/`, `hooks/`, `GameCanvas`, panels); any `src/` change; adoption by an agent; the AM-M6 charter.
- UI tab icons (Lucide stays for chrome), advanced class icons (champion etc.), per-item icons, per-effect status glyphs (the UI shows only buff/debuff), quest/event/faction icons.

## Acceptance Criteria
- [x] All children done or explicitly deferred by the user; `SEQUENCE.md` status line states the outcome.
- [x] Every gate result recorded as measured.

## Related Tickets
- Children (all done): TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS, -KEYS-AND-RC, -SHEET-RULE-GROUPS, -DRAFT-SET, TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS, TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW, TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (done, PR #388: style, palette, rule, key set)

## Related Docs
- docs/assets/icon_style_guide.md, docs/assets/icon_criteria.md, docs/assets/icon_key_set_review.md, ADR D17/D20, docs/assets/pilot_charter_am6.md (why no wiring), docs/brainstorm/render-and-art/visual-system-planning.md (sections 11, 15)

## Related Stored Artifacts


## Related Code Areas
- visual_assets/, tests/visual_assets/, frontend/src/visualAssets/ (preview only)

## Assumptions / Open Questions
- Each child is re-checked against what actually landed before it starts.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
DONE (2026-10-08): the 22 icon set v2 icons were drawn, checked (sheet rule PASS as measured, spec compliance tables, blind recognition check, look-alike report), redrawn where the checks and the planner flagged them, and adopted by the owner (`sa-c9082d078b954f6b`). The batch added the recognisability process (specs, reference study, compliance table, blind check, look-alike report). Nothing is built, released or wired. The branch `visual-asset-icon-set-v2` is not pushed; the user decides.

