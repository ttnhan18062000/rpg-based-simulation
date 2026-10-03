---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE
artifact_type: plan
phase: open
date: 2026-08-30
tags: [testing, corpus, calibration, social]
---

# Plan — TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE

## Ordered Steps

1. **Edit `tests/unit/worldassembly/test_corpus_diversity.py`'s
   `test_urban_political_seed42_1000t_social_grade_stability` (line ~1087-1089)**: replace
   the `anchors` dict literal's `SOCIAL` entry from
   `{"grade": "S", "score": 15.45, "abs_floor": 6.5052}` to
   `{"grade": "S", "score": 35.1038, "abs_floor": 2.5387}`. Grade stays `S` (unchanged —
   all 9 fresh trials landed S).
2. **Update the test's own docstring** (line ~1050-1069) to record this re-baseline event:
   what changed, the fresh 9-trial (3-batch) evidence, and a pointer to this ticket —
   matching this file's own established per-test documentation convention (see e.g.
   `test_urban_political_seed123_500t_cognition_grade_stability`'s and
   `test_urban_political_seed123_1000t_social_economy_grade_stability`'s docstrings for the
   pattern: what changed, why, the evidence, a sanity check).
3. **Update the module docstring's §5 town_center re-baseline section** (lines 24-88) with
   a short addendum/cross-reference noting that
   `test_urban_political_seed42_1000t_social_grade_stability` — one of the 5 tests that
   section deferred to the backpressure ticket — has now been separately re-baselined by
   this ticket, with a pointer to this ticket ID. Do not rewrite that section's own
   historical account of the 2026-08-28/29 events — append, don't rewrite.
4. **Update `docs/testing/regression_policy.md`**: add a one-line cross-reference entry
   for this re-baseline event, matching the existing "TCK-20260824/TCK-20260828
   Re-Baseline" note's style/location (found during Investigate).
5. **Run the target test** (`pytest
   tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability
   -v --tb=short`) — a fresh 4th independent 3-trial draw (via the test's own real code
   path, not the investigation's standalone probe script) — confirm it passes cleanly
   against the new anchor. This is the Test phase's own scoped run, not a separate manual
   step, but sequenced here since it is the concrete verification this plan's Step 1 edit
   is judged against.
6. **Update ticket** `tickets/inprogress/TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE.md`'s
   Implementation Notes / Files Changed / Completion Summary sections (done at Implement
   phase, per workflow convention).

## Files to Change

- `tests/unit/worldassembly/test_corpus_diversity.py` (Steps 1-3)
- `docs/testing/regression_policy.md` (Step 4)
- `tickets/inprogress/TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE.md` (Step 6)

## Explicit Scope Guards (what NOT to touch)

- No other test function in `test_corpus_diversity.py`.
- No `grade_anchors.json` / `SCORE_TOLERANCE_OVERRIDES` (different fixture, out of scope).
- No `src/` file — this is a test-fixture-only calibration change, `behavior_changed=false`.
- No `_within_band` / `_within_score_tolerance` helper functions.
- No re-litigation of the two cooperation-offer tickets' own fixes or the persistence
  backpressure fix — all three are already closed and correct; this ticket only
  recalibrates a test constant to match their already-shipped effect.

## Dependency Map

Step 1 (anchor value) has no dependency. Step 2/3 (docstrings) depend on Step 1's final
numbers being settled (they are — derived in Investigate). Step 4 (regression_policy.md)
is independent of 1-3. Step 5 (test run) depends on Step 1 being complete. Step 6 depends
on Step 5's outcome (pass) to write an honest Completion Summary.

## Acceptance Criteria Map

- AC1 ("test passes with a fresh, evidence-backed floor") → Steps 1, 5.
- AC2 ("floor update documents its reasoning inline, matching the file's existing
  documentation conventions") → Steps 2, 3.

## Unresolved Questions

None. The Investigate phase resolved the root-cause question with clean, consistent,
9-trial evidence — no ambiguity requiring human review.
