---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Normal flow
- `.github/workflows/test.yml` remains valid YAML after the new job is added
  (`python3 -c "import yaml; yaml.safe_load(...)"`).
- The new `simq-grade-drift` job's trigger condition matches the existing "Slow regression" job's
  exactly (push-to-main / schedule / workflow_dispatch), confirmed by direct comparison.
- `make simq-full-audit-full` still runs to completion locally (all 3 steps: engine re-run + diff,
  pytest regression suite, coverage-gap scan) without crashing, regardless of REGRESS count.

## Edge cases
- The job must NOT fail the overall PR/workflow status even when regressions are found (the whole
  point) — verified via `continue-on-error: true` on the step, matching the existing "Type check
  (informational)" job's exact pattern.
- The existing PR-gating "Simulation quality" job's own behavior is unchanged (still silently skips
  anchor comparisons, since it doesn't populate `data/calibration/`) — confirmed no edits were made
  to that job.

## Failure modes
- If `make simq-full-audit-full` itself crashes (not just reports REGRESS) inside the informational
  job, `continue-on-error: true` at the step level still prevents the overall workflow from failing
  — this is deliberate (a crash in this job must never block a push to main, matching CLAUDE.md's
  "monitoring write failure must never fail the workflow" spirit applied to this diagnostic gate).

## Regression-prone paths
- `test_grade_regression.py`'s own test suite is unaffected in shape — no test function signatures,
  fixtures, or parametrize lists changed, only the module docstring. Confirmed by running the full
  file's fast-tier suite before and after the docstring edit and diffing pass/fail/skip counts
  (should be identical, since docstring text has zero runtime effect).

## Commands
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — YAML validity.
- `python3 tools/evaluate_simq.py --dry-run` (after a real engine re-run has populated
  `data/calibration/`) — confirms the tool itself still runs; used during investigation to get the
  AC #1 fresh-drift breakdown without re-paying the ~7min engine-rerun cost twice.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — confirms the real,
  complete (band + score tolerance) anchor comparison, once `data/calibration/` is populated.
- `pytest tests/simulation_quality/ -m "not slow and not extra_slow" -q` — full domain regression
  sweep, confirms no new failures introduced by the docstring-only production-adjacent edit.
