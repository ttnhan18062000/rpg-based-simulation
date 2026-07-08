---
ticket_id: TCK-20260704-SIMQ-CORPUS-SCALE-METRIC
phase: plan
date: 2026-07-06
---

# Plan: Track "distinct populated factions" as an explicit per-world scale metric

PHASE_TS: 2026-07-06T16:48:32Z

## Summary

Add a read-only, additive `distinct_populated_factions` field to `WorldCompiler.compile()`'s
report dict (`src/worldbuilding/compiler.py`), fix the one downstream test that hardcodes the
report's full key set, extend `test_corpus_diversity.py` with a correctness test across all 10
worlds, recompile all 10 worlds so their on-disk `world_compile_report.json` picks up the field,
add a new consolidated scale-summary table to `eval_matrix_results.md`, and verify zero regressions
via `make evaluate --dry-run`. No `FactionState`, faction-assignment logic, or SimQ pillar scoring
is touched — confirmed zero dependency by investigation.md §6.

## Step-by-step

1. Edit `src/worldbuilding/compiler.py` — add `distinct_populated_factions` to the `report = {...}`
   dict literal (currently lines 513-524), after `quest_count`, before `warnings`.
2. Fix `tests/certification/test_world_compile_determinism.py::test_compile_report_contents` —
   add `"distinct_populated_factions"` to `expected_keys` (currently lines 108-119) and add
   `assert saved["distinct_populated_factions"] == 2` (confirmed below) next to the other
   `saved[...]` assertions (after line 133).
3. Extend `tests/unit/worldassembly/test_corpus_diversity.py` — add
   `EXPECTED_DISTINCT_POPULATED_FACTIONS` module-level dict (all 10 worlds, values from
   investigation.md §3's verified table) and a new `test_distinct_populated_factions` test
   parametrized over it, mirroring `test_entity_count_band`'s shape and reusing
   `_load_compile_report`.
4. Recompile all 10 worlds under `data/worlds/` so their `world_compile_report.json` picks up the
   new field. All 10 are composition-schema worlds with `resolved/` already present (verified via
   `resolved/` directory listing) — no `resolve` re-run needed, only `compile --from-resolved`-style
   auto-detection (the composition branch in `handle_compile` triggers automatically off
   `schema_version`). Exact command per world, using each world's currently-recorded seed (from its
   existing `world_compile_report.json`, to keep `state_hash`/layout byte-identical):
   ```
   python -m src.worldbuilding.cli compile wilderness_survival    --seed 101
   python -m src.worldbuilding.cli compile sandbox_world          --seed 42
   python -m src.worldbuilding.cli compile highland_traverse      --seed 91
   python -m src.worldbuilding.cli compile urban_political        --seed 202
   python -m src.worldbuilding.cli compile dungeon_crawl          --seed 303
   python -m src.worldbuilding.cli compile swamp_border_world     --seed 77
   python -m src.worldbuilding.cli compile simq_routing_test      --seed 42
   python -m src.worldbuilding.cli compile frontier_living_world  --seed 42
   python -m src.worldbuilding.cli compile generated_frontier_3_42 --seed 42
   python -m src.worldbuilding.cli compile frontier_extended      --seed 43
   ```
   After each run, `git diff data/worlds/<world>/world_compile_report.json` must show only the new
   `distinct_populated_factions` key added (plus expected `compile_duration_ms` timing noise) —
   `state_hash` and every other field must be byte-identical to the pre-change value.
5. Add a new `## Corpus World-Scale Summary` section to
   `docs/simulation_quality/eval_matrix_results.md`, appended at the end of the file (after the
   existing final section, "Zero-Pillar World Confirmation", which ends at line 562) — a single
   table covering all 10 worlds, not a patch to the 5 existing "Newly-Anchored Worlds" headers (per
   investigation.md §7's recommendation, since those headers cover only half the corpus and have no
   room for a new column without reformatting each one).
6. Run `make evaluate --dry-run`; confirm 0 regressions.
7. Run `make knowledge-index-update` (docs/ file modified).
8. Run the scoped test selection from test_plan.md (not the full suite):
   ```
   pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -v
   pytest tests/certification/test_world_compile_determinism.py -v
   pytest tests/unit/lab/test_lab_result_store.py -v
   ```

## Step 1 — exact diff, `src/worldbuilding/compiler.py`

```diff
         report = {
             "world_id": spec.world_id,
             "seed": seed,
             "entity_count": len(entities),
             "region_count": len(regions),
             "resource_node_count": len(resource_nodes),
             "building_count": len(buildings),
             "quest_count": len(compiled_quests),
+            "distinct_populated_factions": len({
+                fid for e in entities.values()
+                if (fid := e.properties.get("faction_id"))
+            }),
             "warnings": warnings,
             "compile_duration_ms": compile_duration_ms,
             "state_hash": state_hash
         }
```

No other lines in `compile()` change. `entities` is the existing local `Dict[int, EntityState]`
already fully populated by this point in the method (line ~495 area, well before the report dict at
513-524) — no new state construction, no change to `AuthoritativeState(...)`, `factions`, or
`FactionState`.

## Step 2 — exact diff, `tests/certification/test_world_compile_determinism.py`

Confirmed independently (not just trusting investigation.md): `create_certification_base_spec()`
(lines 11-41) defines exactly two `entities` blocks —
`{"id": "villagers", ..., "faction": "locals", ...}` and
`{"id": "monsters", ..., "faction": "intruders", ...}` — and
`test_compile_report_contents` calls `WorldCompiler.compile(spec, seed=1337,
output_report_path=report_path)` with no `context` argument, so `context` defaults to `None`
(`compile()` signature, `context: Optional[Any] = None`, line 121). With `context=None` the
override branch at compiler.py:322-323 (`if context is not None and pop_key in context.entities`)
never executes, so `ent_properties["faction_id"]` keeps the raw `pop_spec.faction` string
unmodified for both populations — `"locals"` and `"intruders"`, two distinct values. Confirmed:
expected value is `2`.

```diff
         # Verify dict keys
         expected_keys = {
             "world_id",
             "seed",
             "entity_count",
             "region_count",
             "resource_node_count",
             "building_count",
             "quest_count",
+            "distinct_populated_factions",
             "warnings",
             "compile_duration_ms",
             "state_hash"
         }
         assert set(report.keys()) == expected_keys
         
         # Verify JSON saved matches
         assert os.path.exists(report_path)
         with open(report_path) as f:
             saved = json.load(f)
             
         assert saved["world_id"] == "cert_valley"
         assert saved["seed"] == 1337
         assert saved["entity_count"] == 35
         assert saved["region_count"] == 2
         assert saved["resource_node_count"] == 2
         assert saved["building_count"] == 1
         assert saved["quest_count"] == 0
+        assert saved["distinct_populated_factions"] == 2
         assert saved["state_hash"] == report["state_hash"]
```

## Step 3 — exact addition, `tests/unit/worldassembly/test_corpus_diversity.py`

Insert a new module-level constant near `ANCHORED_WORLD_BANDS` (after `POPULATION_STABILITY_WORLDS`
at line 47, before the `NEWLY_ANCHORED_MODULES` block, to keep it grouped with the other
world-keyed expectation dicts) and a new test function grouped with `test_entity_count_band` (after
line 122, before the "Population stability" section header at line 125), matching the file's
existing section-comment-banner convention:

```python
# All 10 worlds' distinct-populated-faction counts, verified against
# staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md §2 and re-confirmed by
# TCK-20260704-SIMQ-CORPUS-SCALE-METRIC's own recompile cross-check (investigation.md §3).
EXPECTED_DISTINCT_POPULATED_FACTIONS: dict[str, int] = {
    "wilderness_survival": 2,
    "sandbox_world": 3,
    "highland_traverse": 3,
    "urban_political": 4,
    "dungeon_crawl": 4,
    "swamp_border_world": 4,
    "simq_routing_test": 5,
    "frontier_living_world": 6,
    "generated_frontier_3_42": 7,
    "frontier_extended": 9,
}
```

```python
# ---------------------------------------------------------------------------
# 1b. Distinct populated factions (TCK-20260704-SIMQ-CORPUS-SCALE-METRIC)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "world_id,expected", list(EXPECTED_DISTINCT_POPULATED_FACTIONS.items())
)
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

This covers all 10 worlds (ticket AC only requires 2-3; investigation.md §3 and the test_plan both
recommend the full set since all 10 values are already independently verified and it closes AC2's
"or document and resolve any discrepancy" loop most durably).

## Step 4 — recompile verification data (for the completion summary / doc table)

Current on-disk values (read directly from each world's `world_compile_report.json` before this
change, confirmed 2026-07-06), which the new `docs/` table (Step 5) will present alongside the new
`distinct_populated_factions` column:

| World | Seed | entity_count | region_count | resource_node_count | building_count | quest_count | distinct_populated_factions |
|---|---|---|---|---|---|---|---|
| wilderness_survival | 101 | 11 | 4 | 4 | 1 | 7 | 2 |
| sandbox_world | 42 | 18 | 3 | 5 | 5 | 6 | 3 |
| highland_traverse | 91 | 18 | 5 | 3 | 5 | 6 | 3 |
| urban_political | 202 | 30 | 3 | 3 | 7 | 9 | 4 |
| dungeon_crawl | 303 | 32 | 4 | 3 | 1 | 9 | 4 |
| swamp_border_world | 77 | 26 | 4 | 7 | 5 | 6 | 4 |
| simq_routing_test | 42 | 30 | 3 | 5 | 6 | 7 | 5 |
| frontier_living_world | 42 | 46 | 7 | 9 | 6 | 16 | 6 |
| generated_frontier_3_42 | 42 | 44 | 6 | 9 | 6 | 16 | 7 |
| frontier_extended | 43 | 56 | 10 | 13 | 6 | 22 | 9 |

`entity_count`/`region_count`/`resource_node_count`/`building_count`/`quest_count` are the current
on-disk values (pre-change) and must be unchanged after recompile; `distinct_populated_factions` is
the new field's expected value per investigation.md §3, which this plan's Step 3 test enforces.

## Step 5 — exact doc insertion, `docs/simulation_quality/eval_matrix_results.md`

Append after the current end of file (line 562, end of "Zero-Pillar World Confirmation" section —
confirmed via `wc -l` and `grep -n "^## "`, no section follows it):

```markdown

---

## Corpus World-Scale Summary (TCK-20260704-SIMQ-CORPUS-SCALE-METRIC)

Consolidated scale reporting for all 10 worlds under `data/worlds/`, pulled directly from each
world's `world_compile_report.json`. Earlier per-world reporting in "Newly-Anchored Worlds" above
covered entity/region counts for only 5 of the 10 worlds and did not include resource-node,
building, quest, or populated-faction counts anywhere in this doc — this table closes that gap in
one place rather than patching five scattered headers. `distinct_populated_factions` counts unique
`entity.properties["faction_id"]` values actually assigned to a compiled entity (not the static
16-entry `AuthoritativeState.factions` catalog, which is constant across all worlds and therefore
not a meaningful per-world signal on its own — see
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2).

| World | Seed | Entities | Regions | Resource Nodes | Buildings | Quests | Distinct Populated Factions |
|---|---|---|---|---|---|---|---|
| wilderness_survival | 101 | 11 | 4 | 4 | 1 | 7 | 2 |
| sandbox_world | 42 | 18 | 3 | 5 | 5 | 6 | 3 |
| highland_traverse | 91 | 18 | 5 | 3 | 5 | 6 | 3 |
| urban_political | 202 | 30 | 3 | 3 | 7 | 9 | 4 |
| dungeon_crawl | 303 | 32 | 4 | 3 | 1 | 9 | 4 |
| swamp_border_world | 77 | 26 | 4 | 7 | 5 | 6 | 4 |
| simq_routing_test | 42 | 30 | 3 | 5 | 6 | 7 | 5 |
| frontier_living_world | 42 | 46 | 7 | 9 | 6 | 16 | 6 |
| generated_frontier_3_42 | 42 | 44 | 6 | 9 | 6 | 16 | 7 |
| frontier_extended | 43 | 56 | 10 | 13 | 6 | 22 | 9 |

`generated_frontier_3_42` has zero entries in `tests/simulation_quality/fixtures/grade_anchors.json`
and is not part of the pillar-grade calibration corpus tracked elsewhere in this doc — it is
included here only for scale-metric completeness (it is one of the 10 worlds under `data/worlds/`),
not as a calibration claim.
```

Values are taken verbatim from Step 4's table (pre-change fields) plus the new field's verified
values — no new computation needed at doc-authoring time, only the recompiled on-disk JSON values
carried through.

## Regression / scope guards (carried from investigation + test_plan, restated for the implementer)

- Do **not** touch `FactionState`, `get_faction_enum`, the `ent_properties["faction_id"]`
  assignment/override branch, or any file under `src/simulation_quality/scorers/` (confirmed zero
  dependency, investigation.md §6).
- Do **not** author any new worlds or `world.yaml` files — this ticket only recompiles existing
  worlds to regenerate their reports.
- `state_hash` in every recompiled `world_compile_report.json` must be byte-identical to its
  pre-change value — if it changes, stop and investigate before proceeding (would indicate the
  recompile used a different seed/content than currently committed, not an effect of this ticket's
  own change).
- `tests/unit/lab/test_lab_result_store.py` needs no edits (writes its own synthetic fixture,
  doesn't call `WorldCompiler.compile()`) — run it only as a confirmation, not because a change is
  expected.

## Open Questions

None requiring a human decision. The one documentation-shape ambiguity investigation.md §7 flagged
(whether to patch the 5 existing per-world headers or add one consolidated table) is resolved here
in favor of a single new consolidated section covering all 10 worlds, per that section's own
recommendation and because the 5 existing headers have no natural per-pillar-table home for a
scale-only column (they are pillar-grade tables, not scale tables).

## Deviations

- Step 6: the plan's literal command `make evaluate --dry-run` passes `--dry-run` to `make` itself
  (make's own dry-run flag, which just prints the recipe line without executing it), not to the
  underlying `tools/evaluate_simq.py` script. The `evaluate` Makefile target already bakes
  `--dry-run` into its recipe (`$(PYTHON) tools/evaluate_simq.py --dry-run`). Ran the bare `make
  evaluate` instead, which produced the intended dry-run diff-against-anchors behavior: "390
  pillars checked — 0 regressions — 0 missing", exit code 0. No behavior change from what the plan
  intended, only a command-invocation correction.


---

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This doc's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
and/or its later rename, `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`, point
to a pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact drawn
from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` and/or `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.
