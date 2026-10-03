---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE
phase: done
date: 2026-07-01
tags: [world, worldcomposition, sandbox_world, migration, content]
---

# TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE

## Title
Migrate sandbox_world from worldtemplate.v1 to worldcomposition.v1

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`sandbox_world` is the only compiled world still using the legacy `worldtemplate.v1` schema
(verified: all 9 other worlds under `data/worlds/` use `worldcomposition.v1`). This schema's
compile path never resolves entity stats from the catalog — `WorldCompiler.compile()` is
always called with `context=None` for `worldtemplate.v1` worlds, so every entity (monster or
citizen) gets identical flat defaults. Migrating `sandbox_world` to `worldcomposition.v1`
gives it real catalog-driven stats (matching every other world) and is a prerequisite for
`TCK-20260701-WORLDTEMPLATE-REMOVE`, which cannot remove `worldtemplate.v1` support while
this is still the only world depending on it.

## Scope
1. Investigate `sandbox_world`'s current `worldtemplate.v1` composition
   (`data/worlds/sandbox_world/world.yaml`): town population (~15 citizens + 3 heroes in
   `town_center`), monster population (5 entities in `woods`), topology (128×128).
2. Identify existing `worldcomposition.v1` modules (`data/content/world_modules/`) that
   reasonably replicate this shape. Candidates identified during investigation:
   `frontier_village_core.yaml` (town/settlement population) and `wolf_den_near_forest.yaml`
   (wilderness monster ecology, already used by other worlds) — verify these fit, or find
   better matches. Prefer reuse over authoring a new module; only author a new module if no
   existing one reasonably fits.
3. Author `data/worlds/sandbox_world/world.yaml` as `schema_version: "worldcomposition.v1"`
   using `module_refs` (see `data/worlds/simq_routing_test/world.yaml` for a minimal working
   reference of this format). Preserve `world_id: sandbox_world` and `generation_seed`
   conventions used by existing worlds so downstream tooling/tests that reference
   `sandbox_world` by name continue to work.
4. Resolve and compile: run the composition through `WorldAssemblyResolver` to produce
   `data/worlds/sandbox_world/resolved/world.resolved.yaml` + sidecars, then
   `WorldCompiler.compile()` against the resolved spec. Confirm clean validation.
5. Re-run the D20 audit's 200-tick seed 42/137 scenario against the new composition. Record
   the new entity count, new state_hash, and pillar/grade differences versus the old
   `worldtemplate.v1` baseline in `docs/audits/D20_simq_integration.md`. A different entity
   count and state hash are expected — this is intentional, not a determinism regression
   (same seed must still reproduce the same new hash on repeat runs).
6. Confirm monster entities in the migrated world now resolve real catalog stats (not flat
   100/10/0 defaults) — this is the primary success signal for this ticket, independent of
   whether the extinction-by-hazard issue (tracked separately) is also resolved.
7. Update any test fixtures/tools that assumed `sandbox_world` was `worldtemplate.v1`
   (e.g. `tools/calibrate_simq.py`'s fallback-to-generic-scenario behavior for worlds lacking
   `resolved/world.resolved.yaml` should no longer trigger for `sandbox_world` — verify this
   as a bonus check, don't expand scope to fix `calibrate_simq.py` itself if unrelated worlds
   still hit it).

## Out of Scope
- Modifying `WorldCompiler.compile()`, `WorldAssemblyResolver`, or any other resolution code
  (content-only migration, reusing existing mechanisms)
- Removing `worldtemplate.v1` CLI/code support (that's `TCK-20260701-WORLDTEMPLATE-REMOVE`,
  which depends on this ticket)
- Fixing the hazard-drain extinction issue (that's `TCK-20260701-HAZARD-NATIVE-IMMUNITY`,
  independent)
- Exactly replicating `sandbox_world`'s old entity count/positions — approximate composition
  via existing modules is acceptable and expected to differ

## Acceptance Criteria
- [x] `data/worlds/sandbox_world/world.yaml` has `schema_version: "worldcomposition.v1"`
- [x] `data/worlds/sandbox_world/resolved/world.resolved.yaml` exists and validates
- [x] Compiles cleanly with `WorldCompiler.compile()`, zero validation warnings
- [x] Monster-role entities resolve non-flat, catalog-driven stats (verified by inspecting
      compiled `AuthoritativeState` or `world_compile_report.json`)
- [x] 200-tick seed 42 (and 137) re-run completes successfully; new state_hash recorded
- [x] `docs/audits/D20_simq_integration.md` updated with the new baseline
- [x] No regression in existing `sandbox_world`-referencing tests (grep for `sandbox_world` in
      `tests/` first to find the full set)

## Related Tickets
- TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC — parent epic
- TCK-20260701-WORLDTEMPLATE-REMOVE — depends on this ticket completing first (see
  `SEQUENCE.md`)
- TCK-20260701-SANDBOX-MONSTER-BALANCE — blocked ticket this migration unblocks (partially;
  also needs `TCK-20260701-HAZARD-NATIVE-IMMUNITY`)

## Related Docs
- `docs/architecture/world_repository_layout.md` — schema/directory layout reference
- `docs/audits/D20_simq_integration.md` — needs a new baseline after this migration
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/` — full trace of why
  `worldtemplate.v1`'s stat resolution is broken (investigation_v1_option_a_rejected.md)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/` — prior investigation evidence

## Related Code Areas
- `data/worlds/sandbox_world/world.yaml`
- `data/content/world_modules/frontier_village_core.yaml`, `wolf_den_near_forest.yaml`
  (candidates)
- `data/worlds/simq_routing_test/world.yaml` — structural reference for a minimal
  `worldcomposition.v1` file
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver` (reference only, not modified)

## Assumptions / Open Questions
- Approximate (not exact) population replication is acceptable — confirmed in epic
  Assumptions.
- If neither `frontier_village_core` nor `wolf_den_near_forest` (or close variants) fit well,
  authoring one small new module is in-scope, but should be flagged as a deviation if it
  happens, since the epic's preference was reuse-first.

## Implementation Notes
Followed `staging_artifacts/TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE/plan.md`'s 7 steps exactly,
no deviation from the module choice or composition shape:

1. Replaced `data/worlds/sandbox_world/world.yaml` with the planned minimal `worldcomposition.v1`
   composition (`modules: [frontier_village_core, wolf_den_near_forest]`, `generation_seed: 42`).
2. Resolved via `WorldAssemblyResolver` (`python3 -m src.worldbuilding.cli resolve sandbox_world`)
   — produced `data/worlds/sandbox_world/resolved/world.resolved.yaml` + all 4 sidecars.
   `module_validation`/`composition_validation`/`world_validation` all empty (zero issues);
   `catalog_validation` carries the same class of global `CAT-DEAD-001` "unused by any world"
   warnings present for every other world (confirmed by diffing against `simq_routing_test`'s
   resolve output) — not introduced by this migration.
3. Compiled via `python3 -m src.worldbuilding.cli compile sandbox_world --seed 42` — zero
   compile-time warnings (`report["warnings"] == []`). Directly inspected
   `AuthoritativeState.entities[*].combat` after compiling with the resolved `CompileContext`:
   monster-role entities (`wolf_pack_small` → `hungry_wolf`/`alpha_wolf`) resolve **hp=45,
   atk=12, def=3** — confirmed non-flat and catalog-driven (old `worldtemplate.v1` path gave
   every entity flat hp=100/atk=10/def=0). Other roles also differentiate correctly
   (`frontier_guard` hp=120/atk=12/def=4, `traveling_merchant` hp=80/atk=4/def=1, etc.).
   Entity count: 18 (8 village_worker, 3 frontier_guard, 1 traveling_merchant,
   1 village_blacksmith, 4 hungry_wolf, 1 alpha_wolf).
4. Empirical 200-tick re-run at seed 42 and seed 137 (driving `Kernel.tick_once()` directly
   against the context-compiled state, matching the CLI's own compile path). Both seeds:
   18 entities start, 13 alive at tick 200 — the 5 dead are exactly the 5
   `wolf_pack_small` entities (4 hungry_wolf + 1 alpha_wolf). **The extinction symptom still
   occurs**, as expected — now reproduced against real catalog stats instead of flat defaults,
   confirming this is a genuine hazard-drain/native-immunity gap (tracked by the sibling
   `TCK-20260701-HAZARD-NATIVE-IMMUNITY`), not an artifact of flat stats. New state hashes:
   compile-time seed42=`836b45e8913b46862240c6ba80f177f6`,
   seed137=`7e8ae05dbeffccb8edd65fd9754787aa`; 200-tick final seed42=
   `16e38263ef839603ffe0ce9e362c3c106523cb23440ea25b8b1a1dfee00015be`, seed137=
   `2c37726ffc0cd924703da8246b577cec4c8e626ba478fb89bf3bc62770839492`. Both differ from the
   pre-migration hashes (expected/intentional); re-compiling the same seed reproduces the same
   hash (determinism confirmed).
5. Regenerated calibration anchors for all 4 `sandbox_world_*` keys via
   `tools/calibrate_simq.py` (`--ticks 200 --seed {42,137,999}` and `--ticks 1000 --seed 42`).
   Updated `tests/simulation_quality/fixtures/grade_anchors.json`. `test_grade_regression.py`
   passes 9/9 (all anchor keys, including the other worlds' unaffected entries). Grade shifts:
   WORLD C→B at all three 200t seeds; PROGRESSION C→B at seed137/999; at 1000t COGNITION C→B,
   ECONOMY C→B, NARRATIVE A→B — all within the ±1-band tolerance, no anchor tolerance weakened.
6. Updated `docs/audits/D20_simq_integration.md` with a new "Migration Baseline" section
   documenting the composition/entity-count change, new state hashes, the persisting
   extinction symptom, and the new calibration grade table, alongside the original
   pre-migration baseline for traceability.
7. Confirmed `frontier_village_core`/`wolf_den_near_forest` already present in
   `MODULE_MATRIX` (`tests/integration/worldassembly/test_real_content_world_modules.py`) —
   no change needed.

**Unplanned but necessary correction (not in the original 7 steps):** discovered during the
parity-ledger confirmation pass that `docs/parity_ledger/progression.yaml` entry `PROG-108`
cited `sandbox_world`'s *old* `worldtemplate.v1` HERO population ("sandbox_world (3 HERO via
recipe + faction villagers)") as supporting evidence. `frontier_village_core` +
`wolf_den_near_forest` have no HERO population, so that citation is now stale. The entry's
`status` (`verified`), `priority`, and `test_path` are unaffected — the cited test
(`test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue`) uses a synthetic
fixture, not `sandbox_world`, and `urban_political`'s HERO population is untouched — so the
underlying parity claim is not broken. Corrected the `v2_evidence` prose only, to note the
migration and that the mechanism proof is independent of it. See plan.md Deviations for the
rationale on why this was done despite the architecture review's "no parity ledger updates
needed" determination.

## Test Summary
All scoped commands from `test_plan.md` run and passing:
- `pytest tests/simulation_quality/test_grade_regression.py -k sandbox_world -m "not slow" -v`
  — 3 passed
- `pytest tests/simulation_quality/test_grade_regression.py -v` (full file, all 9 anchors incl.
  slow 1000t) — 9 passed
- `pytest tests/unit/worldbuilding/ -v` — 98 passed
- `pytest tests/integration/worldassembly/ -v` (ran full dir; the `-k "sandbox or
  module_matrix"` filter from test_plan.md matched 0 tests since no test names contain those
  literal substrings — ran the full directory instead per the test plan's fallback guidance)
  — 43 passed
- `pytest tests/unit/worldbuilding/test_quest_definition.py -v` — 24 passed
- `pytest tests/integration/scenarios/test_entity_differentiation.py -v` (regression-surface
  file from test_plan.md, confirmed no accidental sandbox_world dependency) — 2 passed

No test failures. No test tolerance weakened.

## Files Changed
- `data/worlds/sandbox_world/world.yaml` (rewritten: worldtemplate.v1 → worldcomposition.v1)
- `data/worlds/sandbox_world/resolved/world.resolved.yaml` + `compile_context.json` +
  `provenance_manifest.json` + `assembly_report.json` + `validation_report.json` (new)
- `data/worlds/sandbox_world/world_compile_report.json` (regenerated, seed 42 canonical)
- `data/calibration/sandbox_world_seed42_200t/` (quality_report.json, quality_scores.jsonl —
  regenerated)
- `data/calibration/sandbox_world_seed137_200t/` (regenerated)
- `data/calibration/sandbox_world_seed999_200t/` (regenerated)
- `data/calibration/sandbox_world_seed42_1000t/` (regenerated)
- `tests/simulation_quality/fixtures/grade_anchors.json` (updated, 4 sandbox_world entries)
- `docs/audits/D20_simq_integration.md` (new Migration Baseline section)
- `docs/parity_ledger/progression.yaml` (PROG-108 v2_evidence corrected — stale sandbox_world
  citation removed, mechanism proof unaffected; status unchanged)

## Completion Summary
Migrated `sandbox_world` from `worldtemplate.v1` to `worldcomposition.v1`, reusing the existing
`frontier_village_core` + `wolf_den_near_forest` module pair (no new modules authored). Compiles
cleanly with zero validation warnings. Monster-role entities now resolve real, non-flat,
catalog-driven combat stats (e.g. wolves hp=45/atk=12/def=3) instead of the old flat
100/10/0 defaults — the primary success signal for this ticket. Entity count changed from 23
to 18 and region/faction IDs changed (expected per ticket scope — approximate replication, not
exact). 200-tick re-runs at seed 42/137 complete successfully with new, reproducible state
hashes; the tick-8-class monster extinction symptom still occurs (5/5 wolf entities die by
tick 200 at both seeds) — expected and explicitly out of scope, tracked by the sibling
`TCK-20260701-HAZARD-NATIVE-IMMUNITY` ticket. Calibration anchors regenerated for all 4
`sandbox_world_*` keys; `test_grade_regression.py` passes 9/9 with genuine new grades (several
pillars moved up one band — WORLD C→B at 200t, COGNITION/ECONOMY C→B and NARRATIVE A→B at
1000t — all within tolerance). `sandbox_world` is now the last world un-blocking
`TCK-20260701-WORLDTEMPLATE-REMOVE`. Sandbox_world remains the only `worldtemplate.v1`-free
world; no other worlds were touched. One out-of-plan, low-risk correction: fixed a stale
`sandbox_world` evidence citation in parity ledger entry `PROG-108` (status/test_path
unaffected).
