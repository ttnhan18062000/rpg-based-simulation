---
status: active
layer: strategy
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT
tags: [testing, bug]
---

# Test Plan: TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT

## Normal Flow
- `test_scoring_formula_constants_stable` with the corrected `PERSONALITY_BIAS_WEIGHT = 0.50`:
  expected score for the `GATHER_RESOURCE`/greed=1.0/confidence=1.0 unblocked case becomes `0.65`,
  matching `AdventureRouteScorer.score()`'s real, current output.

## Edge Cases
- The `route_blocked` assertion (`scored_blocked.score == 0.0`) depends on `expected_score` (the
  variable, now `0.65`) plus `BLOCKER_PENALTY = 2.0` still exceeding the positive terms — `0.65 +`
  nothing survives the `max(0, ... - 2.0)` clamp regardless, so this assertion needs no direct edit
  but must be re-run to confirm it still passes with the corrected `expected_score`.
- The final assertion (`scored_unblocked.score > scored_blocked.score`) is comparison-based and
  needs no direct edit either, but must be re-confirmed.

## Failure Modes
- If the constant is corrected but the docstring's `§6.2` citation is left uncorrected, a future
  reader following the citation would land on the general weight table, not the calibration note in
  §6.4 that explains WHY 0.50 (not just what) — Implement must update both.

## Regression-Prone Paths
- Confirm no other test in `tests/integration/scenarios/test_balance_regression.py` (or anywhere
  else in `tests/`) references `PERSONALITY_BIAS_WEIGHT`/`CONFIDENCE_BONUS_WEIGHT` with a stale
  value — already confirmed via `grep -rn` in Investigate (4 matches, all in this one file/function).

## Test Commands
```
.venv/bin/python3 -m pytest tests/integration/scenarios/test_balance_regression.py -v
```
Full file, not just the target test, to catch any regression in sibling tests in the same file.
