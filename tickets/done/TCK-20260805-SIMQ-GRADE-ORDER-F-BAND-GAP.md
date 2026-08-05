---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP
phase: done
date: 2026-08-05
tags: [simulation-quality, calibration]
---

# TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP

## Title
Add the F grade band to evaluate_simq.py's and test_grade_regression.py's GRADE_ORDER

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`src/simulation_quality/quality_report.py::_assign_grade()` defines 6 real grade bands
(S > +2.0, A +0.5 to +2.0, B 0.0 to +0.5, C -0.5 to 0.0, D -1.0 to -0.5, F < -1.0 implicit). Both
`tools/evaluate_simq.py:29` and `tests/simulation_quality/test_grade_regression.py:44` independently
define `GRADE_ORDER = ["D", "C", "B", "A", "S"]` — a 5-value ordinal list that excludes F entirely.
Both `_within_band()` functions (`evaluate_simq.py:37-39`, `test_grade_regression.py:224-226`) do
`if actual not in GRADE_ORDER or anchor not in GRADE_ORDER: return False` — so if a real run ever
produces an F grade, these comparisons report it as an unconditional tolerance-band mismatch rather
than a graded ordinal distance, breaking the regression gate's actual purpose for that pillar.

Confirmed dormant, not currently harmful: 0 of 75 fresh reports in this session's 2026-08-05
full-corpus re-run produced F on any pillar, and 0 committed anchors in `grade_anchors.json` are F.
Filed as a hotfix because it's small, precisely diagnosed already, and closes a real latent gap
before it silently breaks a future regression check.

## Scope
- Update `GRADE_ORDER` in both `tools/evaluate_simq.py` and
  `tests/simulation_quality/test_grade_regression.py` to include `"F"` at the correct ordinal
  position (below `"D"`).
- Verify `_within_band()`'s tolerance-distance math still behaves correctly with the added band
  (e.g. `D` vs `F` should now be distance 1, not an unconditional mismatch).
- Add or update a regression test exercising an F-grade comparison explicitly (currently no test
  covers this band at all, since it's never occurred in the corpus).

## Out of Scope
- Any change to `_assign_grade()`'s actual thresholds — those are correct and unaffected.
- Investigating *why* F has never occurred in the corpus, or whether it should — out of scope,
  this ticket only fixes the tooling's blind spot for the band that already exists in the scoring
  model.

## Acceptance Criteria
1. `GRADE_ORDER` in both files includes `"F"` in the correct ascending-quality position.
2. A new or updated test confirms `_within_band("F", "D", tolerance=1)` returns a sensible result
   (not an unconditional mismatch) and that an F-vs-S comparison correctly reports maximum distance.
3. Existing `test_grade_regression.py` suite still passes with no anchor changes required (this is
   a pure tooling fix, not a scoring or anchor change).

## Related Tickets
- `TCK-20260713-SIMQ-RAWSCORE-PERSIST` — added raw-score persistence alongside letter grades;
  related tooling-precision work in the same file, does not touch `GRADE_ORDER` itself.
- `TCK-20260630-SIMQ-ANCHORS` — established the current `GRADE_ORDER`/`_within_band()` design this
  ticket is patching.

## Related Docs
- `docs/simulation_quality/extension_points.md` §5 (Tuning config) — documents this exact gap.
- `docs/simulation_quality/quality_scoring_contract.md` — grade band definitions.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tools/evaluate_simq.py`
- `tests/simulation_quality/test_grade_regression.py`
- `src/simulation_quality/quality_report.py` (`_assign_grade()` — read-only reference, not modified)

## Assumptions / Open Questions
None — root cause fully diagnosed already, no further investigation needed before implementing.

## Implementation Notes
Added `"F"` at the correct ordinal position (lowest) to `GRADE_ORDER` in both
`tools/evaluate_simq.py` and `tests/simulation_quality/test_grade_regression.py`, plus their
docstrings. Found and fixed a third, previously-unnoticed copy: `grade_anchors.json` itself carries
a `"_grade_order"` metadata key (purely documentation, never read as runtime logic — confirmed via
grep of all 4 references) that also needed the same fix for consistency. Added a new explicit test,
`test_grade_order_includes_f_band`, verifying F is ordinal position 0, `_within_band("F", "D")` is
True (adjacent bands), and `_within_band("F", "S")` is False (max distance).

## Test Summary
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`: 65 passed (64 +
1 new) / 1 failed (same pre-existing, unrelated `urban_political_seed42_200t` NARRATIVE/SOCIAL
variance documented in this session's other tickets). Manually verified `tools/evaluate_simq.py`'s
copy imports cleanly and behaves identically (`_within_band("F","D")` True, `_within_band("F","S")`
False).

## Files Changed
- `tools/evaluate_simq.py` — `GRADE_ORDER` includes F
- `tests/simulation_quality/test_grade_regression.py` — `GRADE_ORDER` includes F, docstrings
  updated, new `test_grade_order_includes_f_band` test
- `tests/simulation_quality/fixtures/grade_anchors.json` — `_grade_order` metadata key includes F

## Completion Summary
Fixed the F grade band gap: `GRADE_ORDER` in `evaluate_simq.py` and `test_grade_regression.py`
previously excluded `"F"` despite `quality_report.py::_assign_grade()` being able to produce it,
meaning any future F-graded pillar would have been treated as an unconditional band mismatch
rather than a graded ordinal distance. Also found and fixed a third copy in
`grade_anchors.json`'s own metadata. Added regression test coverage for the previously-untested F
band. All 3 acceptance criteria met.
