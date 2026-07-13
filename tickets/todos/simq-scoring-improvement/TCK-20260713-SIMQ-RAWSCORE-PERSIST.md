---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-RAWSCORE-PERSIST
phase: open
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-RAWSCORE-PERSIST

## Title
Persist raw `normalized_score` alongside the letter grade in `grade_anchors.json`, with its own
regression-tolerance check

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tests/simulation_quality/fixtures/grade_anchors.json` currently stores only the discretized
letter grade per pillar (confirmed: a bare string, e.g. `"S"`) — never the raw `normalized_score`
that produced it, even though every `quality_report.json` computes and prints it. Combined with S
being an unbounded top band (`quality_scoring_contract.md` §4.5: `S | >2.0 | Exceptional`, no
upper limit specified) and `test_grade_regression.py`'s comparison
(`_within_band`, line ~140) only ever checking the letter grade, this makes the regression-
detection goal blind in both directions for any pillar already at S: a real improvement (e.g.
norm-score 2.1 → 10.0) shows as "S → S", invisible — but so does a real *regression* (10.0 → 2.1)
that doesn't happen to cross a full grade-letter boundary. The anchor system can currently only
catch changes that cross a grade-letter line, not changes in magnitude within one.

**This is explicitly not the excluded Non-Goal.** SimQ's §14 rules out "historical run comparison"
(dashboards, trend charts across runs over time) — that stays out of scope, reaffirmed 2026-07-10.
This ticket is narrower: one additional number stored per anchor entry, checked with one
additional tolerance assertion, squarely inside the existing regression-detection goal (§1), not a
new comparison/analytics capability.

## Scope
- Extend `grade_anchors.json`'s per-pillar schema from a bare string (`"S"`) to an object carrying
  both grade and score (e.g. `{"grade": "S", "score": 2.87}`) — migration needed for all 72×10
  existing entries. **Sequence this to reuse `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s re-anchor
  pass — do not run a second full corpus sweep purely for this migration.**
- Extend `test_grade_regression.py`'s comparison logic to additionally assert the raw score stays
  within an empirically-determined tolerance band (e.g. a percentage or absolute delta — to be
  determined by investigation, not guessed) of the anchored value, independent of whether the
  letter grade moved.
- Update any other code that reads `grade_anchors.json` entries as bare strings (grep for
  consumers before assuming `test_grade_regression.py` is the only one — `tools/evaluate_simq.py`
  is a known second consumer).

## Out of Scope
- Any new dashboard, trend chart, or cross-run comparison UI/tooling — that is the excluded §14
  Non-Goal ("historical run comparison"), explicitly not reopened by this ticket.
- The weight/threshold recalibration itself (`TCK-20260713-SIMQ-SCORE-CEILING-FIX`) — this ticket
  only adds visibility into score magnitude; it does not change what the scores are.
- Persisting scores anywhere beyond `grade_anchors.json` (e.g. no new long-term storage of
  `data/calibration/`'s per-run reports — those remain transient/gitignored as today).

## Acceptance Criteria
- [ ] `grade_anchors.json` stores both grade and raw score per pillar per anchor entry.
- [ ] `test_grade_regression.py` asserts the raw score stays within a documented tolerance of the
      anchored value, in addition to the existing letter-grade band check.
- [ ] A deliberately-injected synthetic score regression that stays within the same letter-grade
      band (e.g. an S-graded pillar's score cut in half but still >2.0) is caught by the new
      tolerance check — and demonstrated to NOT have been caught by the old letter-only check, as
      a concrete before/after proof this ticket closes the gap it claims to.
- [ ] The chosen tolerance width is justified against real run-to-run variance data (not guessed)
      — cite `docs/audits/D20_simq_integration.md`'s wall-clock-throttle findings or equivalent
      fresh evidence.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` — sequenced before this ticket to share one re-anchor pass.

## Related Docs
- `docs/simulation_quality/current_state.md` — Recommendation 4, the finding this ticket addresses.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 1b, this ticket's source.
- `docs/simulation_quality/quality_scoring_contract.md` §4.5 (grade bands, S is unbounded), §14
  (Non-Goals — confirm this ticket's scope stays narrower than the excluded item), §1 (goals).
- `docs/audits/D20_simq_integration.md` — wall-clock-throttle run-to-run variance findings, needed
  to justify the tolerance width.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` (`_within_band`, line ~140; `GRADE_ORDER`,
  line ~34)
- `tools/evaluate_simq.py` (a second known consumer of the anchor file's schema — confirm no
  others exist before assuming these two are the full consumer set)

## Assumptions / Open Questions
- The exact tolerance width (percentage vs. absolute delta, and its numeric value) is not yet
  determined — first investigation task, informed by real variance data, not guessed.
- Whether the schema migration is a one-time script or needs to be re-derivable (e.g. re-running
  the corpus sweep regenerates both fields together) is left to the implementer.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
