---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER
phase: open
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER

## Title
Owner review sheets: one command writes a folder of large labelled PNG canvases (plus a README) for any draft set, used at every owner gate

## Status
OPEN

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
- [ ] One command produces the folder for any draft set; deterministic; tests pass.
- [ ] Folder for icons-owner-fixes-v1 generated and its path given to the planner.
- [ ] Process rule updated.

## Related Tickets
- TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES, TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

## Related Docs
- docs/assets/icon_style_guide.md (process rule), docs/assets/icon_set_v2_review.md

## Related Stored Artifacts


## Related Code Areas
- tests/visual_assets/ (new module), visual_assets/store pixels/PNG helpers (read)

## Assumptions / Open Questions
- If the store's PNG helpers cannot encode canvases this size within budget, report it to the planner before adding a dependency.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

