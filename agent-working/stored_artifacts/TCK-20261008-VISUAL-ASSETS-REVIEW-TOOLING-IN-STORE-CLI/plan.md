---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI
artifact_type: plan
date: 2026-10-09
tags: [architecture, testing]
---

# Plan: review tooling gets one supported home (`visual_assets/review/`) and one generic command

## Decisions (planner, 2026-10-09, cross-session message; the user confirmed "Resume tickets 5-7")
- (a) New peer package `visual_assets/review/` with its own CLI `python -m visual_assets.review evaluate|review-sheets --set <id>` (not `store evaluate`): the store's layering forbids importing drawing, and the tools need `drawing.technique` (lint, ramps). Boundary row added: review may import store `config`, `pixels`, `records`, `draftexport` and drawing `technique`; store and drawing must not import review; not `src`, not frontend.
  Deviation to report: the planner named `config`, `pixels` and `lint`; the tools also use `store.records` (adoption records for the ALREADY ADOPTED detection), `store.draftexport` (the draft fixture) and `drawing.technique.ramps` (palette ramps), all read-only, so those are in the allowed set. No gate layer is allowed.
- (b) No shims for `tests.visual_assets.X`; active docs' commands updated; historical records (done tickets, stored artifacts, dated result sections) keep the old paths.
- (c) TWO commits under this ticket: (1) pure move + import rewrites + docs commands, no behaviour change, with the byte-for-byte proof; (2) generic `evaluate --set` with `sets.py`, the one-adopt-set generator change with tests, the `tile_pixels` fix.

## Commit 1: the mapping (git mv, history kept)
`tests/visual_assets/<m>.py` -> `visual_assets/review/<m>.py` for: pilot_colour_vision, set_colour_vision (a dependency of icon_palette, not in the ticket's list), icon_palette, icon_sheet_rule, icon_sheet_synthetic, icon_v2_groups, icon_v2_keys, icon_item_families, icon_specs, icon_compliance, icon_recognition, icon_lookalikes, icon_silhouette_sheet, icon_draft_set, icon_v2_draft_set, icon_owner_fixes_draft_set, icon_draft_fixture, review_sheets (18 modules). `tests/visual_assets` keeps the tests, `adopted_facts`, `derived_runtime`, `strict_aseprite`, conftest. `REPO = parents[2]` is the same depth in both places.
Left untouched on purpose (data records, not live references): `visual_assets/palettes/icons-v1.json` ("derivation" and "source" strings quote the old path; the file is exactly the output of `icon_palette.build_palette`, so editing the string would change a recorded file) and the matching strings in `icon_palette.py`; the dated sections of `pilot_terrain_m5_results.md` and `icon_key_set_review.md`.

## Byte-for-byte proof (acceptance bar)
Baseline taken BEFORE the move from the current code, outside the repo: the three evaluator JSON outputs (`icon_draft_set`, `icon_v2_draft_set`, `icon_owner_fixes_draft_set`) and the review folders (six PNGs + README) of `icons-key-v1`, `icons-v2`, `icons-owner-fixes-v1`. After commit 1 and again after commit 2: the same outputs from the new modules/commands compared with `cmp`/`diff -r`; the committed `icondraft*/rule_result.json` fixtures are the recorded results (`icon_draft_fixture --check`, all three identical).

## Commit 2 (summary)
`visual_assets/review/sets.py`: thin per-set definitions (groups, sizes, shape-only list, extra measurements, compliance table choice) replacing the three per-set evaluators; `python -m visual_assets.review evaluate --set <id>` and `review-sheets --set <id>`; generator prints ONE `adopt-set <set>` with the NEW/REVISION summary when the set's drafts declare `parent_revision`, per-slot commands only for older sets (both tested); `tile_pixels()` selects `terrain.forest` / the key's default detail from the manifest (the CLI of `pilot_colour_vision` now prints the plain row, not the tree row; no recorded result moves: the per-slot rows call `evaluate()` directly and the icon rules use `icon_palette._tiles()`).

## What was built in commit 2 (deviations disclosed)
- The three per-set evaluators were NOT folded into one table-driven function: their reports differ in shape (single family, two families with compliance and look-alikes), so a generic builder would have needed a layout mini-language. They are now thin data modules (no CLI, no hash code) over one shared reader (`sprites.py`); `sets.py` is the registry and `python -m visual_assets.review evaluate --set <id>` the one command. `--recorded` prints the exact sorted-key text committed as `rule_result.json`.
- `review-sheets` README changes by exactly one sentence for every set (the old text said adopt-set cannot make revisions; it can now, for drafts kept with `--revises`); the six PNGs are byte-identical (checked with cmp). The review READMEs of `icons-key-v1` and `icons-v2` still say "no recorded evaluation module": wiring the generic evaluation into them would change their README bytes beyond that sentence, so it is a follow-up, not done here.
- The generator prints ONE `adopt-set` (plus `draft drop` commands for declined drafts) when the set's drafts declare `parent_revision` and none is adopted yet; per-slot commands otherwise (older sets, or a partly adopted set because adopt-set refuses an adopted draft).
- Child 2 misses found by running `tests/tools` for the first time: the `.mcp.json` registration test and one done ticket's phase; fixed in their own commit (b02ebb8b3).

