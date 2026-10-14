---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES
phase: done
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES

## Title
Owner review fixes before PR #418 merges: ruins, common bead, buff frame, blade motifs and the tool icon, through the recognisability process

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Follow-up to `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`, on the same branch and PR. PR #418 (icon set v2) is CI-green and planner-approved, but the owner held the merge ("Don't merge yet") and then
asked to "finish what blocks the PR". The planner's readiness comment on #418 listed five owner-judgement items; the owner
chose (blocking question, 2026-10-08) to fix ALL of them before the merge: the ruins glyph, the common rarity bead, the
adopted buff frame, and the blade motifs + the unmatched spirit lantern.

## Scope
Follow the style guide's recognisability process for every changed icon, in order:
1. **Specs** (update `visual_assets/icons/icon_specs.yaml`, before drawing). Planner proposals, the owner may change them
   at step 3:
   - `icon.marker.ruins` (v2): a new idea, e.g. a broken stone arch with rubble at its feet.
   - `icon.rarity.common` (v2): a lighter silver-grey round bead with a highlight, so it no longer resembles the dark
     tier E/D badges; the rarity I2 ladder must still pass.
   - `icon.status.frame_buff` (adopted key set): a solid up arrow, the mirror of the redrawn debuff's down arrow, in the
     unchanged round green frame, so it stops reading as a gem.
   - Blades: the sword stays only on `icon.item.weapon`. `icon.class.rogue` (v2) becomes a hooded cowl or mask;
     `icon.marker.enemy_camp` (adopted key set) becomes a tent with crossed spears; `icon.class.warrior` keeps its shield
     (the shield is its silhouette).
   - `icon.item.tool` (v2): a toolbox (covers `repair_kit`; one family icon cannot also depict `spirit_lantern`; say so).
2. **Reference study** per changed glyph (reference only, TASL recorded).
3. **One-colour silhouette sheet** of the changed icons next to their neighbours, shown to the owner on the preview page;
   the owner approves or changes it by blocking question BEFORE any full drawing.
4. **Draw** the approved silhouettes (palette icons-v1, own pixels, worktree CLI intakes).
   - **Corrected (planner, 2026-10-08, on the implementer's report):** ALL six changed slots are adopted sources, because the owner adopted `icons-v2` on 2026-10-08 (the original text said v2 slots go through `draft keep --replace` in `icons-v2`; that would change the draft set the adoption hashed and break `test_the_v2_draft_set_still_hashes_to_what_the_adoption_recorded`). The six new drawings go in a NEW draft set `icons-owner-fixes-v1`; `icons-v2` and `icons-key-v1` stay untouched as history.
   - The store's own route for a new revision of an adopted source is `adopt <intake> --visual-key K --source-asset-id <EXISTING id> --parent r0001` (`adoption.py::_lineage`: the parent must be the latest unrevoked revision; the new revision is r0002), human-only, after `review <intake>`. `adopt-set` cannot do revisions (it only creates new source assets); a store change to allow it is out of scope. Draft source ids are distinct (`..._fix`) because `draft keep` refuses an id that already exists in the catalog; the id the owner types at `adopt` is the existing one.
5. **Checks:** sheet rule (thresholds unchanged), measured spec compliance table, blind recognition check, whole-sheet
   look-alike report; before/after in the review doc. Refresh fixtures and the preview page.
6. Merge origin/main into the branch first (26 commits behind as of 2026-10-08) and keep it current.
7. Hand the owner the preview URL and the exact adopt-set command(s) (own terminal; licence placeholder).

## Out of Scope
- Wiring icons into the app. Changing any user threshold. Icons not listed above.

## Acceptance Criteria
- [x] Specs updated and the silhouette sheet approved by the owner before drawing (answer recorded verbatim).
- [x] Every listed icon redrawn; rule PASS; compliance tables met; blind check and look-alike report re-run and recorded. (After the owner's decision only four are proposed: buff, rogue, tool, common; the ruins and the enemy camp are kept as adopted.)
- [x] The re-adoption route for adopted key-set slots is the store's own, reported before use.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (done; PR #418), TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS (the process)

## Related Docs
- docs/assets/icon_style_guide.md (process rule; the owner-fixes reference study), icon_set_v2_review.md (the owner-fixes section and the 12 commands), icon_key_set_review.md; PR #418 readiness comment

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES/ (plan, investigation, test_plan, mutant_proof.txt, owner_fixes_result.json, lookalike_proposed.json, blind_check/, intakes.json, drawing/)

## Related Code Areas
- visual_assets/icons/icon_specs.yaml, visual_assets/drafts/, visual_assets/store/adoption.py (read), frontend/src/visualAssets/

## Assumptions / Open Questions


## Implementation Notes
- **Owner decision after seeing the six drafts (relayed by the planner, who asked the owner by blocking question on 2026-10-08), answer verbatim: "Keep current versions".** The ruins arch and the spear-tent camp are NOT revised and NOT proposed for adoption (the adopted brick wall and crossed swords stay). Reason: both new drawings still misread in free text (the arch as "document with arrow", the tent as "crossed tools on red mound") and the adopted versions read better. The owner adopts only four revisions: buff frame, rogue, tool, common bead. This was applied by amending the commit: the review doc lists 8 commands (not 12); the two declined drafts stay in `icons-owner-fixes-v1` as never-adopted drafts because the store has no command to drop a draft slot (`draft` has keep, export, verify; hand-editing `draft_set.json` would bypass its record), marked "not proposed for adoption, owner decision" in the doc and on the preview page; the specs for the ruins and the enemy camp are restored to describe the adopted r0001 (their revision entries dropped); the silhouette sheet and the recorded result cover the four. Blade overlap is resolved by the rogue cowl; the crossed swords stay by the owner's choice.
- **Merged origin/main first** (26 behind, clean), and kept the branch current.
- **Route reported to the planner before use** (and approved): new draft set `icons-owner-fixes-v1`, distinct draft source ids (`..._fix`), the owner's `review` then `adopt --parent r0001` per slot (12 commands in the review doc); `adopt-set` cannot make revisions.
- **Specs** (`icon_specs.yaml`, status `revision`) revised before drawing; the style guide gained the owner-fixes reference study (Kenney previews only) and the status `revision`.
- **Silhouette sheet** (`silhouette_proposals.yaml`, `icon_silhouette_sheet.py`, the preview page section): shown to the owner, who answered the blocking question (verbatim answers below). The preview page now also shows each revision beside its adopted drawing, the recorded result and the compliance tables.
- **Owner's silhouette answers (blocking question asked by the implementer, 2026-10-08, after the owner viewed the one-colour silhouette sheet on the preview page), verbatim:** Rogue = "A: hooded cowl"; Enemy camp = "A: tent, spears crossed above"; the other four (ruins broken stone arch with rubble, silver common bead, buff frame with a solid up arrow, toolbox) = "Approve all four". Drawing may start; each drawn icon must keep its approved silhouette exactly.
- **Second owner question (implementer, 2026-10-08), on a defect found by measuring after drawing:** the approved tent broke the style guide's live-area rule for 16x16 glyphs (margins 1, 0, 1 px instead of 2; both tent options did, because of the spears: my proposal's mistake). A fitted version (margins 2, 2, 2, 2) was shown on the silhouette sheet and the owner answered, verbatim: "A fitted: spears crossed above". The first tent drawing (intake `in-69b1de139c71dbe3`) was replaced in the draft set.

## Test Summary
- `pytest tests/visual_assets tests/docs tests/static tests/architecture`: 1963 passed, 2 skipped, 1 xfailed; `vitest run src/visualAssets`: 270 passed; `tsc` and `eslint` clean. Mutants A to D caught (B only after replacing a non-discriminating planted case).


## Files Changed
- visual_assets/drafts/icons-owner-fixes-v1/ (6 drafts), visual_assets/icons/{icon_specs,silhouette_proposals}.yaml, frontend/src/visualAssets/{IconHarness.tsx,iconDraftSource.ts,iconMain.tsx}, __fixtures__/{icondraft_fixes,iconsilhouettes}/, __tests__/{IconHarness,isolation}.test, tests/visual_assets/{icon_compliance,icon_owner_fixes_draft_set,icon_silhouette_sheet,icon_draft_fixture,icon_lookalikes,icon_recognition,icon_specs}.py and tests, docs/assets/{icon_style_guide,icon_set_v2_review}.md, ticket and stored artifacts.


## Completion Summary
Six revisions were drawn to the owner-approved silhouettes in a new draft set (`icons-owner-fixes-v1`). After seeing them the owner kept the adopted ruins and enemy camp ("Keep current versions"), so **four are proposed**: the solid up-arrow buff frame, the hooded rogue, the toolbox and the silver bead. The sheet rule passes with thresholds unchanged on the set with those four in place and every compliance row is met; the blind check names all four in free text. Nothing is adopted: the owner runs the 8 commands in the review doc (a `review` and an `adopt --parent r0001` per slot), and the recording ticket follows.

