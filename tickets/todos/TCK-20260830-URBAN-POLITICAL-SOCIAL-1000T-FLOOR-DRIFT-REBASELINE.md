---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE
phase: open
date: 2026-08-30
tags: [testing, corpus, calibration, social]
---

# TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE

## Title
Re-baseline `test_urban_political_seed42_1000t_social_grade_stability`'s SOCIAL Floor (Real Drift,
Not a Backpressure Artifact)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Filed from `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`. That ticket fixed the
persistence-phase backpressure bug that previously made this test fail with
`CalibrationIntegrityError`/timeout. With the fix, the test now completes cleanly (3/3 trials, no
integrity error) but fails on a genuine, now-visible floor/tolerance drift:

```
SOCIAL: mean_score=36.8373 vs anchor_score=15.45 (tolerance abs_floor=6.5052)
per-trial values: [32.3, 34.424, 43.788]
```

This is a large, consistent upward drift (all 3 trials well above the anchor + tolerance band),
not test flakiness. It is very likely the same root-cause pattern already established by
`TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE` (44/61 corpus-wide SOCIAL-pillar drifts
traced to `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION` now being ON by default plus
several M1-batch tickets wiring real content behind previously-dormant cooperation/belief paths)
— but that ticket only covered `test_grade_regression.py`'s fast-tier (`FAST_ANCHOR_KEYS`)
corpus, which does NOT include this slow-tier (1000t) `test_corpus_diversity.py` test. This ticket
exists because this specific test was never in scope for that rebaseline and needs its own
evidence-backed floor update using `test_corpus_diversity.py`'s own established multi-batch
tolerance-band methodology (see `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s
precedent for exactly this kind of re-baseline).

## Scope
- Confirm the SOCIAL drift's root cause (do not assume it's identical to the fast-tier corpus
  pattern without checking — `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` has also
  landed since the original drift was measured, which could itself move this score further;
  re-measure fresh on current HEAD, not the numbers quoted above).
- Re-run `test_corpus_diversity.py`'s multi-batch trial methodology for this specific test and
  derive a new evidence-backed `SCORE_TOLERANCE_OVERRIDES`/floor entry.
- Update the floor with the same rigor and documentation style as
  `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`.

## Out of Scope
- Any other `test_corpus_diversity.py` test not named here.
- The persistence-phase performance fixes already landed by the filing ticket.
- Re-touching `grade_anchors.json` (a different fixture entirely, already handled by the separate
  fast-tier corpus rebaseline).

## Acceptance Criteria
- `test_urban_political_seed42_1000t_social_grade_stability` passes with a fresh, evidence-backed
  floor.
- The floor update documents its reasoning (root cause, evidence) inline, matching the file's
  existing documentation conventions for prior re-baselines.

## Related Tickets
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (filing ticket, disclosed this
  finding by fixing the bug that was masking it)
- TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE (precedent methodology, different fixture)
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (precedent methodology, same fixture)
- TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING (may affect the fresh measurement)

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py

## Assumptions / Open Questions
Whether this is the same SOCIAL-drift root cause as the fast-tier corpus rebaseline, or something
specific to the 1000-tick window — not yet confirmed, to be resolved during investigation.

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
