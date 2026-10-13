---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS
phase: inprogress
date: 2026-10-13
tags: [architecture, testing, mcp]
---

# TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS

## Title
Map markers: object markers for buildings, places and resource nodes (keys, specs, silhouettes, drafts, owner adopt-set)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. Lead: art-only drafting that does not depend on rpg's final kind list may start once filed. Building, place and resource-node kinds come from the authored world data (`spec.buildings`, `PlaceKind`, resource node kinds) and are already V2 names, so this child does not wait for #523. Needs child 1's approved design and the owner's answers.

## Scope
- Add the approved object keys and aliases to `visual_keys.yaml` (labels, `safety_class`, `fallback`). Registry edit -> rc-0010 becomes unexportable (Known gap). Expected red until child 4: list exactly which tests, nothing else may fail.
- **Specs before drawing** (style guide process rule): one `icon_specs.yaml` entry per new key (theme, orientation, proportions in px, parts, reads as, must not read as, synonyms, distractors, modern lookalikes to avoid). The `--table` in the style guide is regenerated.
- **Reference study:** for each subject, note what makes it read as itself at 16 px (healer's hut vs inn, watchtower vs town hall, iron vs silver vein, a cover patch vs a herb patch).
- **Owner-only step 1 (blocking, neutral fixed-order options):** the silhouette sheet. One-colour silhouettes of the whole set at 1x and 4x in a review folder, `~/Work/asset-review/object-markers-silhouettes/`. Draw nothing shaded before the owner approves.
- Draw with the `aseprite-pixel-art` MCP tools (the first `new_sprite` confirms the server pin; if it refuses, STOP and tell asset-planner). Follow `pixel_art_technique.md`, the icon palette and the sheet rule. Lint clean or justified. Intake PASS for each. Compliance table against each spec.
- **Recognisability checks:** the blind naming check with distractors (theme/era pass included). An icon that misreads gets redrawn before the owner gate, not explained.
- **Owner review folder:** `~/Work/asset-review/object-markers-v1/`. Large labelled PNG canvases: each marker at 1x, 4x and on a 16 px map cell over grassland, plus the sample-map crops with the markers drawn (sample-map renderer, offline), and a README. Not the Vite page.
- **Owner-only step 2:** the owner reviews the WHOLE set and runs `adopt-set`. Redraws on request.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [ ] Keys and aliases in the registry per the approved design; the red set listed exactly.
- [ ] Specs, reference notes, owner-approved silhouettes, compliance table, blind check results recorded.
- [ ] The owner adopted the object set with `adopt-set`.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; needs `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`
- Precedents: `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`, `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`, `TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/icons/icon_specs.yaml`, `docs/assets/icon_style_guide.md` (generated table), `tools/visual_assets_sample_map_render.py`, `tests/visual_assets/**`

## Assumptions / Open Questions
**Owner answers, 2026-10-13 (AskUserQuestion, relayed by asset-planner; child 1 approved):**
1. Resource nodes: "13 keys, one per kind" = 13 `icon.node.<kind>` keys, 13 tiles (16x16, live 12x12, no plate), including the 3 `cover_patch_*` as separate keys. (Option (b), a detail axis per kind, is withdrawn: `pickDetail` picks by cell, not kind.)
2. Buildings: "24x24 panel icons only" = 4 new `icon.building.{healer_hut,town_hall,mine_entrance,watchtower}`. A 16x16 building map glyph is a later, separate choice; child 4 adds it to the gap report.
3. Aliases, all four ticked plus `ruin` as planned (registry-only, Known gap): `icon.building.shop` -> `icon.building.store`, `icon.marker.camp` -> `icon.marker.enemy_camp`, `icon.marker.ruin` -> `icon.marker.ruins`, `icon.marker.dungeon` -> `icon.marker.dungeon_entrance`, `icon.marker.lair` -> `icon.marker.boss_arena` (5 aliases).
4. CITY: "Location plate alone": no key, no alias, no glyph. Child 4's renderer draws the plate only.
New `icon.marker.nest` (16x16 on the plate) stays. Child 2 = 18 new keys (4 building + 1 place + 13 node) + 5 aliases.


## Implementation Notes
**Owner answers on the silhouette folder (39e54745f), 2026-10-13 (AskUserQuestion, relayed by asset-planner):** Silhouettes: "Approve all as shown" (all 18; the owner saw the weak list: nest, wood_node, spirit_wisp, iron_vein (could read as a hill), moon_resin_tree (a plain pine until the amber drop is coloured)). Town hall: "A: charter scroll". Mine entrance: "A: pickaxe". The B shapes (bell, cart) are dropped from the specs and the silhouette data. Next: draw all 18 in colour, recognisability checks (blind naming with distractors, era pass), owner review folder `~/Work/asset-review/object-markers-v1/`; the owner (not the implementer) runs `adopt-set`.

Registry: 18 keys + 5 aliases (83 keys, 8 aliases, 42,024 B = 9.2 % of `MAX_REGISTRY_BYTES`), 18 specs + the `node` family, style-guide table regenerated, silhouette data `visual_assets/icons/object_marker_silhouettes.yaml` and the sheet tool `tools/visual_assets_object_marker_sheet.py` (test `tests/visual_assets/test_object_marker_silhouettes.py`, 4 passed). The owner's silhouette gate is next (`~/Work/asset-review/object-markers-silhouettes/`); nothing is drawn in colour.



**Drawing and drafts (2026-10-14).** 18 sprites drawn at their approved silhouettes with the `aseprite-pixel-art` tools (first `new_sprite` confirmed the server pin, Aseprite 1.3.18.6; every `export_handoff`, the lint and the preview went through the tools). DEVIATION, recorded: the pixel ops of 17 of the 18 (`apply_ops`) were applied through `visual_assets.drawing.api.apply_ops` (the library the MCP tool wraps, same Lua pin) instead of the MCP tool, to avoid re-typing about 100 KB of pixel rows into tool calls; wood_node was drawn through the MCP tool. 18 intakes PASSED, kept in draft set `object-markers-v1` (`visual_assets/drafts/object-markers-v1/`, verify ok). Superseded intakes of the redraws (rounds 1 to 3) stay in the local quarantine and are not in the set. Review folder `~/Work/asset-review/object-markers-v1/` (4 sheets and a README). Blind check: four rounds (`blind_check/` in the staging artifacts); the final version names 16 of 18 correctly in free text, all 18 in the choice pass (round 1), none modern in the era pass; berry_thicket (read as a beetle in all four rounds) and spirit_wisp (gem or egg) still misread: a silhouette change needs the owner. Compliance table: `compliance.md`.

## Test Summary
**Expected red set until child 4 (`tests/visual_assets`, one run, 2026-10-13: 14 failed, 14 errors, 2488 passed; every other test passes). They fall in three groups: (1) `registry_mismatch` on an export of rc-0010 (the registry changed since it was assembled): the 14 errors and `test_atlas.py::test_the_cli_flag_is_opt_in`; (2) pins of the registry's contents: 65 keys now 83, 36 icon keys now 54, 3 aliases now 8; (3) the spec and style tests that pin 36 icon specs.**

FAILED (14):
- `tests/visual_assets/store/unit/test_atlas.py::test_the_cli_flag_is_opt_in`
- `tests/visual_assets/store/unit/test_registry.py::test_committed_registry_holds_the_adopted_forest_key_one_optional_key_per_other_terrain_code_the_three_border_mask_keys_and_the_36_icon_keys`
- `tests/visual_assets/store/unit/test_registry.py::test_the_committed_registry_carries_a_class_a_structured_fallback_and_35_labels_for_every_key`
- `tests/visual_assets/test_icon_draft_set.py::test_the_set_holds_exactly_the_14_key_set_keys_and_the_registry_holds_those_plus_the_22_v2_keys`
- `tests/visual_assets/test_icon_recognition.py::test_specs_are_complete_consistent_and_match_the_registry`
- `tests/visual_assets/test_icon_release_candidate.py::test_rc_0008_is_rc_0007_plus_exactly_the_36_icon_entries`
- `tests/visual_assets/test_icon_set_adoption.py::test_each_icon_source_is_in_the_catalog_with_its_own_source_and_the_icon_keys_stay_optional`
- `tests/visual_assets/test_icon_specs.py::test_there_is_one_complete_consistent_spec_for_every_registered_icon_key`
- `tests/visual_assets/test_icon_v2_keys.py::test_the_key_set_keys_are_unchanged_and_no_v2_key_collides_with_them`
- `tests/visual_assets/test_key_usage.py::test_the_command_prints_the_report_exits_zero_and_changes_nothing`
- `tests/visual_assets/test_key_usage.py::test_the_real_report_is_deterministic_read_only_and_describes_the_committed_registry`
- `tests/visual_assets/test_sample_map_data.py::test_every_proposed_alias_names_a_registered_key_and_the_registry_carries_exactly_the_three_v2_terrain_aliases`
- `tests/visual_assets/test_sample_map_render.py::test_the_committed_evidence_is_small_and_is_exactly_what_the_tool_produces`
- `tests/visual_assets/test_v2_terrain_aliases.py::test_the_three_aliases_load_and_resolve_to_the_art_that_exists`

ERROR (14):
- `tests/visual_assets/store/unit/test_atlas.py::test_atlas_pngs_pass_the_chunk_allowlist`
- `tests/visual_assets/store/unit/test_atlas.py::test_every_key_of_rc_0010_reads_back_from_its_atlas_with_the_artifact_pixels`
- `tests/visual_assets/store/unit/test_atlas.py::test_the_atlas_options_leave_the_per_file_export_and_the_manifest_unchanged`
- `tests/visual_assets/store/unit/test_atlas.py::test_two_atlas_exports_are_byte_identical`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_an_export_that_differs_by_one_byte_changes_the_tree_hash`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_no_exported_png_carries_a_chunk_outside_the_allowlist`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_the_allowlist_check_fails_on_a_planted_chunk[iTXt]`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_the_allowlist_check_fails_on_a_planted_chunk[tEXt]`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_the_allowlist_check_fails_on_a_planted_chunk[tIME]`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_the_allowlist_check_fails_on_a_planted_chunk[zTXt]`
- `tests/visual_assets/test_release_byte_reproducibility.py::test_two_exports_of_the_committed_candidate_are_byte_identical`
- `tests/visual_assets/test_sample_map_render.py::test_the_page_names_the_view_of_every_number_and_labels_the_aliases`
- `tests/visual_assets/test_sample_map_render.py::test_the_real_render_counts_its_gaps_against_the_data_and_every_png_decodes`
- `tests/visual_assets/test_sample_map_render.py::test_two_renders_of_a_real_world_are_byte_identical`


## Files Changed
- `visual_assets/drafts/object-markers-v1/` (the 18-draft set, from intakes), `visual_assets/icons/object_marker_silhouettes.yaml` (only option A kept), `tests/visual_assets/test_object_marker_silhouettes.py` (one option per slot), this ticket, SEQUENCE.md, staging artifacts (compliance, blind-check evidence, reference study).


## Completion Summary

