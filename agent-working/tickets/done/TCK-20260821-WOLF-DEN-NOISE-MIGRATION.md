---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-WOLF-DEN-NOISE-MIGRATION
phase: done
date: 2026-08-21
tags: [world, content, determinism]
---

# TCK-20260821-WOLF-DEN-NOISE-MIGRATION

## Title
Migrate wolf_den_near_forest world module to the noise-fill terrain mechanism

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Update wolf_den_near_forest — the FOREST-type module the rendering epic's corpus sweep flagged as the most severe composite-rectangle offender — to use the new noise-fill mechanism, as a real, verifiable proof of the schema and compiler work. Its two regions (near_forest and wolf_den) genuinely overlap in the box x:[70,90], y:[30,55], so the migration must make an explicit, deliberate decision about paint-order/overwrite semantics instead of relying on incidental YAML list order.

## Scope
- Update wolf_den_near_forest.yaml's two regions (near_forest, wolf_den) to declare terrain_variants (from the schema and compiler tickets).
- Decide and document an explicit overlap-resolution rule for the genuinely overlapping box x:[70,90], y:[30,55] (e.g. last-declared-wins or explicit priority), replacing today's incidental YAML-list-order behavior.
- Select a secondary terrain value for the noise-fill (open assumption — no existing sparse_forest/clearing-style value exists in the real corpus).
- Confirm the migration compiles deterministically (same seed -> bit-identical terrain+state_hash) and that existing load/normalize/resolve pipeline tests for this module keep passing unmodified.

## Out of Scope
- Fixing the unrelated, pre-existing TERRAIN_COST casing bug (src/core/state.py uses uppercase terrain keys while all real module content authors lowercase strings, so movement-cost differentiation is already silently inert for all real content today) — flagged only, not fixed in this ticket.
- Implementing the schema field or the compiler's noise-consumption mechanism — those are hard prerequisites (TCK-20260821-NOISE-FILL-SCHEMA, TCK-20260821-COMPILER-NOISE-FILL), not this ticket's own work.
- Migrating any world module other than wolf_den_near_forest.

## Acceptance Criteria
- [x] wolf_den_near_forest.yaml's two regions declare the new terrain_variants field with an explicit, documented choice for how the overlap box x:[70,90], y:[30,55] resolves (e.g. last-declared-wins, or explicit priority) — not left to incidental YAML list order.
- [x] Compiling with a fixed seed produces at least one tile inside each region's bounds whose terrain differs from the region's flat single value pre-migration; tiles outside both regions' bounds are unaffected.
- [x] Recompiling the same world+seed twice produces a bit-identical terrain dict and state_hash.
- [x] Existing test_real_content_world_modules.py pipeline tests for this module (load/normalize/resolve) continue passing unmodified.

## Related Tickets
- TCK-20260821-NOISE-FILL-SCHEMA
- TCK-20260821-COMPILER-NOISE-FILL
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260701-HAZARD-KIND-RESOLVER-GAP
- TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE
- TCK-20260701-HAZARD-NATIVE-IMMUNITY
- TCK-20260701-SANDBOX-MONSTER-BALANCE

## Related Docs
- docs/plans/world_generation_organic_terrain_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- data/content/world_modules/wolf_den_near_forest.yaml
- data/content/world_modules/frontier_village_core.yaml
- src/worldbuilding/recipe.py
- src/worldbuilding/compiler.py
- src/worldassembly/resolver.py
- src/core/state.py

## Assumptions / Open Questions
- Secondary terrain type for the noise-fill is an open content-authoring judgment call — no existing value in the real corpus fits 'sub-forest variation' (surveyed: forest x8, plain x5, ruin x2, cave x2, swamp x1, road x1, river x1, mountain x1); 'swamp' is the most plausible reuse candidate (thematically fits a wolf den, already used once elsewhere) but this is not pre-decided by investigation.
- Overlap paint-order resolution (last-declared-wins vs. explicit priority) is genuinely undecided today (incidental YAML order); this ticket must make and document an explicit decision.

## Implementation Notes
Implemented all 4 steps of the approved plan (`staging_artifacts/TCK-20260821-WOLF-DEN-NOISE-MIGRATION/plan.md`) exactly as specified, no deviations.

**Step 1** — Added an identical `terrain_variants` list (`forest` weight=3.0, `swamp` weight=1.0) to both the `near_forest` and `wolf_den` regions in `data/content/world_modules/wolf_den_near_forest.yaml`, plus the exact two-part YAML comment above the `regions:` list documenting (a) the intra-module overlap resolution (wolf_den, declared second, wins the shared `x:[70,90],y:[30,55]` box per `WorldCompiler.compile()`'s declaration-order paint rule) and (b) the cross-module consequence for `bandit_road_trade_pressure`/`goblin_camp_conflict` overlaps in 5 real compositions (accepted, legality-inert). `id`, `type`, `grid_bounds`, flat `terrain`, `hazard_level`, `hazard_kind`, `tags`, and region list order were left byte-identical.

**Step 2** — Added Test #1 (`test_wolf_den_near_forest_declares_terrain_variants`) and Test #5 (`test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`) to `tests/integration/worldassembly/test_real_content_world_modules.py`, placed immediately before `test_real_world_modules_reference_graph_edges_exist`, reusing the existing `repos` fixture. Created `tests/integration/worldassembly/test_wolf_den_noise_migration.py` with Test #2 (`test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation`), Test #3 (`test_wolf_den_overlap_box_resolves_to_wolf_den_terrain`), and Test #4 (`test_wolf_den_near_forest_recompile_same_seed_is_bit_identical`), using the plan's exact `_make_comp()` synthetic composition (`frontier_village_core` + `wolf_den_near_forest`, seed 4242) and module-scoped `compiled_state` fixture. Test #3's RNG-recomputation helper (`_expected_wolf_den_terrain`) matches `compiler.py`'s real `region_hash`/`tile_offset`/`entity_id`/`weighted_choice` formula byte-for-byte (verified against `src/worldbuilding/compiler.py:211-236` and `src/platform/rng.py` before writing). No existing test function body, `MODULE_MATRIX`, or the `repos` fixture were touched.

**Step 3** — Added the "Paint Order for Overlapping Regions" bullet to `docs/mechanics/06_worldbuilding_foundation.md`'s `### Noise-Fill Terrain Law` subsection, immediately after "Non-Declaring Regions" and before "Bounds Clamp Unchanged", exact text per the plan. No other bullet or section touched.

**Step 4** — Re-ran `grep -n "^- id: SUB-3" docs/parity_ledger/substrate.yaml | tail -5` at implementation time (both before and immediately before the write call): highest existing id was still `SUB-385`, confirming `SUB-386` remained free (no sibling ticket claimed it since the plan was written). Added the new entry via `tools/parity_ledger_writer.write_entry()` (no raw YAML edit) with the plan's exact field values. Confirmed `SUB-385` is byte-unchanged via `git diff` (only an append after its closing lines) and that `docs/parity_ledger/substrate.yaml` still parses as valid YAML (398 total entries after the write).

Also ran `graphify update .` (tests/ changed; no topology changes detected) and attempted `make knowledge-index-update` (docs/ changed) — the latter failed with the same pre-existing huggingface.co network-block environment issue investigation.md already flagged at the start of this ticket's own investigation phase ("search_docs/its CLI fallback confirmed broken this session by a huggingface.co network block"); not a regression introduced by this implementation, and not something this ticket's scope can fix.

## Test Summary
Ran the plan's exact scoped verification command via `.venv/bin/python3 -m pytest`:
```
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/worldassembly/test_wolf_den_noise_migration.py \
       tests/integration/content/test_strict_world_matrix.py \
       tests/integration/content/test_resource_region_coverage_corpus.py \
       tests/integration/content/test_swamp_border_pack.py \
       tests/unit/worldbuilding/ \
       tests/certification/test_world_compile_determinism.py \
       -v -m "not slow"
```
Result: **234 passed, 0 failed** (all real-composition tests touching `frontier_marches`/`frontier_extended`/`frontier_living_world`/`lifecycle_full_coverage_world`/`simq_scale_stress_seed42` and every other composition combining `wolf_den_near_forest` with `bandit_road_trade_pressure`/`goblin_camp_conflict` passed with no regressions — the cross-module overlap consequence documented in Decision 3b is confirmed cosmetic, not correctness-breaking).

Also ran `tests/docs/test_doc_integrity.py` per Step 3's Verify instruction (lightweight sanity pass, not part of the blocking scoped command): **10 passed, 1 skipped** (pre-existing skip, unrelated to this ticket).

All 5 new tests (`test_wolf_den_near_forest_declares_terrain_variants`, `test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`, `test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation`, `test_wolf_den_overlap_box_resolves_to_wolf_den_terrain`, `test_wolf_den_near_forest_recompile_same_seed_is_bit_identical`) pass. All pre-existing tests in the touched files, including `test_hazard_kind_survives_module_pipeline`, pass unmodified.

## Files Changed
- `data/content/world_modules/wolf_den_near_forest.yaml` — added `terrain_variants` to both regions + overlap-resolution YAML comment (Step 1)
- `tests/integration/worldassembly/test_real_content_world_modules.py` — added Test #1 and Test #5 (Step 2)
- `tests/integration/worldassembly/test_wolf_den_noise_migration.py` — new file, Tests #2/#3/#4 (Step 2)
- `docs/mechanics/06_worldbuilding_foundation.md` — added "Paint Order for Overlapping Regions" bullet (Step 3)
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-386` via `write_entry()` (Step 4)
- `tickets/inprogress/TCK-20260821-WOLF-DEN-NOISE-MIGRATION.md` — this file, updated with implementation results

No changes were made to `staging_artifacts/TCK-20260821-WOLF-DEN-NOISE-MIGRATION/plan.md`, `investigation.md`, or `test_plan.md` during this Implement phase — all three were already finalized (plan approved post-Review) before implementation began, and implementation followed the plan with zero deviations, so no "Deviations" section was needed in `plan.md`.

## Completion Summary
Migrated `wolf_den_near_forest.yaml`'s `near_forest` and `wolf_den` regions onto the live `terrain_variants` noise-fill mechanism (forest weight=3.0, swamp weight=1.0), with the intra-module overlap box `x:[70,90],y:[30,55]` resolving to `wolf_den`'s terrain via the pre-existing declaration-order paint rule, now explicitly documented in both the module's YAML comment and the Mechanics Bible. Added 5 new tests proving field preservation, per-tile variation, overlap-winner identity (via exact RNG recomputation), and bit-identical same-seed recompilation, plus a new parity ledger entry (`SUB-386`). All 234 tests in the plan's scoped verification command pass, including every real composition where this migration's cross-module overlap consequence (documented and accepted as legality-inert in Decision 3b) is actually exercised.
