---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS
phase: open
date: 2026-10-07
tags: [architecture, testing, hud]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS

## Title
Extend the icon sheet rule to the v2 groups, with a 24x24 shape threshold answered by the user before any art

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. `tests/visual_assets/icon_sheet_rule.py` has I1 thresholds for 8x8 (3 px) and 16x16 (6 px) only;
a 24x24 group raises an error by design. v2 has 24x24 groups (buildings, classes, item families), new 8x8 (rarity)
and 16x16 (location glyphs) groups. The rule must cover them before art exists.

## Scope
- New must-differ groups: the 3 rarity badges; rarity vs tier badges (every rarity differs from every tier by I1);
  the 6 location glyphs (enemy camp + 5); the 6 buildings; the 4 classes; the item families. I2 applies within each group.
- **24x24 I1 threshold:** measure on synthetic sprites (as child 3 of the key-set batch did), propose, and ask the user
  by blocking question with the numbers (neutral options, ascending). Do not reuse 16x16's number by scaling without asking.
- Record in `docs/assets/icon_criteria.md` (a dated v2 section; the key-set answers unchanged). Tests and mutants as before.

## Out of Scope
- Changing the user's existing thresholds (I1 3/6, I2 6, I3 12). Art.

## Acceptance Criteria
- [ ] 24x24 threshold recorded with the user's answer and date, committed before any v2 art.
- [ ] New groups tested (a recolour pair fails, a boundary at the new threshold); mutant proof.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE (precedent)

## Related Docs
- docs/assets/icon_criteria.md

## Related Stored Artifacts


## Related Code Areas
- tests/visual_assets/icon_sheet_rule.py, icon_sheet_synthetic.py, test_icon_sheet_rule.py

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

