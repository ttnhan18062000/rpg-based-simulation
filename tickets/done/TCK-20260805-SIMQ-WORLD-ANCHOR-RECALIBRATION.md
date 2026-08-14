---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION
phase: done
date: 2026-08-05
tags: [simulation-quality, calibration]
---

# TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION

## Title
Recalibrate WORLD pillar grade anchors against the spawn-occupancy signal

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (landed 2026-07-30) correctly added a new, intentional
negative-weighted signal (`spawn_occupancy_violation`, weight -30.0) to `WorldDynamicsScorer`,
routing real `LAW-SPAWN-OCCUPANCY` hard-law violations into the WORLD pillar's score. The WORLD
entries in `tests/simulation_quality/fixtures/grade_anchors.json` were never recalibrated against
this change. A fresh full-corpus live-engine re-run on 2026-08-05 (`make simq-full-audit-full`,
75/76 scenarios) reproduces 19 of 20 total `test_grade_regression.py` failures as this exact
pattern — the WORLD anchors reflect a pre-signal baseline that no longer matches the scorer's real
(and correctly working) output. Until recalibrated, the WORLD regression gate cannot distinguish
this known, already-diagnosed baseline shift from a genuine future regression, which defeats the
gate's purpose for this pillar.

## Scope
- Regenerate/update the WORLD pillar entries (`{"grade": ..., "score": ...}`) in
  `tests/simulation_quality/fixtures/grade_anchors.json` for every anchor scenario, using a fresh
  live-engine calibration run that includes the `spawn_occupancy_violation` signal.
- Verify `tests/simulation_quality/test_grade_regression.py` passes cleanly for WORLD across the
  full anchor corpus after recalibration (both `_within_band()` and `_within_score_tolerance()`).
- Record the recalibration event and its rationale (this is a durable, intentional baseline shift,
  not a silent number change) — see Architecture Rule below.

## Out of Scope
- Any other pillar's anchors (NARRATIVE, COMBAT, PROGRESSION, FACTION, INFORMATION, COGNITION,
  SOCIAL, ECONOMY, AGENCY) — confirmed unaffected by this signal addition; do not touch.
- `WorldDynamicsScorer`'s scoring logic itself — the signal and its weight are correct and
  intentional (`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`'s own scope); this ticket only recalibrates
  the anchors that test against it.
- The 1 unreliable calibration run (`unit_selfmodel_pilot_seed42_1000t`, failed integrity check
  under observability backpressure this refresh) — unrelated, informational only, not investigated
  or acted on here.

## Acceptance Criteria
1. `tests/simulation_quality/fixtures/grade_anchors.json`'s WORLD entries are updated to match a
   fresh live-engine calibration run that includes the spawn-occupancy signal.
2. `pytest tests/simulation_quality/test_grade_regression.py -k WORLD` (or the full regression
   suite scoped to WORLD) passes with no anchor-mismatch failures.
3. A rationale note explaining *why* the WORLD anchors moved (the spawn-occupancy signal, not a
   regression) is captured somewhere durable and inspectable — either as a comment/note alongside
   the anchor file's WORLD section, or in this ticket's Completion Summary plus a
   `docs/simulation_quality/current_state.md` update — not just implied by the diff.
4. `docs/simulation_quality/current_state.md`'s Finding 1 / grade-distribution numbers are updated
   to reflect the recalibration (currently describes this as an open, stale-anchor problem).

## Related Tickets
- `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` — added the `spawn_occupancy_violation` signal this
  recalibration is catching up to.
- `TCK-20260716-PLACELEGAL-HARDLAW` — the underlying hard-law this signal detects violations of.
- `TCK-20260630-SIMQ-ANCHORS`, `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`,
  `TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT`, `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`
  — prior anchor-recalibration precedent tickets, same layer/pattern.

## Related Docs
- `docs/simulation_quality/current_state.md` — Finding 1 in the 2026-08-05 refresh section
  documents this exact gap with full evidence.
- `docs/audits/D20_simq_quality_status_review.md` — Finding 1, Item A in the Candidate Work Items
  table.
- `docs/simulation_quality/quality_scoring_contract.md` — WORLD pillar scoring spec.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py`
- `src/simulation_quality/scorers/world_dynamics_scorer.py` (read-only reference — not modified)

## Assumptions / Open Questions
None — root cause fully diagnosed already (Finding 1), no further investigation needed before
implementing.

## Implementation Notes
Ran `make simq-full-audit-full` for a fresh full-corpus live-engine calibration (76 scenarios,
`data/calibration/*/quality_report.json`). Wrote a small script
(`update_world_anchors.py`, scratch-only, not committed) that reads each scenario's real
`pillars.WORLD.{grade,normalized_score}` and overwrites ONLY the `WORLD` key in
`grade_anchors.json` for that scenario — verified structurally (script only ever touches the
`"WORLD"` dict key) and empirically (diffed before/after: 0 non-WORLD pillar entries changed, 37
WORLD entries updated, 39 unchanged). Updated `docs/simulation_quality/current_state.md`'s Finding
1 and grade-distribution table with the real post-fix numbers (also noticed
`unit_selfmodel_pilot_seed42_1000t`, flagged unreliable in an earlier same-day refresh, completed
cleanly this run — noted honestly rather than silently carrying the old exclusion forward).

## Test Summary
`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`: before fix, 20 failed
(19 WORLD + 1 unrelated) / 45 passed / 18 deselected. After fix: 1 failed / 64 passed / 18
deselected — the sole remaining failure is `urban_political_seed42_200t`'s pre-existing,
already-documented NARRATIVE/SOCIAL variance, explicitly out of this ticket's WORLD-only scope.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` — WORLD entries recalibrated for 37
  scenarios
- `docs/simulation_quality/current_state.md` — Finding 1 marked resolved, grade-distribution table
  updated

## Completion Summary
Recalibrated `grade_anchors.json`'s WORLD pillar entries against a fresh full-corpus live-engine
run, closing the regression-gate blind spot `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL`'s intentional
`spawn_occupancy_violation` signal had opened. All 4 acceptance criteria met: (1) WORLD anchors
updated for every affected scenario from a real calibration run; (2) `test_grade_regression.py`
passes cleanly for WORLD (0 WORLD failures, down from 19); (3) rationale captured here and in
`current_state.md`; (4) `current_state.md`'s Finding 1 and grade-distribution table both updated.
