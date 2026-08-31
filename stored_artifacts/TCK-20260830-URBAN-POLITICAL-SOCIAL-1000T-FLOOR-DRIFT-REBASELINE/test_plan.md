---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE
artifact_type: test_plan
phase: open
date: 2026-08-30
tags: [testing, corpus, calibration, social]
---

# Test Plan — TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE

## Regression Surface (existing tests that must pass)

- `tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability`
  — the target test itself, must pass with the new evidence-backed anchor.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_score_tolerance_*` /
  `test_within_band_default_tolerance_unchanged` (in
  `tests/simulation_quality/test_grade_regression.py`) — the shared `_within_band` /
  `_within_score_tolerance` helper functions this test imports must remain untouched by
  this ticket (they are not — this ticket only edits an inline `anchors` dict literal in
  `test_corpus_diversity.py`).
- No other test in `test_corpus_diversity.py` is expected to change behavior — this
  ticket edits exactly one test function's `anchors` literal.

## New Tests Required (per AC)

None. The Acceptance Criteria are satisfied by updating the existing test's anchor
constant with fresh, documented evidence — no new test function is required (matching
the precedent ticket's own approach, which edited existing tests' literals rather than
adding new ones).

## Scoped Pytest Commands

Primary target (real, unmocked, 1000-tick, 3-trial run — slow, `resource_budget_large`):

```
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability -v --tb=short
```

Because `test_corpus_diversity.py`'s own docstring documents genuine standalone-vs-bundled
run-to-run variance for this file (16-vs-13 finding, `Kernel`'s wall-clock throttle under
system load) as an already-known, already-deferred, unrelated finding — not something this
ticket is scoped to fix — the primary verification is the single named test run standalone
(above), which is deterministic-enough to interpret cleanly. A broader
`tests/unit/worldassembly/` sweep is optional context, not a blocking requirement, per that
same already-accepted finding.

## Anti-Drift Test Guards

- The test's own internal `band_failures`/`score_failures` assertions are the actual
  regression guard — this ticket must not weaken them (e.g. widening `band_tolerance`
  beyond what the evidence in investigation.md supports, or hand-waving a floor value not
  derived from real trial data).
- Do not edit `_within_band`/`_within_score_tolerance` in
  `tests/simulation_quality/test_grade_regression.py` — shared helpers, out of scope.
- Do not touch `grade_anchors.json` or `SCORE_TOLERANCE_OVERRIDES` — different fixture,
  explicitly Out of Scope per the ticket.
