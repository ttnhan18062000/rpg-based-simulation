---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS
phase: done
date: 2026-10-07
tags: [architecture, testing, hud]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS

## Title
Extend the icon sheet rule to the v2 groups, with a 24x24 shape threshold answered by the user before any art

## Status
DONE

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
- agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS/ (plan, investigation, test_plan, baseline_measurements.txt, mutant_proof.txt)

## Related Code Areas
- tests/visual_assets/icon_sheet_rule.py, icon_sheet_synthetic.py, test_icon_sheet_rule.py

## Assumptions / Open Questions
- Resolved by the user's answers (below). Note found while measuring: the real blacksmith vs warrior are only 5.2 L* apart, so the ticket's "I2 applies within each group" would have made ordinary drawings fail by accident; asked the user (answer: I1 only for the subject groups).

## Implementation Notes
- **User answers (blocking question, 2026-10-07, neutral options in ascending order, baselines shown):** I1 at 24x24 = **N = 8** (over 14 and 24); I2 for the four subject groups (locations, buildings, classes, item families) = **I1 only** (over I1 plus I2 at 6). Written into `docs/assets/icon_criteria.md` ("Icon set v2", with the baselines table) before any v2 art.
- **Rule change:** `RULE.shape_min` gains `24: 8` (a size without a threshold still raises `KeyError`; the existing test now proves it with 32); `evaluate_sheet(..., shape_only=...)` skips I2 for the named groups and reports `value_checked: false`. Key-set thresholds (I1 3 and 6, I2 6, I3 12) untouched.
- **Groups (`tests/visual_assets/icon_v2_groups.py`):** `rarity` (3, 8x8, I1 + I2), `badges` (the 3 rarity badges against the 8 tier badges, E and D one class, I1 only: the best 11-step palette ladder is 4.5 L*), `locations` (enemy camp + 5, 16x16), `buildings` (blacksmith + 5), `classes` (warrior + 3), `items` (6 families): all I1 only.
- **Tests (`test_icon_v2_groups.py`, 11 new):** the groups are well-formed and cover every v2 key once; E and D stay together; a recoloured-only pair fails I1 in every group size; boundary at 24x24 (8 passes, 7 fails); an unruled size raises; shape-only groups skip I2 and say so while `rarity` keeps it; a rarity badge with a tier silhouette fails the badge group. Mutants A to D caught (mutant_proof.txt).
- **Baselines (measured before asking; baseline_measurements.txt):** real blacksmith vs warrior 135 px and 5.2 L*; synthetic 24x24 changes of 1, 3, 4, 16 and 36 px; the rarity mock shapes 8 px or more from every tier silhouette (bead and sparkle against the S diamond are the closest); palette ladder capacity N3 35.4 to N11 4.5.

## Test Summary
- `pytest tests/visual_assets`: `pytest tests/visual_assets tests/docs tests/static` all passed (1773 incl. 11 new; the first full run had 3 failures, the icon draft fixture guards, because the recorded rule result gained the additive `value_checked` field: refreshed with `icon_draft_fixture --write`, a diff of only that field); mutants A to D caught. Whole frontend vitest: 332 of 333 in one full run; the one failure, `useSimulation.test.tsx` ("transitions to CONNECTING_LIVE ..."), is code this branch does not touch and passed 3 of 3 re-runs alone and in every earlier full run: a load-dependent flake, reported to the planner, not changed.

## Files Changed
- tests/visual_assets/{icon_sheet_rule,icon_v2_groups,test_icon_v2_groups,test_icon_sheet_rule}.py, docs/assets/icon_criteria.md, ticket and stored artifacts.

## Completion Summary
The 24x24 shape threshold (8 px) and the v2 groups (subject groups I1 only, rarity I1 + I2, rarity vs tier I1 only) are committed with the user's answers before any v2 art.
