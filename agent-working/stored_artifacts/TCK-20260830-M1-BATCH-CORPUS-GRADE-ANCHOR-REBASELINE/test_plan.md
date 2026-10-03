---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
artifact_type: test_plan
tags: [simulation-quality, grade-thresholds, calibration]
---

# Test Plan — TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE

## Regression Surface

- `tests/simulation_quality/test_grade_regression.py` — the entire fast-tier suite
  (`-m "not slow"`, 71 collected tests): 61 `FAST_ANCHOR_KEYS` parametrized cases (the ones this
  ticket rewrites anchors for) + 2 selfmodel-probe tests (out of scope, must remain untouched by
  this ticket's anchor writes and their pass/fail status is not this ticket's concern) + 8
  structural/meta tests (`test_grade_anchor_file_exists_and_valid`,
  `test_grade_anchors_entry_count_unchanged`, `test_grade_order_includes_f_band`,
  `test_within_band_default_tolerance_unchanged`, `test_score_tolerance_catches_within_band_regression`,
  `test_score_tolerance_override_table_scoped_to_named_pillars`,
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`,
  `test_information_intent_execution_fires_through_kernel_tick_once`) — these must stay passing;
  in particular `test_grade_anchors_entry_count_unchanged` asserts the anchor file's total entry
  count doesn't change, which this ticket's edit (grade/score value edits only, no new/removed
  run_key or pillar entries) must respect.
- `tools/simq_ceiling.py` and `tools/evaluate_simq.py` are read-only dependencies of this ticket's
  own analysis; not modified, but their behavior (e.g. `lookup_ceiling`) must not regress since the
  investigation's classification depends on it staying accurate.

## New Tests Required

None — this ticket is a test-fixture data update (`grade_anchors.json`'s committed values), not a
behavior/logic change. No new test coverage is warranted; the existing `test_grade_regression.py`
suite is itself the regression guard for the new anchor values going forward.

## Scoped Pytest Commands

Primary gate (must pass clean except the one disclosed `highland_traverse_seed42_200t` failure —
see investigation.md):
```
python3 -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

Isolate just the 61 `FAST_ANCHOR_KEYS` band/score test to verify the anchor rewrite directly:
```
python3 -m pytest tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band -m "not slow" -q
```

Confirm the 2 out-of-scope selfmodel-probe tests were never touched (their own separate test
functions, run in isolation, result should be unchanged from before this ticket — whatever their
current pass/fail status is, covered by `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`):
```
python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "selfmodel" -m "not slow" -q
```

Confirm the anchor-file-shape structural guards still pass (entry count unchanged, override table
still scoped correctly — these would only break if this ticket accidentally added/removed a
run_key or pillar entry instead of only editing values):
```
python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "entry_count or override_table or overrides_do_not_affect" -m "not slow" -q
```

## Anti-Drift Test Guards

- Before writing `grade_anchors.json`, diff the new file against the pre-edit version and assert
  the changed run_key set is a subset of exactly the 210 `(run_key, pillar)` combos this ticket's
  investigation.md classifies as "known-*" or "M1-batch drift" (i.e. everything in the full
  classification table except the one disclosed `highland_traverse_seed42_200t`/SOCIAL entry, and
  except any entry belonging to a run_key not in `FAST_ANCHOR_KEYS`, especially the 2 selfmodel-probe
  keys, which must show zero diff).
- After writing, re-run the full `-m "not slow"` suite and confirm the only remaining failure is
  `test_grade_within_anchor_band[highland_traverse_seed42_200t]` (or a superset only if genuinely
  new evidence emerges — never fewer classified failures silently dropped without explanation, and
  never additional failures silently ignored).
- Do not re-run `tools/evaluate_simq.py` between investigation and anchor-writing (see
  investigation.md's Anti-Drift Hazards) — write anchors from the exact same
  `data/calibration/` snapshot the investigation's evidence table was built from, so the numbers
  committed match the numbers documented 1:1.
