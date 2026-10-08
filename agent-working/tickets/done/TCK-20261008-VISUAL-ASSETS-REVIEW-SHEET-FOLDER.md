---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER
phase: done
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER

## Title
Owner review sheets: one command writes a folder of large labelled PNG canvases (plus a README) for any draft set, used at every owner gate

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner (2026-10-08) finds the live preview page fine but slow to use (start Vite, scroll a long page), and asked
for review material as a batch of large canvases (images) placed under one folder per review. This replaces the page as
the owner's primary review surface; the page stays for detail.

## Scope
- A command, e.g. `python -m tests.visual_assets.review_sheets --set <draft_set_id> [--out DIR]`, default
  `DIR = ~/Work/asset-review/<draft_set_id>/` (outside every repo: no git noise, no gitignore under visual_assets).
  It (re)writes the folder deterministically:
  - `01_overview.png`: every drafted icon at 1x and 4x (whole-number scale, nearest neighbour), on a dark and a light
    panel, each labelled with its key and shown beside its fallback (colour chip/emoji name as text).
  - `02_before_after.png` (when a draft revises an adopted source): adopted rN next to the proposed revision.
  - `03_groups.png`: each must-differ group side by side (e.g. rarity next to tier badges; buff/debuff; locations).
  - `04_colour_vision.png`: the groups in colour, greyscale and protan/deutan/tritan (labelled "approximation").
  - `05_map_markers.png`: location glyphs on the plate over the darkest and brightest terrain tiles and a small map scene.
  - `06_silhouettes.png`: one-colour silhouettes (the process's owner-approval sheet; also usable before drawing).
  - `README.txt`: what each image shows, the recorded rule result and compliance summary, open findings, and the exact
    owner commands (adopt-set or per-slot review/adopt) for this set.
- Pure Python using the store's own PNG encode/decode (no new heavy dependency); labels with a small built-in bitmap
  font. Canvases large and legible at 100% zoom in a normal image viewer.
- Tests: deterministic bytes for a fixture set; every image present; a planted extra draft appears in 01; README lists
  the commands.
- Process: add to the style guide's process rule and the review docs: every owner gate (including the silhouette step)
  ships the folder path. Generate it now for `icons-owner-fixes-v1` (the four proposed revisions only, per the owner's
  decision) and hand the planner the path.

## Out of Scope
- Removing the preview page. Any app wiring. Committing the generated PNGs (the folder is local output; the generator and its tests are committed).

## Acceptance Criteria
- [x] One command produces the folder for any draft set; deterministic; tests pass.
- [x] Folder for icons-owner-fixes-v1 generated and its path given to the planner.
- [x] Process rule updated.

## Related Tickets
- TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES, TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Related Docs
- docs/assets/icon_style_guide.md (process rule), docs/assets/icon_set_v2_review.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER/ (plan, investigation, test_plan, mutant_proof.txt)

## Related Code Areas
- tests/visual_assets/ (new module), visual_assets/store pixels/PNG helpers (read)

## Assumptions / Open Questions
- If the store's PNG helpers cannot encode canvases this size within budget, report it to the planner before adding a dependency.

## Implementation Notes
- `tests/visual_assets/review_sheets.py`: `python -m tests.visual_assets.review_sheets --set <draft_set_id> [--out DIR]`, default `~/Work/asset-review/<set>/`; it refuses a folder inside any repository. Six canvases (01 overview at true size and zoomed beside the fallback, 02 before/after, 03 groups, 04 colour vision with an "approximation" label, 05 map markers or a note, 06 silhouettes) plus a README (what each image shows, recorded results, findings, the exact owner commands: per-slot `review` and `adopt --parent` for revisions, `adopt-set` for new icons, ALREADY ADOPTED for adopted drafts). Pure Python: zlib and struct for the PNG, a built-in 5x7 bitmap font (capitals), no new dependency; the whole folder takes about 4 seconds.
- Profiles: `icons-owner-fixes-v1` shows only the four proposed revisions and lists the two declined drafts as NOT PROPOSED; its recorded results come from `icon_owner_fixes_draft_set.evaluate`. Other sets work with defaults.
- Process: the style guide's step 7 and step 3, and the review doc, now say every owner gate (the silhouette step included) ships the folder path.
- Folder generated for `icons-owner-fixes-v1` at `/home/vboxuser/Work/asset-review/icons-owner-fixes-v1/` (local output, never committed).


## Test Summary
- `test_review_sheets.py` (10 tests); mutants A to E caught. `pytest tests/visual_assets tests/docs tests/static tests/architecture` was run after the change : 1975 passed, 2 skipped, 1 xfailed.


## Files Changed
- tests/visual_assets/{review_sheets,test_review_sheets}.py, docs/assets/{icon_style_guide,icon_set_v2_review}.md, ticket and stored artifacts.


## Completion Summary
One command writes a deterministic folder of six large labelled PNG canvases and a README for a draft set, outside every repository, with no new dependency; the owner gate now ships the folder path. Generated for `icons-owner-fixes-v1` (the four proposed revisions).

