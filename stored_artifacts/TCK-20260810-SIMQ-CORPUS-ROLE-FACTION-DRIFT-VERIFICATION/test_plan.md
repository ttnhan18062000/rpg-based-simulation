---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION
phase: test
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION

## Scope

`tests/simulation_quality/test_grade_regression.py -m "not slow"` — the fast-tier (≤500t) SimQ
regression suite. This is the authoritative gate for `grade_anchors.json` correctness; no other
test module is affected since no source code changed.

## Normal flow

- Every recalibrated run_key/pillar pair passes both the ±1 grade-band check (`_within_band`) and
  the numeric score-tolerance check (`_format_score_failures`).

## Edge cases

- Two guard-only run_keys (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`) reference scenarios outside the
  main `FAST_ANCHOR_KEYS` parametrization — their calibration reports were missing on disk
  (gitignored, regenerate-on-demand) and needed fresh generation before the guard assertions could
  even evaluate; both then surfaced real, same-cause COMBAT/SOCIAL drift, fixed alongside the main
  batch.

## Failure modes / regression-prone paths

- `test_grade_anchor_file_exists_and_valid`'s raw_score/normalized_score field-confusion guard —
  confirmed still passes post-edit (guards against an implementer wiring `raw_score` into the
  anchor `score` field; all edits in this ticket used `normalized_score` exclusively, sourced
  directly from each fresh `quality_report.json`).
- Pre-existing `[known tick_budget: ...]` / `[known flag_gated: ...]` annotated failures must
  remain failing (not silently anchored) — verified: 15 such failures remain post-edit, all
  carrying their pre-existing bracket annotation, none touched.

## Result

`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` →
**35 passed, 15 failed (all pre-existing annotated noise), 20 skipped, 18 deselected.**
Zero unexplained failures — satisfies the ticket's Acceptance Criteria.
