---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-COMPILER-NOISE-FILL
phase: done
date: 2026-08-21
tags: [world, determinism]
---

# TCK-20260821-COMPILER-NOISE-FILL

## Title
Consume seeded noise in WorldCompiler's region-painting loop for declared terrain variants

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend WorldCompiler.compile()'s region-painting loop to consult a seeded noise field when a region declares terrain variants, thresholding into per-tile terrain types within the region's existing bounds, without letting unrelated worlds' golden hashes shift. The original framing asked to "settle draw-sequence ordering," but investigation found DeterministicRNG is a stateless composite-key hash, not a sequential stream — the real requirement is choosing a collision-free RNG Domain namespace for the new draws. Must preserve existing bounds-clamping and town_tiles membership logic exactly.

## Scope
- Extend WorldCompiler.compile()'s region-painting loop (src/worldbuilding/compiler.py) to consult a seeded noise field when a region's terrain_variants (from TCK-20260821-NOISE-FILL-SCHEMA) is populated, thresholding into per-tile terrain within the region's existing bounds.
- Key noise-fill RNG draws under a distinct Domain from Domain.WORLD (e.g. Domain.INIT, already registered) rather than sequencing within Domain.WORLD's existing entity/resource/building draw order — this replaces the epic's original "settle draw-sequence ordering" framing, since DeterministicRNG is a stateless composite-key hash, not a sequential stream.
- Preserve the existing bounds-clamp and town_tiles membership logic unchanged for both variant-declaring and non-declaring regions.
- Verify unrelated worlds' golden hashes (certification corpus) are unaffected.

## Out of Scope
- Adding the terrain_variants field to RegionRecipeSpec/RegionSpec — that is TCK-20260821-NOISE-FILL-SCHEMA, a hard prerequisite for this ticket.
- Migrating any real world module (e.g. wolf_den_near_forest) to declare variants — that is TCK-20260821-WOLF-DEN-NOISE-MIGRATION.
- Authoring the dedicated golden-hash tile-level regression test — that is TCK-20260821-NOISE-FILL-DETERMINISM-TEST (this ticket only needs to keep the existing determinism tests passing).
- Documentation updates to docs/mechanics/06_worldbuilding_foundation.md, the substrate.yaml parity ledger entry, and docs/guidelines/intentional_divergences.md are required in-session per the Authoritative Mechanics Rule, but are follow-through on this ticket's own change, not a separately deferred scope item.

## Acceptance Criteria
- [x] Compiling any world spec where no region declares variants produces a bit-identical state_hash and coordinates to pre-change output, verified against the certification corpus.
- [x] When a region declares variants, compiling twice with the same seed produces identical per-tile terrain assignment within bounds; compiling with different seeds produces a measurably different distribution within the same bounds.
- [x] Noise-filled terrain never writes outside region bounds or exceeds topology width/height — the existing clamp continues to gate every write.
- [x] town_tiles membership for a variant-declaring town region is unaffected by which terrain string the noise-fill assigns — still driven solely by r_spec.type == "town".
- [x] Noise-fill draws are keyed under a distinct RNG Domain (e.g. Domain.INIT) from Domain.WORLD's existing entity/resource/building draws, eliminating collision risk by construction rather than by draw-order sequencing.

## Related Tickets
- TCK-20260821-NOISE-FILL-SCHEMA
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260820-EPIC-WORLD-RENDERING-CORE
- TCK-20260523-WORLD-COMPILER
- TCK-20260619-P0-ENTITY-INIT
- TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/parity_ledger/substrate.yaml
- docs/guidelines/intentional_divergences.md
- docs/world/compiler_contract.md
- docs/plans/world_generation_organic_terrain_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/platform/rng.py
- src/worldbuilding/schema.py
- src/worldbuilding/recipe.py
- src/worldassembly/resolver.py
- src/core/enums.py
- tests/unit/worldbuilding/test_world_compiler.py
- tests/certification/test_world_compile_determinism.py
- data/content/world_modules/wolf_den_near_forest.yaml
- data/content/world_modules/forest_warden_grove.yaml

## Assumptions / Open Questions
- Domain.INIT is the recommended noise-fill key namespace per investigation (confirmed registered, confirmed no collision risk since compile()'s RNG instance is distinct from Kernel's own); final confirmation of the exact Domain value happens during implementation.

## Implementation Notes

Implemented all 5 steps of the APPROVED `staging_artifacts/TCK-20260821-COMPILER-NOISE-FILL/plan.md` exactly as specified, with no deviations.

**Step 1** — `src/worldbuilding/compiler.py`'s region-painting loop (previously lines 214-221) now branches on `r_spec.terrain_variants`. When populated, `region_hash` is computed once per region (`region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF` over `r_spec.id`), then per in-bounds tile: `tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)` (the corrected 16-bits-per-axis encoding from the Review round), `entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF`, and `rng.weighted_choice(Domain.INIT, tick=0, entity_id=entity_id, seq=[...], weights=[...], sub_id=1)` picks the tile's terrain. When not populated (`None` or `[]`, both falsy), the flat `r_terrain` fill is used exactly as before. The bounds clamp (`0 <= x < spec.topology.width and 0 <= y < spec.topology.height`) and the `if r_spec.type == "town": town_tiles.add((x, y))` line are untouched, executing identically regardless of branch.

**Step 2** — Added all 10 new tests to `tests/unit/worldbuilding/test_world_compiler.py`, immediately before `test_compiler_faction_bravery_bias_produces_real_action_style_skew` (matching plan's file-placement decision for test #8 — kept in this file, not a new `tests/architecture/` file, since that directory's existing convention is static source scans, not behavioral RNG-output assertions). Test #10 (`test_compiler_terrain_variants_tile_offset_injective_across_wide_regions`) constructs a region spanning `y` in `[0, 300]` (topology `height=305`, 1,806 in-bounds tiles). **Architecture-Verify caught that the first version of this test was vacuous** — it discarded `compile()`'s return value and only asserted self-consistency of a standalone recomputation of the tile-offset formula in the test body, never exercising `compiler.py`'s real code path; it would have passed unchanged even with the original buggy `(x << 8) | y` encoding still in place. Fixed by patching `DeterministicRNG.weighted_choice` to spy on the real `entity_id` values `compiler.py` actually computes and passes during a real `compile()` call, then asserting those captured values are unique. Verified genuinely regression-guarding by temporarily reverting `compiler.py`'s `tile_offset` line to `(x << 8) | y` and confirming the test fails (1536 unique of 1806 expected, real collisions detected), then restoring the correct code and confirming it passes again.

**Step 3** — Added a "Noise-Fill Terrain Law" subsection to `docs/mechanics/06_worldbuilding_foundation.md` under `## 2. Regional Boundaries & Sovereignty`, immediately after the existing `### Spatial Laws` subsection, documenting the variant-declaring/non-declaring behavior split, the unchanged bounds clamp, unchanged `town_tiles` membership rule, and citing `src/worldbuilding/compiler.py` as implementing code.

**Step 4** — Flipped `SUB-385` in `docs/parity_ledger/substrate.yaml` to `status: verified` via `tools/parity_ledger_writer.write_entry()` (never raw Edit), preserving `id`/`text`/`priority`/`support_boundary` verbatim per the plan's explicit instruction, updating only `status`, `v2_evidence`, and `test_path`. Ran `git status`/`git diff` on the shard immediately before the write and confirmed it was clean (no concurrent session had an uncommitted change in flight). Confirmed via `git diff` after the write that exactly one hunk changed, touching only the `SUB-385` entry — no other of the shard's ~2050 entries were touched. `write_entry()`'s in-process `parity_index.py build()` call succeeded (`entry_count: 2051`, `shard_count: 9`).

**Step 5** — Appended `### 2.46 Noise-Fill Terrain Draws Namespaced Under Domain.INIT, Not Domain.WORLD (TCK-20260821-COMPILER-NOISE-FILL)` to `docs/guidelines/intentional_divergences.md`, immediately after `### 2.45` and before `## 3. Unsupported / Retired Behavior`. Confirmed `2.46` was still the next available number at implementation time (highest existing entry was still `2.45`, no other session had added entries since planning). Rationale class **Bounded**, `Status: ACTIVE`, cites test #8 as Verification per the plan.

No deviations from the plan were necessary at any step — no separate "Deviations" section was added to `staging_artifacts/TCK-20260821-COMPILER-NOISE-FILL/plan.md`.

One environment-only note, not a ticket deviation: `make knowledge-index-update` (run per the Workflow Rule's "After Work" step, since `docs/` files were modified) failed locally with `OSError: We couldn't connect to 'https://huggingface.co'` — this is the pre-existing, already-documented u24desktop environment gap (no network access for the sentence-transformers embedding model download; project memory already tracks an SSL-cert fix as needed for HuggingFace downloads on this machine). Not caused by, or related to, this ticket's code changes; docs content itself is correct and complete.

## Test Summary

All tests run with `.venv/bin/python3 -m pytest` (bare `python3` lacks pydantic in this environment).

- `pytest tests/unit/worldbuilding/test_world_compiler.py -v` — 41 passed (31 pre-existing unmodified + 10 new), 0 failed.
- `pytest tests/docs/test_doc_integrity.py -v` — 10 passed, 1 skipped (pre-existing skip, unrelated), 0 failed. Confirms the Step 3/Step 5 doc edits did not break structural/link/terminology integrity checks.
- `pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py -v` (plan's first scoped command) — **136 passed, 0 failed.**
- `pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py tests/integration/kernel/test_phase2_determinism.py -v -m "not slow"` (plan's second scoped command) — **163 passed, 0 failed.**

No pre-existing test failed or needed investigation; no flakiness observed. All 4 personality/bravery/action-style regression-surface tests named in test_plan.md (`test_compiler_faction_bravery_bias_produces_real_population_skew`, `test_compiler_faction_bravery_bias_produces_real_action_style_skew`, plus the `Domain.INIT`/`Domain.WORLD` separation guards in `test_phase2_determinism.py::TestDomainEnum`) passed unmodified, confirming `Domain.WORLD`'s existing draw sequence is untouched.

## Files Changed

- `src/worldbuilding/compiler.py` — Step 1: branched region-painting loop.
- `tests/unit/worldbuilding/test_world_compiler.py` — Step 2: added 10 new tests.
- `docs/mechanics/06_worldbuilding_foundation.md` — Step 3: added "Noise-Fill Terrain Law" subsection under `## 2. Regional Boundaries & Sovereignty`.
- `docs/parity_ledger/substrate.yaml` — Step 4: `SUB-385` flipped to `status: verified` (written via `tools/parity_ledger_writer.write_entry()`, not raw Edit).
- `docs/guidelines/intentional_divergences.md` — Step 5: added `### 2.46` entry.
- `docs/world/compiler_contract.md` — Document-Update phase: added `terrain_variants` to `RegionSpec`/`RegionRecipeSpec` field listings and a new "Terrain fill (step 2)" paragraph describing the `Domain.INIT` noise-fill branch; bumped `last_verified`.
- `docs/plans/world_generation_organic_terrain_epic.md` — Document-Update phase: appended "Update (TCK-20260821-COMPILER-NOISE-FILL, closed 2026-08-21)" status blocks to epic child-ticket items 1 and 2 (item 1's block backfills a gap missed by the prior ticket in this batch, TCK-20260821-NOISE-FILL-SCHEMA).
- `tickets/inprogress/TCK-20260821-COMPILER-NOISE-FILL.md` — this file: Status, Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion Summary.

No changes were made to `staging_artifacts/TCK-20260821-COMPILER-NOISE-FILL/plan.md`, `investigation.md`, or `test_plan.md` during this Implement run — all three staging artifacts were already created and approved in a prior session/phase before this implementer run started, and the plan's own code blocks were followed exactly with no deviation requiring a "Deviations" addendum.

## Completion Summary

Extended `WorldCompiler.compile()`'s region-painting loop so that a region declaring `terrain_variants` gets per-tile terrain sampled deterministically via `DeterministicRNG.weighted_choice()` under `Domain.INIT` (using a collision-free 16-bits-per-axis tile-offset encoding, corrected during Review), while non-declaring regions keep the exact prior flat-fill behavior. Added 10 new tests proving determinism, seed-sensitivity, bounds-safety, weight-respect, `Domain.WORLD` isolation, empty-list handling, and tile-offset injectivity; all pre-existing tests in the affected suites (163 total across the two required scoped pytest commands) pass unmodified. Updated the Mechanics Bible, flipped parity ledger entry `SUB-385` to `verified` with real evidence/test-path via the authoritative writer tool, and recorded the `Domain.INIT` namespacing choice as intentional divergence `2.46`.
