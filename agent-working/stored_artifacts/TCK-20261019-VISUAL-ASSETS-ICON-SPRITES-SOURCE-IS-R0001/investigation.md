---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation

Fresh grep at base 7be048263 (main d3a0e4843 + the scoped ticket): `grep -rn all_icon_sprites --include=*.py` finds **26 call sites + 1 definition** (`icon_lookalikes.py:51`) + 1 historic script (`agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/drawing/fix.py:169`, a one-off, not importable code; left as history). Per file: `review/` 11 (compliance 6, review_sheets 1, silhouette_sheet 1, owner_fixes 1, recognition 1, lookalikes `__main__` 1), `tools/` 1, `tests/` 14 (compliance 8, silhouette 2, owner_fixes 2, lookalikes 1, recognition 1).

## What the accessor returns today
`icon_lookalikes.all_icon_sprites()` = `{**icon_draft_set.draft_sprites(), **icon_v2_draft_set.v2_sprites()}`: the 14 `icons-key-v1` + 22 `icons-v2` kept drafts, which are the **r0001** drawings. Seven of the 36 keys were re-adopted as r0002 on 2026-10-08 (set `icons-owner-fixes-v1`): `item.tool`, `class.rogue`, `rarity.common`, `status.frame_buff`, `status.frame_debuff`, `building.hero_house`, `building.inn`. The r0002 art is `icon_owner_fixes_draft_set.fix_sprites()` limited to `PROPOSED` (the same 7; `ruins` and `enemy_camp` drafts were never adopted). The evidence that this is also what the store holds is the pin test (below).

## Store read, no lock
Adopted pixels are readable without the store lock: `visual_assets/catalog/generated/<source>--x1/<png_hash>.r000N.artifact.json` carries `source_revision` and `pixel_hash` (one artifact per icon source, 65 icon sources, none has two) and the PNG sits beside it. A test reads those files and `visual_assets.store.pixels` (pure functions). `cli.py` `WRITING_COMMANDS` = intake, review, build, release, export-runtime, adopt, adopt-set, revoke; `READ_ONLY_COMMANDS` = list, show, audit, verify; the test calls none of them. No `store_write_lock`, no write, no build.

## Classification of every call site
"R1" = r0001 on purpose (an old/before comparison, an r1-spec table, or a recorded historic gate); "NOW" = means the art adopted now. Values are identical for a NOW site whose keys are not among the 7 (marked "same").

| # | site | class | reason |
|---|---|---|---|
| 1 | `visual_assets/review/icon_compliance.py:253` (`bead`) | NOW (same) | distance to the tier badges; tier keys are not revised |
| 2 | `icon_compliance.py:314` (`silver_bead`) | NOW (same) | mean L* of tier D/E; not revised |
| 3 | `icon_compliance.py:331` (`buff_arrow`) | R1 | `before` = the frame the arrow revision started from |
| 4 | `icon_compliance.py:442` (`spiked_debuff`) | R1 (kept, decided in step C) | "differs from the round buff frame": the row's value is carried by committed records (below); it is the same 28 px against the r0001 and the r0002 frame, so repointing would change nothing and only risk the owner-gated table. Kept on r0001 and recorded |
| 5 | `icon_compliance.py:456` (`tankard`) | R1 | `before` = the r0001 mug outline |
| 6 | `icon_compliance.py:497` (`__main__`) | R1 | prints the r1 `CHECKS` table, written for the r0001 redraws; against r0002 its rows fail by design (test 155) |
| 7 | `visual_assets/review/review_sheets.py:509` | R1 | builds the review folder of a set with a PROFILE (only `icons-owner-fixes-v1`): `adopted_old` is the "before" panel, r0001; with r0002 the panel would be empty and the owner's recorded sheet could not be reproduced. Decision flagged for the planner (below) |
| 8 | `visual_assets/review/icon_silhouette_sheet.py:49` | R1 | the silhouette-proposal gate of 2026-10-06; its committed output `frontend/src/visualAssets/__fixtures__/iconsilhouettes/silhouette_sheet.json` records what the owner saw against r0001 |
| 9 | `visual_assets/review/icon_recognition.py:211` | NOW | `build` without `--proposed` is the blind naming check of "the adopted set" |
| 10 | `visual_assets/review/icon_lookalikes.py:83` | NOW | `__main__` default report "for the adopted icons" |
| 11 | `visual_assets/review/icon_owner_fixes_draft_set.py:51` | R1 (base) | `proposed_sprites()` = r0001 base overlaid with the revisions; it IS the overlay and keeps the r0001 base (it can't call the accessor: same meaning, circular) |
| 12 | `tools/visual_assets_entity_marker_sheet.py:41` | NOW (same meaning) | hand overlay `{**all_icon_sprites(), **fixes.proposed_sprites()}` = the accessor; replaced by it |
| 13 | `tests/visual_assets/test_icon_recognition.py:13` | NOW | module `SPRITES` used to exercise the blind set and renders of the adopted set; no expected value depends on the 7 keys |
| 14-15 | `tests/visual_assets/test_icon_compliance.py:62,85` | R1 | the r1 `CHECKS` table against r0001 |
| 16 | `test_icon_compliance.py:98` | NOW (same) | edge-case beads over the rest of the sheet; the base sprites don't matter (the bead is replaced) |
| 17 | `test_icon_compliance.py:144` | R1 (base) | `{**r0001, **fix_sprites()}` with `CHECKS_R2` over the fix keys: the overlay replaces them |
| 18-19 | `test_icon_compliance.py:155,186,188,192` | R1 | "the old X fails the new row" (4 sites) |
| 20-21 | `tests/visual_assets/test_icon_silhouette_sheet.py:27,39` | R1 | follow site 8 |
| 22 | `tests/visual_assets/test_icon_lookalikes.py:55` | NOW (same) | "covers all 36 icons" |
| 23-24 | `tests/visual_assets/test_icon_owner_fixes_draft_set.py:59,73` | R1 | compare proposed against the r0001 drawings |

(26 sites = rows 1-24 with the grouped rows expanded: 14-15 is 2 sites, 18-19 is 4 sites, 20-21 is 2, 23-24 is 2. The `__main__` of `icon_lookalikes` is row 10 and has a second `--proposed` branch that calls `proposed_sprites()`.)

## Decision (confirmed by the planner)
Sites 7 and 8 are "means adopted now" in name but reproduce a recorded owner gate, so they stay on r0001. A future revision set needs an "adopted now" base in `review_sheets` (site 7); that belongs to that set's own ticket, not this one.

## Expected review-value changes: none
Checked (planner's step C) whether any committed output carries the `icon_compliance.py:442` row. It is carried by `docs/assets/icon_set_v2_review.md:217` (`| differs from the round buff frame | >= 6 px (I1 at 16x16) | 28 px | ok |`), `frontend/src/visualAssets/__fixtures__/icondraft_fixes/rule_result.json:281` (compared byte for byte by `test_icon_owner_fixes_draft_set.py:87`, the icons-owner-fixes-v1 compliance table the owner gated on) and `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/owner_fixes_result.json.txt`. Measured: the r0002 debuff is 28 px from the r0001 buff frame and 28 px from the r0002 buff frame, so the value would not change either way; because committed records carry the row, site 4 stays on r0001 and is the only "adopted now"-looking site kept for that reason. No review output changes in this ticket. The NOW sites are therefore 8: 1, 2, 9, 10, 12, 13, 16, 22.

## Guarded files
`docs/assets/aseprite_local_proof.json` lists conftests, drawing tests, store support, `test_release_byte_reproducibility.py` and others. None of the files in this change is in it (re-checked after the edits).

## Store icon sources the pin accounts for (planner's step A)
The store has 65 icon sources (`visual_assets/catalog/sources/icon_*`): 14 `icons-key-v1` + 22 `icons-v2` = the 36 accessor keys, plus an explicit excluded set that the test names with a reason:
- 18 object markers (`adopted_facts.OBJECT_KEYS`: `icon.node.*` x9, `icon.marker.nest`, `icon.building.*` x4 and the others of `object-markers-v1`): adopted 2026-10-14, drawn after the 36-icon review sheet, not in the accessor's sheet;
- 11 entity role markers (`adopted_facts.ENTITY_KEYS`): `entity-markers-v1`, 2026-10-19, same reason.
The test fails if a store icon source is in neither the 36 nor the excluded set, if an accessor key has no store source, and if the excluded set names a source that is not in the store.

## Static check
After the rename `grep -rn all_icon_sprites` must match exactly one file: `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/drawing/fix.py:169`. It is a stored artifact, a record, and is not edited.

## Name
`all_icon_sprites` is renamed to `r0001_icon_sprites` at all R1 sites in one commit (the old name is the bug: it reads as "all the icons"). The new accessor is `adopted_icon_sprites()`; both live in `icon_lookalikes.py`. The new one imports `icon_owner_fixes_draft_set` inside the function (that module imports `icon_compliance` and `icon_lookalikes`, so a top-level import is circular).
