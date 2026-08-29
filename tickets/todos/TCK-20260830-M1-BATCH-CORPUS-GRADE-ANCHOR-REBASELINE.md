---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
phase: open
date: 2026-08-30
tags: [simulation-quality, grade-thresholds, calibration, social, feature-flags]
---

# TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE

## Title
Re-baseline `grade_anchors.json` After M1 Batch's Real Behavior Changes (63/71 Fast Corpus Tests
Now Failing)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
This is the "verify with SimQ" step requested after the M1 Quick Wins batch (22 tickets) and its
~10 follow-up tickets landed on `m1-quick-wins`. Running `make simq-full-audit-full` (real engine
re-run across all 71 fast (≤500t) corpus scenarios, diffed against
`tests/simulation_quality/fixtures/grade_anchors.json`) found **63 of 71 tests failing** — nearly
the entire corpus.

Root-caused via a dedicated read-only investigation (evidence-based, not guessed — verified
against real `data/calibration/*/quality_scores.jsonl` event data and `git log`):
`tests/simulation_quality/fixtures/grade_anchors.json` has **zero commits** anywhere in the
entire M1 batch, despite the batch landing multiple real, intentional behavior changes:
`TCK-20260824-ROLLOUT-FLAG-DECISIONS` flipped `ENABLE_BELIEF_ASSIMILATION` and
`ENABLE_SOCIAL_COOPERATION` `ON` by default corpus-wide (independently confirmed:
`src/domains/optimization/feature_flags.py:37,52` both now `FeatureMode.ON`), and several other
tickets wired real production content behind those and other previously-dormant paths
(`TCK-20260824-WIRE-ORPHANED-MECHANISMS`, `TCK-20260824-TOWN-CENTER-POINTER-FIX`,
`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, `TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING`, and
others — see the investigation's full ticket list below).

Of the 61 non-already-tracked failures (2 others are already covered by
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`), the investigation found:
- **0 confirmed real regressions.**
- **~55/61** legitimate M1-batch-caused drift, each traced to a specific causing ticket and
  verified against real event data (dominant pattern: 44/61 involve `SOCIAL` drifting sharply
  upward — cooperation/belief content firing for the first time; smaller patterns in
  `PROGRESSION`, `COMBAT`, `ECONOMY`, `NARRATIVE`, `COGNITION`, `AGENCY`).
- **~6/61** already fully covered by the pre-existing `tools/simq_ceiling.py` known-tolerance
  mechanism (tick-budget / flag-gated / watchdog-variance noise), i.e. not new drift at all.

Full per-run_key classification, evidence, and causing-ticket mapping is preserved in this
ticket's own investigation.md (see Implementation Notes for where the raw investigation output
was captured).

## Scope
- Re-run `make calibrate` (or the file's own documented anchor-regeneration procedure — see
  `tests/simulation_quality/fixtures/grade_anchors.json`'s own module docstring / the
  `test_grade_regression.py` module docstring, lines ~23-30) for all `FAST_ANCHOR_KEYS` on the
  current `m1-quick-wins` HEAD.
- Regenerate `grade_anchors.json` with the fresh values.
- In `investigation.md`, explicitly document (not silently re-center):
  1. The `SOCIAL`/cooperation-wiring root cause for the ~44 `SOCIAL`-pillar entries.
  2. The wound-penalty-driven `PROGRESSION` sign-flip specifically observed in the two
     `urban_political_*_500t` worlds (the investigation found `PROGRESSION` moves the *opposite*
     direction there vs. the 200t worlds — same wound-penalty wiring, opposite-sign effect
     depending on run length; this needs a one-line explanatory note, not silent re-centering).
  3. A due-diligence check (not necessarily a fix) on the three `loop_detected` `SOCIAL`-decrease
     cases (`urban_political_seed42_200t`, `highland_traverse_seed42_200t`,
     `lifecycle_full_coverage_world_seed42_200t`) — these show very high per-entity
     cooperate/expire event cadence (some entities firing every tick) triggering
     `pillar_accumulator.py`'s anti-spam `loop_detected` dampener. Confirm this reads as
     legitimate (cooperation content going from dormant to real, expected to be dense) rather
     than a tuning problem, before accepting the new lower score as the anchor. If it looks like
     a real tuning issue (e.g. cooperation offers should have a cooldown and don't), disclose it
     as a separate finding — do not silently fix cooldown logic inline as part of a re-baseline
     ticket.
- Re-run `test_grade_regression.py -m "not slow"` after regeneration and confirm it passes clean
  (mirroring `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s precedent for a
  legitimate-fix-caused batch of anchor drift, `docs/testing/regression_policy.md` §9).

## Out of Scope
- The 2 already-tracked `urban_political_selfmodel*_probe` failures — covered by
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`, do not duplicate that work
  here.
- Slow-tier (`-m slow`, 1000t/2000t) corpus tests — out of this ticket's scope; run separately if
  warranted after this lands.
- Fixing any actual code defect uncovered during due diligence on the `loop_detected` cases (per
  above, disclose rather than fix inline).
- Changing any feature flag default — this ticket only re-baselines anchors to match already-
  decided, already-shipped defaults; it does not revisit the ROLLOUT-FLAG-DECISIONS verdicts.

## Acceptance Criteria
- `make simq-full-audit-full`'s `test_grade_regression.py -m "not slow"` step passes clean (or
  any remaining failure is independently new and disclosed as its own finding, not silently
  absorbed into the re-baseline).
- `grade_anchors.json`'s diff is reviewed for genuine content (not a raw full-file rewrite
  artifact) — confirm the diff touches only the run_keys this ticket's investigation named.
- The three `loop_detected` cases and the `PROGRESSION` sign-flip nuance are explicitly written up
  in investigation.md, not silently absorbed into a blanket re-baseline.

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (flipped ENABLE_BELIEF_ASSIMILATION/ENABLE_SOCIAL_COOPERATION ON)
- TCK-20260824-WIRE-ORPHANED-MECHANISMS
- TCK-20260824-TOWN-CENTER-POINTER-FIX
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
- TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (precedent for this kind of ticket)
- TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION (covers the 2 excluded failures)

## Related Docs
- docs/testing/regression_policy.md (§9)
- tests/simulation_quality/test_grade_regression.py (module docstring, anchor-regeneration procedure)

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json
- src/simulation_quality/pillar_accumulator.py (loop_detected dampener)
- tools/simq_ceiling.py

## Assumptions / Open Questions
Whether the 3 `loop_detected` cooperation-cadence cases represent a real tuning gap (cooperation
offers should have a cooldown) or expected behavior for newly-live content — to be resolved
during this ticket's own due-diligence check, not assumed either way going in.

## Implementation Notes
(Not yet implemented. The full per-run_key classification from the filing investigation — every
one of the 61 run_keys with its pillar(s), actual vs anchor values, classification, and evidence
— should be re-derived fresh into this ticket's own investigation.md during Investigate, using
the same methodology: read `data/calibration/*/quality_scores.jsonl` event data directly, cross-
reference `git log --oneline main..m1-quick-wins`, do not assume the filing investigation's
classifications are still current without re-verifying against the actual HEAD at implementation
time.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
