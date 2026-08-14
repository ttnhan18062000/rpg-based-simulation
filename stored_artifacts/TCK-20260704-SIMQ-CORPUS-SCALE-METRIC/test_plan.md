---
ticket_id: TCK-20260704-SIMQ-CORPUS-SCALE-METRIC
phase: test_plan
date: 2026-07-06
---

# Test Plan: Track "distinct populated factions" as an explicit per-world scale metric

## Regression Surface

- `tests/certification/test_world_compile_determinism.py::test_compile_report_contents` — asserts
  `set(report.keys()) == expected_keys` (lines 108-120), a hardcoded exhaustive key set. **Will
  fail as soon as `distinct_populated_factions` is added** unless `expected_keys` is updated in the
  same change. This is a required edit, not optional cleanup.
- `data/worlds/*/world_compile_report.json` (all 10) — additive field only; every existing key
  (`world_id`, `seed`, `entity_count`, `region_count`, `resource_node_count`, `building_count`,
  `quest_count`, `warnings`, `compile_duration_ms`, `state_hash`) must keep its current value after
  recompile (confirmed reproducible in this investigation — recompiling with each world's recorded
  seed reproduced the currently-committed `entity_count` for every world exactly, so no drift is
  expected from this change alone).
- `src/lab/store.py::LabResultStore.load_compile_report` / `src/lab/orchestrator.py` — passthrough
  JSON consumers, no key filtering; verified no exact-key-set assertions exist there. No test
  changes needed for these two files themselves.
- `tests/unit/lab/test_lab_result_store.py::test_load_validation_and_compile_reports` — writes its
  own synthetic fixture JSON rather than calling `WorldCompiler.compile()`; unaffected, no change
  needed.
- `src/simulation_quality/scorers/faction.py` (FACTION pillar scorer) — confirmed no dependency on
  `world_compile_report.json` or this new field; must remain untouched (Out of Scope constraint).
  No test coverage change needed there, but a quick post-change `grep` confirming this import graph
  is still true is worth one line in the completion summary.
- `make evaluate --dry-run` — ticket's own AC: must exit 0 with 0 grade regressions (purely
  additive reporting field, no pillar-scoring path touches it).

## New / Extended Tests Required

1. **Extend `tests/unit/worldassembly/test_corpus_diversity.py`** (do not create a new file — this
   module's docstring and `_load_compile_report` helper are a direct, zero-friction fit):
   - Add an `EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int]` module-level constant, values
     taken from this investigation's verified table (all 10 confirmed correct):
     `wilderness_survival: 2, sandbox_world: 3, highland_traverse: 3, urban_political: 4,
     dungeon_crawl: 4, swamp_border_world: 4, simq_routing_test: 5, frontier_living_world: 6,
     generated_frontier_3_42: 7, frontier_extended: 9`. Ticket AC only requires 2-3 worlds be
     asserted; including all 10 is stronger and costs nothing extra since the values are already
     verified here — recommend the full set to close the loop the ticket itself opened (AC2: "or
     document and resolve any discrepancy found" — asserting all 10 is the most durable way to
     "resolve," since it makes any future drift fail loudly rather than silently).
   - New test function, e.g. `test_distinct_populated_factions`, parametrized over
     `EXPECTED_DISTINCT_POPULATED_FACTIONS.items()`, using the existing `_load_compile_report`
     helper (which already `pytest.skip`s cleanly if a report is missing — no new skip-handling
     logic needed):
     ```python
     @pytest.mark.parametrize("world_id,expected", list(EXPECTED_DISTINCT_POPULATED_FACTIONS.items()))
     def test_distinct_populated_factions(world_id: str, expected: int) -> None:
         report = _load_compile_report(world_id)
         assert "distinct_populated_factions" in report, (
             f"{world_id}: world_compile_report.json missing 'distinct_populated_factions' — "
             "recompile with the updated WorldCompiler."
         )
         assert report["distinct_populated_factions"] == expected, (
             f"{world_id}: distinct_populated_factions={report['distinct_populated_factions']} "
             f"!= expected {expected} (staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/"
             "investigation.md §2)"
         )
     ```
   - This mirrors `test_entity_count_band`'s exact shape (same file, lines 111-122) — same
     parametrize-over-dict pattern, same helper, same module, no new fixtures.

2. **Update `tests/certification/test_world_compile_determinism.py::test_compile_report_contents`**
   (required, not optional — see Regression Surface above):
   - Add `"distinct_populated_factions"` to the `expected_keys` set (line ~108-119).
   - Add one value assertion for the new field against the fixture world (`create_certification_base_spec()`
     → `cert_valley`, seed 1337): `assert saved["distinct_populated_factions"] == 2`. Verified by
     inspection — the fixture (lines 11-41) defines exactly 2 populations
     (`villagers`→`faction: "locals"`, `monsters`→`faction: "intruders"`), `compile()` is called
     with `context=None` in this test, so `ent_properties["faction_id"]` takes the raw
     `pop_spec.faction` string unmodified for both (no override branch executes) — 2 distinct
     values.

3. **No change needed to `tests/unit/lab/test_lab_result_store.py`** — confirmed it does not call
   `WorldCompiler.compile()` (writes its own synthetic report fixture), so the new field is
   invisible to it either way.

## Manual / Integration Verification (per ticket Scope items 5-6)

- Recompile all 10 worlds under `data/worlds/` (composition-schema worlds via
  `python -m src.worldbuilding.cli resolve <world>` then `compile`; raw-schema worlds via
  `compile` directly — mirrors this investigation's own verification script logic) so each
  `world_compile_report.json` picks up `distinct_populated_factions` on disk.
- Confirm no other on-disk field changed value as a side effect (`git diff` on all 10
  `world_compile_report.json` files should show only the new key added, or `compile_duration_ms`
  drift, which is expected/ignorable non-deterministic timing noise — everything else must be
  byte-identical, especially `state_hash`, which must NOT change since this is a read-only reporting
  addition with zero effect on `AuthoritativeState` construction).
- Run `make evaluate --dry-run`; confirm 0 regressions against `tests/simulation_quality/fixtures/grade_anchors.json`.
- If `docs/simulation_quality/eval_matrix_results.md` is edited, run `make knowledge-index-update`
  per the Definition of Done.

## Test Selection for This Ticket's Verification Pass

Do not run the full suite. Scope to:
```
pytest tests/unit/worldassembly/test_corpus_diversity.py -v
pytest tests/certification/test_world_compile_determinism.py -v
pytest tests/unit/lab/test_lab_result_store.py -v   # confirm truly unaffected
```
`test_population_stability` in `test_corpus_diversity.py` is `@pytest.mark.slow` — exclude via
`-m "not slow"` unless specifically validating population stability, which this ticket does not
change.
