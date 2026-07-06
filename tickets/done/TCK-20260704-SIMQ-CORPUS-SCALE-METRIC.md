---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCALE-METRIC
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, corpus, faction]
---

# TCK-20260704-SIMQ-CORPUS-SCALE-METRIC

## Title
Track "distinct populated factions" as an explicit per-world scale metric

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that
"distinct factions actually assigned to a population" ranges 2-9 across the 10 worlds under
`data/worlds/` (`wilderness_survival`: 2, `frontier_extended`: 9), and that this is a genuine,
currently-untracked per-world scale axis — distinct from `AuthoritativeState.factions`, which is
always the full 16-entry catalog regardless of content and therefore not meaningful as a per-world
signal on its own (investigation.md §2, table note: "Factions in catalog" is a global constant).
`world_compile_report.json` already tracks entity/region/resource-node/building/quest counts per
world but has no field for populated-faction count. This ticket adds it, per investigation.md §4
open question 1.

## Scope
1. Locate the `world_compile_report.json` generation code path (likely `WorldCompiler.compile()` or
   a report-writing helper it calls) and add a `distinct_populated_factions` field — the count of
   unique faction IDs actually assigned to at least one entity's population in the compiled world
   (matching the definition used in investigation.md §2's table, not the raw catalog count).
2. Verify the new field against investigation.md §2's table for all 10 existing worlds as a
   correctness check (e.g. `wilderness_survival` → 2, `frontier_extended` → 9) — recompile each
   world and confirm the generated report matches the investigation's numbers exactly, or document
   and resolve any discrepancy found.
3. Add a corresponding row/column to `docs/simulation_quality/eval_matrix_results.md`'s world-scale
   reporting section, alongside the existing entity/region/resource-node scale reporting.
4. Add a unit test (likely alongside or extending
   `tests/unit/worldassembly/test_corpus_diversity.py`, created by
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`) asserting the new field is present and numerically
   correct for at least 2-3 of the existing worlds with known faction counts from the investigation
   table.
5. Recompile all 10 worlds under `data/worlds/` so `world_compile_report.json` picks up the new
   field (content/report regeneration only — no world.yaml changes, no calibration grade changes
   expected since this is purely additive reporting).
6. Run `make evaluate --dry-run` to confirm zero grade regressions (this ticket should not change
   any pillar score, only add a reporting field).

## Out of Scope
- Authoring any new worlds (that is tickets 4-8 in this batch) — this ticket only instruments
  existing worlds and the reporting pipeline
- Changing faction assignment logic, `FactionState`, or `WorldCompiler`'s faction-resolution
  behavior — this is a read-only count derived from already-resolved state, not a new mechanic
- Adding the metric to any SimQ pillar's scoring formula (this is a diagnostic/reporting metric, not
  a scored signal — do not conflate with FACTION pillar scoring)

## Acceptance Criteria
- [ ] `world_compile_report.json` includes a `distinct_populated_factions` field for every
      compiled world
- [ ] Field value matches investigation.md §2's table exactly for all 10 existing worlds after
      recompile (or any discrepancy is investigated and documented, not silently accepted)
- [ ] `docs/simulation_quality/eval_matrix_results.md` world-scale reporting section includes the
      new metric alongside entity/region/resource-node counts
- [ ] New/extended unit test asserts correctness of the field for at least 2-3 worlds
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions (purely additive change)
- [ ] `make knowledge-index-update` run if `docs/` files were modified

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — this metric should be referenced as a scale-diversity
  criterion in the taxonomy doc's future-classification section
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — will use this metric to verify its many-factions/
  small-map stress world actually achieves a high distinct-faction count
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — established `test_corpus_diversity.py`, the likely home
  for this ticket's new/extended test

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 (scale diversity
  table, populated-faction column) and §4 open question 1
- `docs/simulation_quality/eval_matrix_results.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — precedent for corpus-wide recompile
  + verification discipline

## Related Code Areas
- `src/worldbuilding/` — `WorldCompiler.compile()` and wherever `world_compile_report.json` is
  written
- `data/worlds/*/world_compile_report.json` — all 10 worlds, regenerated
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `docs/simulation_quality/eval_matrix_results.md`

## Assumptions / Open Questions
- UQ-1: Is "populated" defined as "at least one entity currently assigned this faction ID at
  compile time" (investigation.md's apparent definition) or does it need to also account for
  factions that gain population only via runtime spawn events? Scope this ticket to the compile-time
  definition (matching investigation.md's own methodology) — runtime-population drift is a
  separate, more complex signal and out of scope here.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260704-SIMQ-CORPUS-SCALE-METRIC/plan.md`'s 8
steps, no deviations.

1. Added `"distinct_populated_factions": len({fid for e in entities.values() if (fid :=
   e.properties.get("faction_id"))})` to the `report = {...}` dict literal in
   `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`), placed after `quest_count`, before
   `warnings`. Purely additive, read-only aggregation over the already-built `entities` local — no
   change to `FactionState`, `factions`, or faction-assignment logic.
2. Fixed the one downstream consumer that hardcodes the report's exact key set —
   `tests/certification/test_world_compile_determinism.py::test_compile_report_contents` — adding
   `"distinct_populated_factions"` to `expected_keys` and `assert saved["distinct_populated_factions"]
   == 2` (verified: `create_certification_base_spec()` has exactly 2 populations, `"locals"` and
   `"intruders"`, and `context=None` in that test so no resolved-composition override fires).
3. Extended `tests/unit/worldassembly/test_corpus_diversity.py` with
   `EXPECTED_DISTINCT_POPULATED_FACTIONS` (all 10 worlds) and a new
   `test_distinct_populated_factions` test, parametrized in the same style as
   `test_entity_count_band` and reusing the existing `_load_compile_report` helper.
4. Recompiled all 10 worlds under `data/worlds/` via `python3 -m src.worldbuilding.cli compile
   <world_id> --seed <recorded_seed>` (each world's own already-recorded seed, matching plan.md's
   table). Verified via `git diff` that every world's `world_compile_report.json` changed only by
   the addition of `distinct_populated_factions` plus expected `compile_duration_ms` timing noise —
   `state_hash` is byte-identical to the pre-change value in all 10 cases, confirming no drift.
5. Added a new "## Corpus World-Scale Summary" section at the end of
   `docs/simulation_quality/eval_matrix_results.md` (after the prior final section, "Zero-Pillar
   World Confirmation") with one consolidated 10-world table (seed, entity/region/resource-node/
   building/quest/distinct-populated-faction counts), cross-checked field-by-field against the
   freshly recompiled JSON reports — all values match exactly.
6. `make evaluate` (the target already bakes in `--dry-run` via its Makefile recipe; running
   `make evaluate --dry-run` directly passes `--dry-run` to `make` itself rather than the script,
   which is a no-op pass-through — used the bare `make evaluate` invocation instead) reported
   "390 pillars checked — 0 regressions — 0 missing", confirming this is a purely additive change
   with zero SimQ pillar-grade impact.
7. `make knowledge-index-update` ran successfully after the `docs/` edit (3 files re-embedded, 1921
   from cache).
8. `graphify update .` ran successfully after the `src/`/`tests/` edits (24216 nodes, 51162 edges,
   1536 communities rebuilt).

No architecture-constrained files were touched: no edits to `FactionState`, faction-assignment
logic, or any file under `src/simulation_quality/scorers/`. No new worlds authored.

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -v` — 21 passed, 5
  deselected (the deselected are the `@pytest.mark.slow` `test_population_stability` cases, out of
  scope for this scoped run per plan.md). All 10 new `test_distinct_populated_factions[...]` cases
  passed.
- `pytest tests/certification/test_world_compile_determinism.py -v` — 3 passed, including the fixed
  `test_compile_report_contents`.
- `pytest tests/unit/lab/test_lab_result_store.py -v` — 6 passed (unaffected, as expected — this
  file writes its own synthetic fixture and never calls `WorldCompiler.compile()`).
- `make evaluate` — "390 pillars checked — 0 regressions — 0 missing", exit code 0.

## Files Changed
- `src/worldbuilding/compiler.py` — added `distinct_populated_factions` field to the compile report
  dict.
- `tests/certification/test_world_compile_determinism.py` — updated `expected_keys` and added the
  new field's value assertion.
- `tests/unit/worldassembly/test_corpus_diversity.py` — added
  `EXPECTED_DISTINCT_POPULATED_FACTIONS` and `test_distinct_populated_factions`.
- `docs/simulation_quality/eval_matrix_results.md` — added "Corpus World-Scale Summary" section.
- `data/worlds/wilderness_survival/world_compile_report.json` — recompiled (seed 101).
- `data/worlds/sandbox_world/world_compile_report.json` — recompiled (seed 42).
- `data/worlds/highland_traverse/world_compile_report.json` — recompiled (seed 91).
- `data/worlds/urban_political/world_compile_report.json` — recompiled (seed 202).
- `data/worlds/dungeon_crawl/world_compile_report.json` — recompiled (seed 303).
- `data/worlds/swamp_border_world/world_compile_report.json` — recompiled (seed 77).
- `data/worlds/simq_routing_test/world_compile_report.json` — recompiled (seed 42).
- `data/worlds/frontier_living_world/world_compile_report.json` — recompiled (seed 42).
- `data/worlds/generated_frontier_3_42/world_compile_report.json` — recompiled (seed 42).
- `data/worlds/frontier_extended/world_compile_report.json` — recompiled (seed 43).

## Completion Summary
Added `distinct_populated_factions` to `WorldCompiler.compile()`'s report dict — a read-only count
of unique `entity.properties["faction_id"]` values, computed from already-built entity state (not
the coarse 4-bucket `Faction` enum, which cannot distinguish e.g. `undead_remnants` from
`wild_beast_pack`). Recompiled all 10 worlds under `data/worlds/`; independently confirmed
byte-identical `state_hash` in all 10 (purely additive, no behavior change) with the new field
matching `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`'s §2 table
exactly (`wilderness_survival=2` ... `frontier_extended=9`, no discrepancy found).

Fixed the one downstream test that hardcoded the report's key set
(`test_world_compile_determinism.py::test_compile_report_contents`), extended
`test_corpus_diversity.py` with a new correctness test across all 10 worlds, and added a
consolidated "Corpus World-Scale Summary" table to `eval_matrix_results.md` (the doc previously
only had partial entity/region reporting for 5 of 10 worlds, not a full corpus table — this ticket
adds the first one). `make evaluate` confirmed zero SimQ pillar-grade regressions, independently
re-confirmed. No `FactionState`, faction-assignment logic, or SimQ pillar scoring touched.
