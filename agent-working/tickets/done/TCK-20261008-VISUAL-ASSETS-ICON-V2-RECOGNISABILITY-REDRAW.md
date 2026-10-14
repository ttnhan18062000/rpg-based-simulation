---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW
phase: done
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW

## Title
Run the recognisability checks on icons-v2 and redraw every flagged icon to its spec, the weapon sword included, before the owner gate

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 4c of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. With child 4b's specs and checks committed, fix what they flag. The weapon sword is flagged by the owner already. At the owner gate of `icons-v2` the user found the weapon sword "kinda weird" (a short 4 px blade, a lumpy grip
wider than the guard, no pommel: reads as a cleaver, and it nearly duplicates the rogue dagger) and asked for the root
cause. Planner analysis (2026-10-08): every gate measures **distinguishability** (I1 shape, I2 value, I3 contrast, lint),
none measures **recognisability**. Four misreads in 36 icons all passed every gate: the debuff frame (a smile), the shrine
(a bell), the ruins (a boot), the sword (a cleaver). Causes: one-word glyph specs with no proportions; drawing from
memory with no reference study; a design loop that optimised the rule numbers; no cross-family comparison; agent eyeballing
of tiny pixel art is unreliable (the implementer and the planner both passed the sword). The user chose (blocking
question, 2026-10-08) **"Fix the process now"**: build the checks in this batch, run them on the 22 v2 icons, redraw what
they flag, then the owner gate.

## Scope
- Redraw the sword to its spec and every icon the recognition check or the look-alike report flags (report-only
  findings: the planner decides which are redrawn). `draft keep --replace` per slot; intakes via the worktree CLI.
- Re-run the sheet rule (thresholds unchanged), the recognition check and the look-alike report on the full set; record
  before/after per redrawn icon in `docs/assets/icon_set_v2_review.md`; refresh the fixture and the draft set hash in
  the adopt-set template.
- If a family convention changes (e.g. weapons upright), list every icon it touches and redraw those too.

## Out of Scope
- Adopted key-set pixels (a finding there is reported to the owner only). Wiring.

## Acceptance Criteria
- [x] Every flagged icon redrawn or explicitly kept by the planner with a reason; the sword redrawn. (Six redrawn; the dagger kept per the planner's bar; the adopted buff, debuff and tiers B, D, E report-only. The ruins are redrawn but still flagged in free text: see the findings.)
- [x] Sheet rule PASS, recognition re-run recorded, look-alike report re-run recorded.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Related Docs
- docs/assets/icon_set_v2_review.md (redraw section, compliance tables, blind rounds), docs/assets/icon_style_guide.md (process rule step 5)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW/ (plan, investigation, test_plan, mutant_proof.txt, compliance_before.md, compliance_after.md, rule_result_before/after.json, lookalike_before/after.json, blind_check/, drawing/)

## Related Code Areas
- visual_assets/drafts/icons-v2/, frontend/src/visualAssets/__fixtures__/icondraft_v2/, visual_assets/icons/icon_specs.yaml, tests/visual_assets/{icon_compliance,test_icon_compliance,icon_specs,icon_recognition}.py

## Assumptions / Open Questions


## Implementation Notes
- **Process:** added step 5 (spec compliance table) to the style guide's process rule with the reason (the sword passed naming), and `tests/visual_assets/icon_compliance.py`, which measures each spec proportion from the pixels. It found a bug in its own sword measure on a planted wide-grip case (fixed, pinned).
- **Specs revised before drawing:** the tool family is a wrench (the catalog's tool items are a repair kit and a spirit lantern); ruins a ruined brick wall; trinket a teardrop chain loop with a bail ring and a round pendant; ranger a longbow (vertical, curved limbs, pulled string, no stock); sword 20 px upright with a 12 px blade, 12 px guard, 2 px grip and a pommel; common bead 7 px round. The distractor check now shares the whole-word rule with the scoring ("crossbow" is a distractor for the ranger, not a correct answer).
- **Redraws:** six icons, local prototypes first (several design-loop changes from looking at renders: the ruins four times, the first wrench head was a blob, the first pendant read as a bottle), then the drawing API, worktree CLI intakes and `draft keep --replace` per slot. The dagger was kept (the sword's nearest neighbour is now the shrine at 101 XOR px, the dagger's the wrench at 160).
- **Results:** sheet rule PASS unchanged thresholds (rarity I2 min 9.6, rarity vs tier 9 / 16 / 8 px); every compliance row met on the committed drafts (before the redraw the old art failed them); look-alike report re-run (the sword and dagger twin gone; new pair: common bead vs tier D and E at 25 XOR px); blind check re-run twice on all 36 (rounds A and B). Final round: sword, trinket, tool, ranger and bead name correctly in free text; the **ruins are still flagged** ("grey building blocks"; the choice pass names the wall) after four ideas; the check is noisy (unchanged icons flip between rounds). One synonym ("archway") was added after seeing a correct answer scored as a miss, recorded.
- Fixture `icondraft_v2/` refreshed (guard identical), draft set hash and adopt-set template updated in the review doc.


## Test Summary
- `pytest tests/visual_assets tests/docs tests/static`: 1817 passed, 2 skipped, 1 xfailed; `vitest run src/visualAssets`: 261 passed; `tsc` and `eslint` clean. New: `test_icon_compliance.py` (6). Mutants A to D (D first survived, then a planted slope wall caught it).


## Files Changed
- visual_assets/drafts/icons-v2/ (six slots replaced), frontend/src/visualAssets/__fixtures__/icondraft_v2/, visual_assets/icons/icon_specs.yaml, tests/visual_assets/{icon_compliance,test_icon_compliance,icon_specs,test_icon_specs,icon_recognition,test_icon_recognition}.py, docs/assets/{icon_style_guide,icon_set_v2_review}.md, ticket and stored artifacts.


## Completion Summary
Six icons (sword, ruins, trinket, tool, ranger, common bead) were redrawn to measured specs; the sheet rule passes with thresholds unchanged, every compliance row is met, and the blind check now names the sword, pendant, wrench, bow and bead; the ruins are still flagged in free text after four ideas, and the common bead now looks close to the dark tier badges in the look-alike report. Both are in the review doc for the owner.

