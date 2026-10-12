---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS
phase: open
date: 2026-10-12
tags: [architecture, testing, mcp]
---

# TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS

## Title
Terrain variants: detail axes on seven terrain keys, about 14 drawn variants, owner review folder and adopt-set

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. The art itself.

## Scope
- **Owner-only step 1 (blocking question, neutral fixed-order options):** the detail values per key. Start from the planner's split below; the owner may change counts or terrains.
Planner's proposed split (14 tiles; the owner decides the values in child 3's blocking question):
  - `terrain.grassland` (60,239 sample cells via the alias): 4 new values -> `base` + 4 = 5
  - `terrain.mountain`, `terrain.cave`, `terrain.ruins`, `terrain.swamp`, `terrain.shallow_water`: 2 new values each -> `base` + 2 = 3 each
  - `terrain.forest` keeps its 3; `terrain.road` gets none (a road wants connecting tiles, gap G5, not random variants).
- Add the approved `detail` axes (default `base`) to the keys, per child 1's design.
- Draw the variants with the `aseprite-pixel-art` MCP tools from a session started after the 2026-10-11 restart: the first `new_sprite` confirms the server pin. If it still refuses, STOP and tell asset-planner, and do not drive the api around it this time without asking. Follow `docs/assets/pixel_art_technique.md` and the existing tile palettes. A variant must read as the same terrain at 1x and break up repetition (one feature, not a new terrain). Lint clean or justified.
- Make one draft set; intake PASS for each; measure each against the bounds.
- **Owner review folder:** `~/Work/asset-review/terrain-variants-v1/`. Large labelled PNG canvases: each key's base plus its variants side by side, and a 16x16-cell sample patch tiled with the client's pick (the sample-map renderer), with a README. Not the Vite page.
- **Owner-only step 2:** the owner reviews the WHOLE set and runs `adopt-set` (no per-tile adoption). Redraws on request.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] The owner's detail-value answer recorded; axes added.
- [ ] Every variant intake PASS, measured, in one draft set; the review folder delivered.
- [ ] The owner ran `adopt-set` (adoption id recorded), or the redraws asked for are done and adopted.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/drawing/**` (used), `visual_assets/drafts/`, `visual_assets/catalog/**`, `tools/visual_assets_sample_map_render.py` (used for the review patch)

## Assumptions / Open Questions


## Implementation Notes
- MCP: the restart is CONFIRMED from this session: the first `new_sprite` (`pin_check_scratch2`, Aseprite 1.3.18.6) ran with no pin refusal; the scratch sprite stays in the MCP workspace and was not handed off. The tools serve the main checkout, so intake and `draft keep` ran with the store CLI in this worktree (the MCP's `submit_candidate` would have staged into the main checkout).
- OWNER ANSWER (2026-10-12, asked directly with neutral fixed-order options): "Planner's split, named features (14 tiles)": grassland base + tufts, flowers, clover, bare; mountain base + crag, scree; cave base + stalagmite, rubble; ruins base + moss, fallen; swamp base + reeds, puddle; shallow_water base + ripple, pebbles. Forest keeps plain/bush/tree; road gets none. `visual_keys.yaml`: the six `detail` axes (default `base`), with a comment; the registry is 30,943 B (6.7 % of the bound).
- Drawing, through the MCP tools: each base tile was rebuilt as an MCP sprite from the adopted pixels (`new_sprite` with the dominant colour, then `apply_ops pixels` / `rect`), and each variant is a `branch_sprite` of its base plus a few `apply_ops pixels` (10 to 21 pixels changed, one feature, none on the tile's outer ring). The pixels come from a small script of diffs over the adopted base pixels, tuned by eye after looking at every contact sheet (not stroke by stroke); the owner is told so in the review README. Two variants first changed one edge pixel (`grassland/flowers` (13,15), `mountain/scree` (0,9)); they were put back to the base colour (revision r0003), re-handed off, re-intaked and replaced in the set (`draft keep --replace`).
- New colours: `grassland/flowers` petal #e6e2c8, `grassland/bare` earth #7d6a42 and #3b2f1c (first #6b5a37 and #54452a, moved after lint reported a value_separation against the greens), `ruins/moss` #5f8248; every other variant uses its base palette only; all are within the 8-colour budget (5 to 7 colours). Lint: touches_edge and orphan_pixels are info (the base tiles have them); every value_separation pair is the base palette's own except grassland/bare (brown earth against mid green) which is stated in its handoff limitation.
- Intake PASSED for all 14 (draft set `terrain-variants-v1`, `draft verify` ok): `in-65c05a4883b85475` (grassland tufts), `in-89cc0d2840d4ffcc` (flowers, the corrected one), `in-fc507b5f0a392e56` (clover), `in-7d9d12e1710c976c` (bare), `in-e9bc4952cd35a949` (mountain crag), `in-520e785806ae7283` (scree, corrected), `in-e22daabccc89b641` (cave stalagmite), `in-1ebc360e5d0e2640` (rubble), `in-210c87fe60a73e2e` (ruins moss), `in-c3717bbe699dddba` (fallen), `in-5bb43e1bfa5bf6bb` (swamp reeds), `in-b96287b353ee54dc` (puddle), `in-74b31b522a46310c` (shallow_water ripple), `in-2e64e51314b373ce` (pebbles). Measured against the bounds: source 360 to 406 B (`MAX_SOURCE_BYTES` 102,400: 0.4 %), `IntakeResult` 672 B, handoff `package.json` 1,156 to 1,222 B, preview 681 to 770 B at 128 x 128 (`MAX_PREVIEW_DIM` 1,024), one frame, no tag, no slice. No bound exceeded.
- Review folder `~/Work/asset-review/terrain-variants-v1/`: `02_repetition_check_grassland.png` (G4: 16 x 16 cells, base only against the client's pick), `03_mixed_landscape_with_fringes.png` (28 x 20 cells, base tiles against variants, the same border rule and 73 fringed cells), six `01_*` canvases, README. The images are made with the sample-map renderer's port of `pickDetail` and the border rule (`tools/visual_assets_sample_map_render.py`), reading the real variant previews of the quarantined intakes; the script is kept in the stored artifacts.
- Blind check (asset-planner's gate; a fresh model, same protocol each time): the 20 tiles (6 bases + 14 variants) shuffled, unlabelled but numbered, shown at x6, named from a list of 11 terrains: 20 of 20 before the edge-pixel fix and 20 of 20 on the FINAL sheet. One reader and one image: a screen, not proof.
- OWNER STEP 2 (pending): the owner reviews the whole set and runs `adopt-set`; recorded at close with the adoption id.
- 12 TESTS CHANGED, WITH THE REASON (planner ruling 2026-10-12, rc-0008 ruling (c) precedent for gate-closed sets, lead-planner narrowing): declaring an axis on adopted keys made a fresh draft export copy the new axes into its `details` block for the adopted terrain references, and made an old candidate derived with the new registry invalid. The 12: `test_closed_draft_fixtures.py` (6: `test_a_closed_fixture_matches_its_gate_and_a_full_fresh_export_no_longer_would[icons-key-v1|icons-v2|icons-owner-fixes-v1]`, `test_mutant_a_set_removed_from_the_closed_pin_runs_the_full_equality_and_fails_on_todays_store[...x3]`), `test_icon_draft_fixture.py` (2: `test_the_committed_copy_equals_a_fresh_export_modulo_the_registry_hash`, `test_a_changed_registry_hash_alone_is_deliberately_not_caught`), `test_icon_owner_fixes_draft_set.py::test_the_recorded_result_is_current_and_the_committed_copy_equals_a_fresh_export`, `test_icon_v2_draft_set.py::test_the_committed_copy_equals_a_fresh_export_modulo_the_registry_hash`, `test_pilot_fixture.py::test_the_committed_pilot_export_equals_the_forest_slots_of_a_fresh_export_of_the_release`, `test_terrainset_fixture.py::test_the_committed_terrainset_export_equals_the_export_derived_from_the_stored_release`. Not one of the 12 was edited: they pass because (1) `closed_draft_fixture.details_problems` (new) keeps what the owner SAW exact (every committed `details` row identical, an entry keeps its `detail`, the manifest keeps the store's rule "detail exactly when listed") and allows a fresh row only for a key in the pinned constant `AXES_DECLARED_AFTER_THE_GATES` (the six terrains, tied to this ticket; `terrain.forest`, whose axis predates the gates, still matches exactly) whose committed entries carry no detail and whose row equals the current registry's axis; (2) `derived_runtime.derive` emits a `details` row only for a key whose entries in that candidate carry a detail value (an OLD candidate with a NEWER registry, not what `export_runtime` does; it refuses with `registry_mismatch`; on an agreeing candidate and registry it is still byte-for-byte `export_runtime`'s, `test_derived_runtime.py`). The four direct callers of the open comparator named in the first report were already going through the closed comparator (`cdf.differences`); the one `fx.differences` call is the negative assertion that a full fresh export would NOT equal a closed fixture and is unchanged. No fixture file changed (`git diff` of every fixture: zero bytes) and every pinned manifest sha256 is as it was.
- New tests `tests/visual_assets/test_closed_details_rule.py` (10): the pinned list is the six terrains and not forest; the rule test (a fresh export carries axes the gate never showed, the closed gate still passes with its committed bytes untouched); mutation proofs, each applied at the right site and shown failing for the right reason with the pin rewritten so nothing masks it: (a) a changed details value for forest, (a2) a missing forest row, (b) an added row whose values are not the registry's, (c) an entry that gains a detail, (c2) an entry that loses its detail, (d) a derived row for a key with no detail entries (refused by the store's own manifest rule; the derived rows are exactly the keys with detail entries), (e) a row allowed for a key outside the pinned list.

## Test Summary
`tests/visual_assets` (project venv) at this commit: 2492 passed, 2 failed, 14 errors = EXACTLY the 16 expected-red tests of `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES` (all `registry_mismatch` on an export of rc-0009: `test_atlas.py` 5, `test_release_byte_reproducibility.py` 7, `test_sample_map_render.py` 4, the same ids), nothing else; they go green with rc-0010 in child 4. The 12 tests that the axes first broke are green (71 passed with `test_closed_details_rule.py`, `test_derived_runtime.py` and the fixture family). The registry pins moved to exact values (`adopted_facts.TERRAIN_VARIANT_AXES`, `test_registry.py`).

## Files Changed
- `visual_assets/catalog/definitions/visual_keys.yaml` (six detail axes), `visual_assets/drafts/terrain-variants-v1/` (the draft set, 14 drafts), `tests/visual_assets/closed_draft_fixture.py`, `tests/visual_assets/derived_runtime.py`, `tests/visual_assets/test_closed_details_rule.py` (new), `tests/visual_assets/adopted_facts.py`, `tests/visual_assets/store/unit/test_registry.py`, the staging scripts (variants spec, review builder)

## Completion Summary

