---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION
tags: [simulation-quality, calibration, testing, bug]
---

# Test Plan — TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION

## Commands and results

Pre-fix (old test failing, captured during investigation): idle-only capture already diverged
(`event_count=355` vs anchor `2`) in 2 of 4 isolated runs and 5 of 5 in a clean batch — see
investigation.md.

Post-fix:
```
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_500t_cognition_grade_stability -m slow --resource-budget large -q
```
`1 passed in 37.59s`.

Regression checks:
```
pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -q
```
`1 passed in 0.05s` — confirms this ticket's explicit `band_tolerance=2` call-site override did
not touch `_within_band`'s own default parameter.

```
grep -c "bit_identical_under_load" tests/unit/worldassembly/test_corpus_diversity.py
```
`0` — confirms no stale cross-references to the removed test name remain (11 sibling docstrings
were updated).

```
pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -q
```
`58 passed, 32 deselected in 1.04s` — the file's own fast-lane tests (unaffected by this ticket's
`-m slow`-only changes) still pass, confirming no import-time or fixture-level breakage from the
edit.

## Regression check
No `src/` file changed. `docs/simulation_quality/eval_matrix_results.md`'s edit is append-only
(verified by diff review — the original `## COGNITION Loop-Detection Nondeterminism Verification`
section text is byte-identical before and after).

## Final status
The converted guard passes reliably and reflects the real, currently-recurring bimodal behavior
honestly, without touching any shared default tolerance or source code.
