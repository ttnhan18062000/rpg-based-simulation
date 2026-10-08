---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI
phase: open
date: 2026-10-08
tags: [architecture, testing]
---

# TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI

## Title
Review tooling moves into the store CLI as one generic per-set command, and the tile_pixels wrong-slot bug is fixed

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 5 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. Each draft set got its own evaluator module under `tests/visual_assets/` (icon_draft_set, icon_v2_draft_set, icon_owner_fixes_draft_set), and `review_sheets.py` (505 lines), recognition and look-alike tools live in tests/. `pilot_colour_vision.tile_pixels()` takes the first PNG of the pilot export (a documented fragility: pilot_terrain_m5_results.md:85).

## Scope
- One supported home and command for set evaluation and review sheets (e.g. `python -m visual_assets.store evaluate
  --set <id>` and `review-sheets --set <id>`): sheet rule, compliance, look-alikes, review folder, README with commands.
  Check the import-linter contracts c14/c15 (visual_assets <-> src) and the store's dependency rules first.
- Retire the per-set modules (or reduce them to thin data), keeping every existing recorded result reproducible.
- Fix `tile_pixels()` to select the slot by key/detail, not file order; test it on the real export.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Changing any rule threshold or recorded verdict.

## Acceptance Criteria
- [ ] Generic commands reproduce the recorded results of icons-key-v1, icons-v2, icons-owner-fixes-v1 byte for byte; per-set modules gone or thin; tile_pixels fixed and tested.

## Related Tickets


## Related Docs


## Related Stored Artifacts


## Related Code Areas
- tests/visual_assets/review_sheets.py, icon_*_draft_set.py, icon_sheet_rule.py, icon_recognition.py, icon_lookalikes.py, pilot_colour_vision.py; visual_assets/store/cli.py

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

