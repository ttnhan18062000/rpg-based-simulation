---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE
phase: done
date: 2026-08-07
tags: [simulation-quality, combat]
---

# TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE

## Title
26 COMBAT anchors show a stable, bit-identical-across-3-trials `combat_dormant` score drift —
F6 wall-clock-noise hypothesis refuted; determine the actual root cause (real regression vs.
deterministic-under-current-load F6 variant)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION` ran the established 3-independent-trial
methodology (`TCK-20260710`/`TCK-20260715` precedent: real throttled `Kernel`, no `audit_mode`)
against 26 COMBAT (run_key, pillar) pairs flagged by a 2026-08-07 full-corpus SimQ verification run.
**Every one of the 26 pairs produced a bit-identical `normalized_score` across all 3 independent
process-level trials** — zero variance, the opposite of genuine load-sensitivity (which shows real
trial-to-trial jitter per Parts 1/2 of `docs/simulation_quality/eval_matrix_results.md`'s own
precedent sweeps). This refutes that investigation's own working hypothesis (F6 wall-clock-throttle
noise) for all 26 pairs, but does NOT establish what the actual cause is.

`combat_dormant` (`src/simulation_quality/scorers/combat.py:54-66`) fires when `tick >
zero_combat_by_tick` (200, `config/simulation_quality/detection_params.yaml:11`) with zero COMBAT
events recorded. 22 of the 26 flagged pairs are exactly `_200t` scenarios (zero margin before the
gate); the other 4 are `_500t` scenarios with 300 ticks of margin past the gate, yet show the same
stable zero/negative signal — this pattern favors "COMBAT events are not being generated/extracted
at all for these worlds" over "combat merely started a few ticks late due to throttling."

This ticket's own predecessor left the 26 anchors as flagged, intentionally-failing gate conditions
(`tests/simulation_quality/test_grade_regression.py -m "not slow"`) rather than converting them to
`SCORE_TOLERANCE_OVERRIDES` — converting a confirmed-stable, unexplained drift into a tolerance
override would silence the signal, not resolve it.

## Scope
1. **Investigate**:
   - Determine whether the 26 affected worlds share a common trait (world family, combat-trigger
     content config, hostile-faction density, entity roster) that would explain zero COMBAT
     initiation within their own tick budgets — cross-reference `config/` world/profile definitions
     for the 26 run_keys.
   - Trace whether any recently-landed change (this session's own quest_event push-migration epic,
     or any other recent `src/observability/`/`src/simulation_quality/` change) could have broken
     COMBAT event generation or extraction specifically — check `git log` for `src/domains/combat/`
     (or wherever combat initiation lives) and `src/observability/event_extractor.py`'s own COMBAT
     event-type handling for recent changes.
   - Determine whether this is a genuinely NEW regression (compare against a historical stored
     calibration baseline predating the suspected change, if one exists in `stored_artifacts/`) or
     whether these 26 worlds have ALWAYS had this property and their anchors were simply
     miscalibrated from the start.
   - Investigate whether `WatchdogTrip`/`PRESSURE`-mode firing unusually early (tick 6-60, vs F6's
     documented ~tick 300-320 onset — noted in this session's own earlier full-corpus run logs) is
     itself an anomaly worth separately investigating, even though the predecessor ticket's 3-trial
     data suggests it isn't the direct cause of THIS specific drift (zero trial-to-trial variance
     argues against a wall-clock-timing-dependent cause).
2. **Plan**: design the fix once root cause is confirmed — likely one of: a genuine combat-initiation
   logic bug, a broken/stale world config for these specific worlds, or (if these worlds legitimately
   never produce hostile encounters within their tick budget) a corrected, intentional
   `combat_dormant` anchor recalibration with a documented rationale (not a blind tolerance override).
3. **Implement**: apply the fix.

## Out of Scope
- Any change to `src/engine/kernel.py`'s watchdog/throttle/`ResourceGovernor` logic — still out of
  scope per the predecessor ticket's own guard, unless this investigation's own evidence directly
  implicates it (in which case scope this ticket to `docs/guidelines/intentional_divergences.md`
  disclosure + a properly-scoped follow-up, not a same-ticket kernel change).
- Re-litigating the predecessor ticket's own disposition work (already correctly done, DONE).

## Acceptance Criteria
- [ ] investigation.md identifies the actual root cause with real evidence (not guessed)
- [ ] Fix applied (or, if these 26 worlds are confirmed to genuinely never produce hostile
      encounters within their tick budget, anchors corrected with a documented, evidenced rationale)
- [ ] `tests/simulation_quality/test_grade_regression.py -m "not slow"` passes cleanly for all 26
      previously-flagged pairs
- [ ] `docs/simulation_quality/current_state.md`/`eval_matrix_results.md` updated with the resolution
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION (predecessor — ran the 3-trial
  verification, refuted the F6 hypothesis, left anchors flagged pending this ticket — DONE)
- TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY, TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP
  (established the 3-trial methodology and genuine-load-sensitivity precedent this ticket's own
  predecessor used to rule OUT load-sensitivity here — DONE)

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` ("Anchor Reliability Verification, Part 6" —
  this finding's own evidence trail)
- `docs/simulation_quality/current_state.md` ("2026-08-07 COMBAT score-tolerance drift investigation")
- `docs/audits/D06_longrun_health.md` (F6 — ruled out as the direct cause for this specific drift,
  but the early WatchdogTrip-onset anomaly noted here is still unexplained)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION/` (3-trial raw
  evidence and disposition)

## Related Code Areas
- `src/simulation_quality/scorers/combat.py` (`combat_dormant` trigger)
- `src/observability/event_extractor.py` (COMBAT event-type extraction — check for recent changes)
- Combat-initiation logic (wherever COMBAT events actually originate — not yet located, first
  Investigate task)
- `tests/simulation_quality/fixtures/grade_anchors.json` (26 COMBAT entries, left unchanged pending
  this ticket)

## Assumptions / Open Questions
- Whether a pre-regression historical baseline calibration exists anywhere in `stored_artifacts/`
  to compare against — not assumed; Investigate must check before concluding "always broken" vs.
  "newly broken."

## Implementation Notes
Subagent spawn cap (200/200) reached before this session started (carried over from the
predecessor ticket) — Investigate/Implement/Verify performed directly.

`mcp__knowledge-search__search_docs` (Context Scan Step 1, mandatory) surfaced the root cause on
the FIRST query — no guessing needed. Two already-landed, same-day (2026-08-06) tickets fully
explain the predecessor investigation's own "zero trial-to-trial variance" finding:
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY` (deliberate DEV-002 ruling:
`ENABLE_COMBAT_ENGAGEMENT` off corpus-wide, confirmed still true) and its child hotfix
`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` (confirmed still live in
`src/observability/event_extractor.py:22-24,42` — `_NON_COMBAT_OUTCOME_KINDS`,
`_real_combat_update()`). That hotfix's own AC explicitly deferred `grade_anchors.json`
recalibration to "a separate ticket" — this ticket is that follow-up.

Not a code regression: reused the predecessor ticket's own already-captured 3-trial data (no new
engine runs needed) and recalibrated all 26 COMBAT `grade_anchors.json` entries to their
confirmed-stable post-fix values.

Disclosed, deliberately NOT fixed: closing this out surfaced 1 new, unrelated failure
(`hero_guild_routing_seed42_500t`/COGNITION — anchor far from 3 fresh trials, with small genuine
jitter unlike COMBAT's zero-variance signature). No diagnosed cause, left untouched rather than
guessed at or silently absorbed into this ticket's own COMBAT-only scope.

## Test Summary
`tests/simulation_quality/test_grade_regression.py -m "not slow"`: 1 failed (the disclosed,
unrelated, out-of-scope COGNITION finding), 68 passed, 18 deselected — all 26 previously-flagged
COMBAT pairs now pass. `git status --porcelain -- src/engine/` shows only pre-existing,
already-uncommitted modifications from earlier in this session (unrelated to this ticket's own
work, which touched only `grade_anchors.json` and 2 docs files) — confirmed via this ticket's own
tool-call history, not a new anti-drift violation.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` (26 COMBAT entries recalibrated)
- `docs/simulation_quality/current_state.md` (root-cause closure note)
- `docs/simulation_quality/eval_matrix_results.md` (Part 6 closure note)

## Completion Summary
Root cause confirmed via the mandatory Context Scan's very first search_docs query, not guessed or
chased through code archaeology — the answer was already fully documented one day prior. Corrected
the predecessor ticket's own working hypothesis (F6 wall-clock noise) with the real explanation
(a deferred anchor recalibration following an already-fixed extraction bug + an already-deliberate
feature-gate ruling), matching this session's own recurring pattern (NARRATIVE/PROGRESSION earlier,
now COMBAT) of disclosed-cause anchor staleness rather than live engine regressions. Disclosed
rather than fixed 1 newly-surfaced, unrelated COGNITION finding to avoid scope creep on
unevidenced ground.
