---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-RAWSCORE-PERSIST
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260713-SIMQ-RAWSCORE-PERSIST

## Regression Surface

All of `tests/simulation_quality/` reads or is adjacent to `grade_anchors.json`'s schema; the
scoped domain for this ticket is that whole directory plus `tools/evaluate_simq.py`'s own test
file. Must keep passing (fast tier, default `pytest` run):

**Unit — grade anchor / harness core:**
- `tests/simulation_quality/test_grade_regression.py` — all fast-tier tests (`test_grade_
  within_anchor_band` × 53 `FAST_ANCHOR_KEYS`, `test_urban_political_selfmodel_cognition_isolated_
  grade_anchor`, `test_grade_anchor_file_exists_and_valid`). This file is *itself* being modified by
  this ticket — regression here means "post-migration, on the new schema, these still pass," not
  "byte-identical to pre-migration."
- `tests/simulation_quality/test_evaluate_harness.py` — `TestWithinBand`, `TestCompare`,
  `TestResolveWorldName`, `TestParseRunKey`-equivalent classes. These operate on bare grade strings
  passed as plain function arguments (not read from the JSON file) and must NOT need to change.
- `tests/unit/tools/test_simq_audit_gaps.py` — `load_anchor_keys`/`find_uncovered_anchor_keys` only
  touch top-level keys; confirm still green (schema-agnostic, but re-run per Testing Rule since the
  fixture file itself changes).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_module_family_anchored` (and the other
  3 tests in that file) — reads `_anchored_world_ids()`, top-level keys only; confirm still green.

**Unit — scorer/report formula (must NOT change, since this ticket persists an existing field, it
does not alter how it's computed):**
- `tests/simulation_quality/test_report.py` — `normalized_score`/formula-stability tests.
- `tests/simulation_quality/test_weights.py`, `test_timegate_penalties.py` — untouched by this
  ticket's scope; run as a cheap confirm-nothing-else-moved guard.

**Integration:**
- `tests/simulation_quality/test_kernel_simq_integration.py`, `test_quality_hub_integration.py`,
  `test_scenario_coverage.py`, `test_calibrate_world_loading.py`, `test_traceability_path.py` —
  none of these read `grade_anchors.json`'s per-pillar shape; included as the standard SimQ-domain
  regression surface per the Testing Rule ("scope to the domain under modification").
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — reads top-level anchor keys
  only (precedent citation, not per-pillar values); confirm still green.

**Slow tier (`pytest -m slow`, run separately, not part of the default gate):**
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run` × 19
  `SLOW_ANCHOR_KEYS`.

## New Tests Required

Per the ticket's Acceptance Criteria:

1. **Schema structural test — both fields present and correctly typed per pillar per anchor entry.**
   - Category: unit (extend existing `test_grade_anchor_file_exists_and_valid`, do not add a
     parallel standalone test — this is the existing "file is well-formed" test's natural home).
   - Verifies: every non-metadata entry has exactly 10 pillars; each pillar value is now a dict with
     exactly the keys `{"grade", "score"}` (or documented equivalent); `grade` is a member of
     `GRADE_ORDER`; `score` is a `float`/`int` (not a string, not `None`).
   - Location: `tests/simulation_quality/test_grade_regression.py`
     (`test_grade_anchor_file_exists_and_valid`, currently line ~301).

2. **Grade-band assertion continues to work on the new schema (regression of the existing
   mechanism, not new behavior).**
   - Category: unit (modify existing parametrized tests, not a new test).
   - Verifies: `test_grade_within_anchor_band` / `test_grade_within_anchor_band_long_run` /
     `test_urban_political_selfmodel_cognition_isolated_grade_anchor` still correctly extract
     `anchors[pillar]["grade"]` (not the whole dict) and still call `_within_band` on grade strings.
   - Location: `tests/simulation_quality/test_grade_regression.py` (same three functions).

3. **New score-tolerance assertion, independent of the letter-grade check.**
   - Category: unit.
   - Verifies: for every pillar in every anchor entry with a live calibration report, the report's
     `normalized_score` stays within the (empirically-determined — see Investigation §Risks #1 for
     the open numeric-design question) tolerance of `anchors[pillar]["score"]`, reported as a
     separate failure list from the letter-band failures (so a CI reader can distinguish "letter
     moved" from "same letter, magnitude drifted").
   - Location: `tests/simulation_quality/test_grade_regression.py`, folded into
     `test_grade_within_anchor_band`/`test_grade_within_anchor_band_long_run` as an additional
     assertion block (reuses the existing per-run_key parametrization rather than adding a second,
     separately-parametrized test function — matches the ticket's "one additional tolerance
     assertion" framing).

4. **Before/after proof — the AC's mandated demonstration that the new check catches what the old
   one misses.**
   - Category: unit, dedicated new test function (this one genuinely needs its own test, since it
     is a demonstration of the fix, not a per-scenario regression check).
   - Verifies: construct a synthetic report dict (in-memory, not a new committed calibration
     scenario) with an anchor at grade S with some `score` value `X > 4.0`, and a "live" value of
     `X / 2` (still `> 2.0`, so still grade S). Assert (a) the OLD letter-only comparison
     (`_within_band(actual_grade, anchor_grade)`) would report PASS (both "S"), and (b) the NEW
     score-tolerance check reports a failure for this synthetic case. Both assertions belong in the
     same test so the "before/after" contrast is explicit and can't silently rot into only checking
     the new behavior.
   - Location: new test function in `tests/simulation_quality/test_grade_regression.py`, e.g.
     `test_score_tolerance_catches_within_band_regression()`.

5. **`tools/evaluate_simq.py` schema-compatibility fix.**
   - Category: unit.
   - Verifies: `main()`'s anchor-read call site (line ~200) correctly extracts `.grade` per pillar
     from the new object schema before calling `_compare()`, and does not crash/misbehave on a
     fixture using the new schema. `_compare()`/`_within_band()` themselves are unchanged (per
     Investigation — they already operate on bare grade strings passed as arguments).
   - Location: `tests/simulation_quality/test_evaluate_harness.py` — add a test that loads a small
     in-memory or `tmp_path`-fixtured anchor dict in the new object schema and confirms `main()`'s
     read path (or a testable helper extracted from it, if `main()` itself isn't unit-testable as-is)
     produces the same `_compare()` inputs it would have produced under the old bare-string schema.

6. **(If the planner resolves Investigation Risk #3 to include it) `evaluate_simq.py` score-
   tolerance parity check.** Not committed to here since it's an open design question — if adopted,
   mirrors New Test #3's shape against `_compare()`'s output rows instead of
   `test_grade_regression.py`'s failure list.

## Scoped Pytest Commands

Fast tier (default gate, run after every implementation step):
```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v
pytest tests/simulation_quality/test_evaluate_harness.py -v
pytest tests/simulation_quality/ -m "not slow" -v
pytest tests/unit/tools/test_simq_audit_gaps.py tests/unit/worldassembly/test_corpus_diversity.py -v
```

Slow tier (run once before Finalize, not on every edit):
```
pytest tests/simulation_quality/test_grade_regression.py -m slow -v
```

Never `pytest tests/` — scope stays to the `simulation_quality` domain plus the two schema-agnostic
consumer test files named above, per the Testing Rule.

## Anti-Drift Test Guards

- **Metadata-key exclusion regression guard.** `test_grade_anchor_file_exists_and_valid` already
  iterates only `MINIMUM_FAST_ANCHORS` (not raw top-level keys), so it's naturally immune to
  `_note`/`_instructions`/`_grade_order` — but the new structural assertion (New Test #1) must be
  added inside that same guarded iteration, not a fresh raw `for key in grade_anchors` loop that
  could reintroduce a metadata-key false-positive.
- **`raw_score` vs. `normalized_score` field-confusion guard.** Add an explicit assertion (can live
  inside New Test #1 or as its own tiny check) that the persisted `score` value for at least one
  known S-graded anchor entry is `> 2.0` and *not* equal to that same report's `raw_score` (which is
  typically an order of magnitude different) — catches an implementer accidentally wiring the wrong
  field during the migration script.
- **COGNITION-under-load exclusion guard (ties to Investigation Risk #2).** If the chosen tolerance
  design ends up pillar-specific or has any special-casing for COGNITION, add a test asserting the
  special-case is scoped to COGNITION only and does not silently loosen the tolerance for any other
  pillar — this guards against the known, unrelated `TCK-20260713-SIMQ-COGNITION-LOOPDET-
  NONDETERMINISM` bug being used as an excuse to over-widen the tolerance globally.
- **`_within_band`'s `tolerance=1` default must not move.** A parametrized test
  (`test_letter_band_tolerance_unchanged` or equivalent, or simply asserting
  `_within_band.__defaults__ == (1,)` / calling it directly with boundary cases) guards against the
  new score check's implementation accidentally also loosening the pre-existing letter-band width
  while it's being edited in the same file.
- **Anchor-count guard.** `test_grade_anchor_file_exists_and_valid`'s `MINIMUM_FAST_ANCHORS` check
  already guards against losing scenario coverage; after migration, additionally confirm the total
  scenario-entry count is unchanged (75) unless a new scenario is deliberately added — a schema
  migration script that silently drops or duplicates an entry should fail this.
- **`evaluate_simq.py` non-crash guard on the live (non-dry-run) path.** Since `main()`'s call site
  is the one real break identified, a dry-run smoke test against the post-migration fixture (using
  an existing `data/calibration/` report) should be part of the new test, not just a synthetic
  in-memory shape check — catches a subtle bug where the extraction works for the unit test's
  synthetic dict but not for the real committed fixture's exact key ordering/typing.
