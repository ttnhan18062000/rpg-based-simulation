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
INPROGRESS

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
- None yet

## Related Code Areas
- `visual_assets/review/icon_lookalikes.py`, `visual_assets/review/icon_owner_fixes_draft_set.py`, `visual_assets/review/icon_compliance.py`, `tests/visual_assets/test_icon_*.py`

## Assumptions / Open Questions
- Guarded files: none of the call sites is in the guarded list (checked by the planner at c35648e75); re-check after the edits.
- Store reading in a test: read-only via the read model does not take the write lock (cli.py WRITING_COMMANDS lists the writers); confirm in investigation.md.
- If a "now" site turns out to need the r0001 art for an owner-visible reason (e.g. a before/after panel), keep it on r0001 and say so; do not decide it silently.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
