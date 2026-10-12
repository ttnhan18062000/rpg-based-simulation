---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES
phase: open
date: 2026-10-12
tags: [architecture, testing]
---

# TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES

## Title
Terrain variants: registry aliases for the V2 terrain names (plain, ruin, river) onto existing art

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. The asset half of #523: V2 names are canonical, existing art is reused through aliases.

## Scope
- Add to `visual_keys.yaml` `aliases`: `terrain.plain -> terrain.grassland`, `terrain.ruin -> terrain.ruins`, `terrain.river -> terrain.shallow_water`. Comment: owner answer on #523 (2026-10-12), V2 names canonical.
- **`PLAIN`:** an alias must match the lowercase key pattern (`visual_assets/store/identities.py:16`), so `terrain.PLAIN` cannot exist. The name -> key rule lowercases (the sample-map tool's rule), so `PLAIN` and `plain` both resolve through `terrain.plain`. Write this rule in store_contract.md as the asset side of the contract with rpg, and state that the dedupe is rpg's.
- Check what the runtime manifest / export carries for aliases. If a client could not resolve an alias from the export, record it as a finding for activation (no store-code change here).
- Tests: the three aliases resolve; no chain, no alias that is also a key (the loader's own rules); the registry content pins move to exact values.
- Registry edit -> rc-0009 becomes unexportable (known gap). Expected red until child 4's rc-0010, as in the real-art batch: list exactly which tests, nothing else may fail.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] Three aliases load and resolve; the name rule documented.
- [ ] The known red set listed exactly in the Test Summary; nothing else red.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN` (design approved)

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `docs/assets/store_contract.md`, `tests/visual_assets/**`

## Assumptions / Open Questions
- If rpg's dedupe later keeps `PLAIN` (uppercase), the lowercase rule still covers it; no registry change needed.

## Implementation Notes
- `visual_keys.yaml`: three aliases `terrain.plain -> terrain.grassland`, `terrain.ruin -> terrain.ruins`, `terrain.river -> terrain.shallow_water`, with a comment citing the owner's answer on #523 (V2 names canonical), the lowercasing name rule, rpg's dedupe and that the aliases are registry-only. The file is 30,206 B with comments (6.6 % of `MAX_REGISTRY_BYTES`); no key, no bound, no schema field added. They load and resolve (`Registry.resolve`).
- `PLAIN`: `terrain.PLAIN` cannot exist (`identities.py` `VISUAL_KEY_PATTERN` is lower case), so the name -> key rule lowercases and `PLAIN` and `plain` both resolve through `terrain.plain`. Written in `docs/assets/store_contract.md`, new section "V2 terrain names and the name -> key rule", with the four-point rule, rpg's dedupe (#523) and lead's matching requirement (no two V2 terrain names may differ only by case, checked when rpg publishes the vocabulary); if `PLAIN` stays, the lowercase rule still covers it with no registry change.
- OWNER ANSWER (2026-10-12, asked directly, neutral options): "Registry-only aliases". The runtime check this ticket asked for found: registry aliases have exactly one consumer, `visual_assets/review/key_usage.py:85-86`; `ReleaseCandidateManifest` and `RuntimeManifest` have no alias field and the client (`manifest.ts`, `resolver.ts`) reads none, so a client asking for `terrain.plain` finds no entry. Stated plainly in `store_contract.md` Known gaps ("registry aliases are not carried by a release, the runtime export or the client; a runtime consumer is needed at activation", cited to #523). No store or client change here. The sample-map re-render in child 4 may resolve names through `Registry.resolve` (offline tool); its page and the gap report must say the live client does not.
- Tests: new `tests/visual_assets/test_v2_terrain_aliases.py` (7): the three resolve to existing art, no alias is a key, no chain, a target exists, `terrain.PLAIN` is refused by the key pattern and the lowercasing rule maps both names to `terrain.plain`, the release and runtime records carry no alias field (the Known gap as a test), key-usage is the one consumer. Registry-content pins moved to exact values: `adopted_facts.REGISTRY_ALIASES`, `test_registry.py` (alias pin exact), `test_sample_map_data.py` (the registry carries exactly the three aliases and the sample-map tool's lowercased terrain proposals equal them).
- KNOWN RED until child 4's rc-0010 (a registry edit makes rc-0009 unexportable, `registry_mismatch`), exactly 16 tests, all exporting the committed candidate; see the Test Summary. Nothing else may fail.

## Test Summary
`tests/visual_assets` (project venv): 2481 passed, 2 failed, 14 errors = EXACTLY 16 expected-red tests, all `BuildError registry_mismatch` on an export of the committed rc-0009, to be turned green by child 4's rc-0010 (owner-gated):
- `store/unit/test_atlas.py` (5): `test_atlas_pngs_pass_the_chunk_allowlist`, `test_every_key_of_rc_0009_reads_back_from_its_atlas_with_the_artifact_pixels`, `test_the_atlas_options_leave_the_per_file_export_and_the_manifest_unchanged`, `test_the_cli_flag_is_opt_in`, `test_two_atlas_exports_are_byte_identical`.
- `test_release_byte_reproducibility.py` (7): `test_an_export_that_differs_by_one_byte_changes_the_tree_hash`, `test_no_exported_png_carries_a_chunk_outside_the_allowlist`, `test_the_allowlist_check_fails_on_a_planted_chunk[iTXt|tEXt|tIME|zTXt]` (4), `test_two_exports_of_the_committed_candidate_are_byte_identical`.
- `test_sample_map_render.py` (4): `test_the_committed_evidence_is_small_and_is_exactly_what_the_tool_produces`, `test_the_page_names_the_view_of_every_number_and_labels_the_aliases`, `test_the_real_render_counts_its_gaps_against_the_data_and_every_png_decodes`, `test_two_renders_of_a_real_world_are_byte_identical` (they export rc-0009 to render it).
Nothing else is red. `test_v2_terrain_aliases.py` 7 passed; `test_budgets_parity.py` passed.

## Files Changed
- `visual_assets/catalog/definitions/visual_keys.yaml` (3 aliases, comment), `docs/assets/store_contract.md` (name rule section, Known gap), `tests/visual_assets/test_v2_terrain_aliases.py` (new), `tests/visual_assets/adopted_facts.py`, `tests/visual_assets/store/unit/test_registry.py`, `tests/visual_assets/test_sample_map_data.py`

## Completion Summary

