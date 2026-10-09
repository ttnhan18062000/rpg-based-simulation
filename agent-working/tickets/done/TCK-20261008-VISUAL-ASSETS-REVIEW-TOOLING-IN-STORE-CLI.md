---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI
phase: done
date: 2026-10-08
tags: [architecture, testing]
---

# TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI

## Title
Review tooling moves into the store CLI as one generic per-set command, and the tile_pixels wrong-slot bug is fixed

## Status
DONE

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
- [x] Generic commands reproduce the recorded results of icons-key-v1, icons-v2, icons-owner-fixes-v1 byte for byte; per-set modules gone or thin; tile_pixels fixed and tested.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI/ (plan with the planner's decisions, investigation, test_plan, mutant_proof, byte_for_byte_proof)

## Related Code Areas
- tests/visual_assets/review_sheets.py, icon_*_draft_set.py, icon_sheet_rule.py, icon_recognition.py, icon_lookalikes.py, pilot_colour_vision.py; visual_assets/store/cli.py

## Assumptions / Open Questions
- Planner decisions (2026-10-09): new peer package `visual_assets/review/` with its own CLI (not `store evaluate`); no shims; active docs updated, historical records untouched; TWO commits under this ticket (a pure move with the byte-for-byte proof, then the generic command, the generator change and the tile_pixels fix).
- The three per-set evaluators stay as thin data modules over one shared reader; a table-driven single evaluator was not built (their reports differ in shape).
- The review READMEs of icons-key-v1 and icons-v2 still say there is no recorded evaluation: wiring the generic evaluation in would change their bytes beyond one sentence; a follow-up.

## Implementation Notes
- Commit 4a8c0f6d3: 18 modules git-mv'd from tests/visual_assets to visual_assets/review (one more than the ticket listed: set_colour_vision), imports and active docs rewritten, boundary row, c14/c15 kept.
- Commit 2: `sprites.py` shared reader, `sets.py` registry, `__main__.py` CLI (`evaluate`, `review-sheets`, `--recorded`), per-set modules reduced to data (no CLI), the generator prints ONE adopt-set for revising sets, tile_pixels selects by key and detail (the plain row now).
- Also found by running tests/tools for the first time: two child 2 misses (the .mcp.json registration test, one done ticket's phase), fixed in b02ebb8b3.

## Test Summary
- Byte-for-byte proof after both commits (see byte_for_byte_proof.txt); 6 new test groups; mutants A-I caught (one first attempt did not apply and was redone). Scoped suites: see the commit report.

## Files Changed
- visual_assets/review/ (18 moved modules, sprites, sets, __main__), tests (boundaries, review CLI, review sheets, pilot colour vision, imports), docs (drawing_tools, style guide, review docs, handoff), frontend comments and one path in iconScene.test.ts, visual_assets/README.md, ticket and artifacts.

## Completion Summary
Review tooling has one supported home (`visual_assets/review/`) and one command per job; the recorded results reproduce byte for byte; the owner review folder prints one adopt-set for revising sets; tile_pixels picks the right slot; the store's layering and c14/c15 are intact.
