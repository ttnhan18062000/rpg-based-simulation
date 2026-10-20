---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001
artifact_type: plan
tags: [architecture, testing]
---

# Plan

1. `visual_assets/review/icon_lookalikes.py`: rename `all_icon_sprites` to `r0001_icon_sprites` (docstring: the r0001 drawings, for before/after and r1-spec checks); add `adopted_icon_sprites()` = `{**r0001_icon_sprites(), **{k: fixes.fix_sprites()[k] for k in fixes.PROPOSED}}` with a function-local import of `icon_owner_fixes_draft_set`.
2. Rename at every R1 site and the definition in ONE commit (sites 3, 5, 6, 7, 8, 11, 14-15, 17-21, 23-24). Repoint the NOW sites to `adopted_icon_sprites()` (1, 2, 4, 9, 10, 12, 13, 16, 22).
3. New read-only test `tests/visual_assets/test_icon_adopted_art.py`: for every icon key of `adopted_icon_sprites()` (36), the generated artifact of its source (artifact record `pixel_hash`, `source_revision` and PNG) equals the accessor's pixels; the 7 keys are r0002 and the other 29 r0001; negative cases: an accessor that drops one revision (monkeypatched `PROPOSED` minus one key) fails the pin.
4. Update expected values only where site 4 changes them; list them.
5. Guarded-set check after the edits; `git diff --stat` limited to `visual_assets/review/**`, `tests/visual_assets/**`, `tools/visual_assets_entity_marker_sheet.py`, ticket and artifacts.
6. Light scoped runs (icon tests + the new one), then slot (a) and slot (b) on lead's GO (background plus watcher), close.
