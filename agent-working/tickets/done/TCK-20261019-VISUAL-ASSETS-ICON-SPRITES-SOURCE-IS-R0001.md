---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001
phase: done
date: 2026-10-19
tags: [architecture, testing]
---

# TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001

## Title
`icon_lookalikes.all_icon_sprites()` returns r0001 art for the 7 revised icon keys; find which consumers mean "adopted now" and point them at the current art

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by asset-implementer on 2026-10-19 in `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`. The entity silhouette sheet took its comparison glyphs from `icon_lookalikes.all_icon_sprites()`, and it showed `icon.item.tool` as the pre-D21 wrench. The adopted `item.tool` is r0002 (hammer and tongs, adopted 2026-10-08), and so is `class.rogue`. The sheet fixed itself by overlaying `icon_owner_fixes_draft_set.proposed_sprites()`. Several consumers use the r0001 art on purpose (`old = ...`, `before = ...` in `tests/visual_assets/test_icon_compliance.py` and `visual_assets/review/icon_compliance.py`). Others may mean "the art adopted now" and so check stale art: `tests/visual_assets/test_icon_recognition.py:13`, `tests/visual_assets/test_icon_lookalikes.py:55`, `tests/visual_assets/test_icon_silhouette_sheet.py:27,39` and `visual_assets/review/icon_compliance.py:253,314,497`.

## Scope
Owner decision 2026-10-20 (via lead-planner): scope AS FILED, a review-tool correctness fix only.
- Classify every `icon_lookalikes.all_icon_sprites()` call site at main c35648e75 as "r0001 on purpose" (old/before comparisons) or "means the art adopted now", with file:line and one line of reason, in investigation.md. Starting list (re-check with a fresh grep; the list is not authoritative):
  - `visual_assets/review/`: `icon_compliance.py:253,314,331,442,456,497`; `review_sheets.py:509`; `icon_silhouette_sheet.py:49`; `icon_recognition.py:211`; `icon_lookalikes.py:83`; `icon_owner_fixes_draft_set.py:51`.
  - `tests/visual_assets/`: `test_icon_recognition.py:13`; `test_icon_compliance.py:62,85,98,144,155,186,188,192`; `test_icon_silhouette_sheet.py:27,39`; `test_icon_lookalikes.py:55`; `test_icon_owner_fixes_draft_set.py:59,73`.
  - `tools/visual_assets_entity_marker_sheet.py:41` (already overlays the fixes by hand).
- Add ONE accessor for the current adopted art (r0001 drafts overlaid with the adopted r0002 revisions), with a name that says so (e.g. `adopted_icon_sprites()`), in `visual_assets/review/`. Repoint every "adopted now" site to it. Leave the on-purpose r0001 sites on the old accessor; rename the old one (e.g. `r0001_icon_sprites()`) only if it makes the meaning clearer, and then rename at every site in the same commit.
- Hand overlays that reimplement the accessor (`icon_owner_fixes_draft_set.py:51` as a base, `tools/visual_assets_entity_marker_sheet.py:41`) use the accessor where the meaning is the same; investigation.md says which.
- One read-only test pins the accessor against the store's adopted pixels for every icon key (through the store read model or `pixels`; no store write, no lock taken, no build). The test fails if a future adoption adds a revision the accessor does not carry.

## Out of Scope
- No art: no redraw, no new draft set, no handoff, no intake.
- No adoption, adopt-set, revoke, release or build (owner-only, and not asked).
- No registry change (`visual_assets/catalog/definitions/visual_keys.yaml`), no catalog write.
- No refreshed review folder under ~/Work/asset-review (owner chose option 1, not option 2).
- No edit under `src/**`, `frontend/**`, `visual_assets/store/**`, `visual_assets/drawing/**`.
- No edit to any file in the guarded list of `docs/assets/aseprite_local_proof.json` (so no Aseprite proof refresh).

## Acceptance Criteria
- [ ] investigation.md classifies every call site (fresh grep at the start), with file:line, class and reason; the count matches the grep.
- [ ] One accessor named for "current adopted art" exists in `visual_assets/review/`; every "adopted now" site uses it; no "r0001 on purpose" site changed meaning.
- [ ] A read-only test pins the accessor against the store's adopted pixels for every icon key, and fails (shown in the Test Summary) when one adopted revision is dropped from the accessor.
- [ ] Review outputs whose expected values were the stale art are updated, and each such change is listed in the Test Summary with the key and why.
- [ ] No guarded file touched: the guarded-set check against `docs/assets/aseprite_local_proof.json` is run after the repoint edits and passes; the Aseprite proof test stays green without a refresh.
- [ ] Nothing outside scope changed: `git diff --stat origin/main...HEAD` shows only `visual_assets/review/**`, `tests/visual_assets/**`, optionally `tools/visual_assets_entity_marker_sheet.py`, the ticket, staging/stored artifacts, monitoring shards and `docs/REGISTRY.yaml`.
- [ ] Tests: scoped light runs during work (load < 3); slot (a) `tests/visual_assets -m "not slow"` and slot (b) `tests/unit/tools tests/tools` (background plus watcher) only with lead's GO for each; results recorded exactly.

## Related Tickets
- `TCK-20261020-VISUAL-ASSETS-STORE-TESTS-REAL-LOCK` (#692; store tests' lock in tmp)
- `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS` (where it was found)
- the icon owner-fixes batch (r0002 revisions, adopted 2026-10-08)

## Related Docs
- `docs/assets/icon_style_guide.md` (D21, the item.tool row)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001/ (investigation.md: the classification of every call site; plan.md; test_plan.md)

## Related Code Areas
- `visual_assets/review/icon_lookalikes.py`, `visual_assets/review/icon_owner_fixes_draft_set.py`, `visual_assets/review/icon_compliance.py`, `tests/visual_assets/test_icon_*.py`

## Assumptions / Open Questions
- Guarded files: none of the call sites is in the guarded list (checked by the planner at c35648e75); re-check after the edits.
- Store reading in a test: read-only via the read model does not take the write lock (cli.py WRITING_COMMANDS lists the writers); confirm in investigation.md.
- If a "now" site turns out to need the r0001 art for an owner-visible reason (e.g. a before/after panel), keep it on r0001 and say so; do not decide it silently.

## Implementation Notes
- `icon_lookalikes.adopted_icon_sprites()` is the one accessor for the art adopted now: the r0001 drawings with the seven owner-fix revisions (`icon_owner_fixes_draft_set.fix_sprites()` for `PROPOSED`) in place of theirs. It imports `icon_owner_fixes_draft_set` inside the function (that module imports `icon_compliance`, which imports `icon_lookalikes`).
- `all_icon_sprites` is renamed `r0001_icon_sprites` at the definition and every r0001 site in one commit. 26 call sites were classified (investigation.md): 8 "adopted now" repointed (`icon_compliance.py` 253 and 314, `icon_recognition.py:211`, `icon_lookalikes.py` `__main__`, `tools/visual_assets_entity_marker_sheet.py`, `test_icon_recognition.py:13`, `test_icon_compliance.py:98`, `test_icon_lookalikes.py:55`); the rest stay r0001 on purpose. `icon_compliance.py:442` (the debuff's "differs from the round buff frame", 28 px against the r0001 and the r0002 frame) stays r0001 because committed records carry that row (`docs/assets/icon_set_v2_review.md:217`, `icondraft_fixes/rule_result.json`, compared byte for byte by `test_icon_owner_fixes_draft_set.py:87`). `review_sheets.py:509` and `icon_silhouette_sheet.py:49` stay r0001: they reproduce recorded owner gates; a future revision set needs an "adopted now" base in `review_sheets`, which is that set's own ticket.
- `tests/visual_assets/test_icon_adopted_art.py` (5 tests, read-only: no lock, no CLI, no write, no build): the expected revision is derived from the store (newest non-revoked revision under `sources/<source>/` via `records.list_revisions` + `records.is_eligible`), the built artifact's `source_revision` and `pixel_hash` must match it and the accessor's pixels; the 65 store icon sources are the 36 accessor keys plus an explicit excluded set of 29 (18 object markers, 11 entity markers); unknown, missing and stale-excluded keys fail.
- The historic script `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/drawing/fix.py:169` still says `all_icon_sprites`; stored artifacts are records and are not edited.

## Test Summary
- Review outputs whose expected value was stale art: **none**. The 8 "adopted now" sites do not depend on the seven revised keys (the tier badges, the blind-set and renders, the 36-icon count, the edge-case bead), and `icon_compliance.py:442` stays on r0001. No fixture, doc or expected value changed.
- Pin shown to fail: with `icon.item.tool` dropped from the overlay, `pin_mismatches` returns `['icon.item.tool']` (permanent test `test_dropping_one_adopted_revision_from_the_accessor_is_reported_as_that_key`); an adopted but unbuilt r0003 on `icon_item_tool` is reported (`test_an_adopted_revision_that_is_not_built_yet_is_reported`); the old r0001 art mismatches exactly the 7 revised keys.
- Scoped light runs: `test_icon_adopted_art.py` 5 passed; `test_icon*`, `test_review*`, `test_sample_map*` not slow 214 passed (211 s, before the pin fix).
- Guarded-set check against `docs/assets/aseprite_local_proof.json` after the repoint edits: none of the changed files is guarded; `test_aseprite_local_proof.py` + `test_aseprite_licence_guard.py` 54 passed.
- Static grep: `grep -rn all_icon_sprites` in py/md/yaml leaves exactly one code match, the stored-artifact script named above (plus prose in this ticket, its artifacts and the REGISTRY title).
- Slot (a) at a5dbce8f2: `tests/visual_assets -m "not slow"` 2564 passed, 0 failed, 0 skipped, 637.62 s (10:37); host at the end MemAvailable 5121 MB, swap 3004 MB.
- Slot (b) `tests/unit/tools` + `tests/tools`: pending.

## Files Changed
- visual_assets/review/icon_lookalikes.py (accessor, rename), icon_compliance.py, icon_recognition.py, icon_owner_fixes_draft_set.py, icon_silhouette_sheet.py, review_sheets.py; tools/visual_assets_entity_marker_sheet.py.
- tests/visual_assets/test_icon_adopted_art.py (new); test_icon_compliance.py, test_icon_lookalikes.py, test_icon_owner_fixes_draft_set.py, test_icon_recognition.py, test_icon_silhouette_sheet.py.
- This ticket, its staging artifacts (moved to stored_artifacts), monitoring shards, docs/REGISTRY.yaml.

## Completion Summary
Review tools that mean "the art adopted now" read it from one accessor, `adopted_icon_sprites()`; the r0001 drawings keep a name that says so, `r0001_icon_sprites()`. A read-only test pins the accessor against the store for all 36 icon keys, derived from the store's newest adopted revision, with the 65 icon sources fully accounted for. No art, adoption, registry or catalog change; no review output changed. Known gaps: none stated; the two recorded gate sites (review_sheets, silhouette sheet) stay on r0001 by design.
