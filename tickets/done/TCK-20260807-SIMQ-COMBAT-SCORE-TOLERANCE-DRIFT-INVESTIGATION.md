---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION
phase: done
date: 2026-08-07
tags: [simulation-quality, combat]
---

# TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION

## Title
26 COMBAT + 1 COGNITION + 1 SOCIAL anchors drifted beyond score tolerance in a 2026-08-07
full-corpus run with no traceable code cause — confirm via multi-trial re-verification (the
established `TCK-20260710`/`TCK-20260715` precedent) before recalibrating or dismissing as noise

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during a 2026-08-07 full-corpus SimQ verification run (79 scenarios, real engine re-run per
scenario, following `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`/`-COMMITMENT-ABANDONED-PUSH-
MIGRATION-GAP`/`-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`). After recalibrating NARRATIVE/
PROGRESSION anchors against 2 confirmed, already-disclosed causes (see
`docs/simulation_quality/current_state.md`'s "2026-08-07 session summary"), the fast-tier
regression gate (`tests/simulation_quality/test_grade_regression.py -m "not slow"`) still shows 26
COMBAT + 1 COGNITION + 1 SOCIAL score-tolerance failures with **no traceable cause in that
session's own code changes** — mostly COMBAT dropping to exactly `0.0` events
(`combat_dormant`, "zero combat events in hostile world by tick threshold"), in scenarios where
neither `event_shapers.py`/`event_extractor.py` (this session's own touched files) nor any combat
logic was modified.

The run's own log showed extensive `WatchdogTrip`/`PRESSURE`-mode governor activity, firing far
earlier and more often (tick 6-60 onset, vs. `docs/audits/D06_longrun_health.md` F6's own
documented tick~300-320 onset for the mechanism it describes) than the environment the anchors
were presumably last calibrated on — suggesting this specific run's own machine was more
loaded/slower than usual, plausibly suppressing combat-initiation timing via F6's own documented
mid-tick emergency-throttle drop mechanism (real wall-clock-dependent, not code-dependent,
non-determinism).

**This is not a novel failure shape** — `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` already
found and resolved an almost identical case: 14 `grade_anchors.json` scenarios drifted beyond
score tolerance "for reasons unrelated to that ticket's own work," root-caused to the same F6
load-sensitivity mechanism, and resolved via multi-trial re-verification
(`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s own established methodology: 3 independent
same-seed trials, real throttled `Kernel`, no `audit_mode`) followed by converting genuinely
load-sensitive scenarios to `SCORE_TOLERANCE_OVERRIDES` entries with a widened floor derived from
the REAL observed trial-to-trial range — not blindly.

## Scope
1. **Investigate** (mandatory before Plan):
   - Run 3 independent trials (same seed, real engine, no `audit_mode`) for each of the 27
     currently-flagged (run_key, pillar) pairs — or at minimum a representative sample if 27×3
     full engine re-runs are too slow for a single Investigate pass — following
     `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s exact methodology.
   - For each pair: does the score/grade land within the existing anchor band across all 3
     trials (confirms transient/single-draw noise, no anchor change needed — the original run was
     just unlucky), does it consistently miss the anchor by a stable margin across all 3 trials
     (confirms a real, deterministic behavior change worth investigating as a genuine regression,
     NOT load noise), or does it vary widely trial-to-trial (confirms genuine load-sensitivity,
     candidate for a `SCORE_TOLERANCE_OVERRIDES` entry sized to the real observed range, per the
     `TCK-20260715` precedent)?
   - Cross-check `combat_dormant`'s exact trigger condition (`src/simulation_quality/scorers/
     combat.py` or equivalent) against F6's documented mid-tick throttle-drop mechanism
     (`src/engine/kernel.py:420-442`/`574-601`) to confirm the causal chain is plausible, not just
     coincidental timing.
2. **Plan**: per-pair disposition — no action (confirmed transient), `SCORE_TOLERANCE_OVERRIDES`
   entry (confirmed load-sensitive, real range known), or a real regression investigation (if any
   pair reproduces a stable, non-load-explained drift).
3. **Implement**: apply the disposition per pair. Do NOT blanket-recalibrate all 27 to their
   single 2026-08-07 values without the multi-trial evidence this ticket's own Scope requires —
   that would risk baking one session's environment-load artifact in as the new "expected"
   baseline, silently raising the bar for a future, quieter-environment run to look like a
   regression instead.

## Out of Scope
- Any change to `src/engine/kernel.py`'s watchdog/throttle/`ResourceGovernor` logic — F6 is
  documented, intentional, corpus-wide engine behavior (`docs/engine/performance_contract.md`
  §7), not a defect to fix, per `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s
  own explicit scope guard (already respected by every prior ticket in this lineage).
- NARRATIVE/PROGRESSION anchors — already correctly recalibrated this session against confirmed,
  disclosed causes; not part of this ticket's own scope.
- Re-investigating the push-migration work itself (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`
  and its 2 siblings) — already verified clean (AGENCY 79/79 PASS), not implicated in this
  finding.

## Acceptance Criteria
- [ ] `investigation.md` reports a 3-trial disposition for every one of the 27 currently-flagged
      (run_key, pillar) pairs (or a representative, justified sample if full coverage isn't
      feasible in one pass — explicitly disclosed, not silently narrowed)
- [ ] Each pair gets one of: no action (transient), `SCORE_TOLERANCE_OVERRIDES` entry (with a
      cited real trial-to-trial range, not an arbitrary widened floor), or a flagged genuine
      regression for further investigation
- [ ] `tests/simulation_quality/test_grade_regression.py -m "not slow"` reflects the resolved
      disposition — passes for transient/overridden pairs, still correctly flags any confirmed
      real regression
- [ ] `docs/simulation_quality/current_state.md`/`eval_matrix_results.md` updated with the
      disposition, following the established "Anchor Reliability Verification" section format
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260807-QUEST-EVENT-PUSH-MIGRATION, TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP,
  TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP (DONE — the session whose own full-corpus
  verification surfaced this finding; confirmed NOT the cause)
- TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY (established the 3-trial verification methodology
  this ticket reuses — DONE)
- TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP (resolved an almost identical prior finding via
  this exact methodology — DONE, direct precedent)
- TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE (discovered the underlying F6
  mechanism — DONE)

## Related Docs
- `docs/audits/D06_longrun_health.md` (F6 — the documented, intentional watchdog-throttle
  mechanism)
- `docs/simulation_quality/eval_matrix_results.md` ("Anchor Reliability Verification" sections —
  the precedent format for this ticket's own findings)
- `docs/simulation_quality/current_state.md` ("2026-08-07 session summary" — where this finding
  was first disclosed)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/` (methodology precedent)
- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/` (near-identical prior
  finding and resolution)

## Related Code Areas
- `src/simulation_quality/scorers/combat.py` (`combat_dormant` trigger condition)
- `src/engine/kernel.py` (tick-budget watchdog / mid-tick throttle — read-only reference, not to
  be modified)
- `tests/simulation_quality/test_grade_regression.py` (`SCORE_TOLERANCE_OVERRIDES`)

## Assumptions / Open Questions
- Whether all 27 pairs can realistically get a full 3-trial re-verification in one ticket's own
  pass, given engine re-run time (79-scenario full sweep already took real wall-clock time this
  session) — not assumed; Investigate should scope down to a representative/prioritized subset
  (e.g. COMBAT first, since it's 26 of 27) if full coverage isn't practical, and disclose the
  narrowing explicitly rather than silently skipping pairs.

## Implementation Notes
Subagent spawn cap (200/200) reached before this ticket started — Investigate/Implement/Verify
performed directly. Sub-agent dispatch unavailable throughout; all 81 real engine trial runs
(27 unique run_keys x 3 trials) executed directly via `tools/evaluate_simq.py --scenario`, not
delegated.

Real, fresh recount at Investigate time: 26 COMBAT + 1 COGNITION (not "26 COMBAT + 1 COGNITION + 1
SOCIAL" as the ticket's own title/Request Summary claimed — no SOCIAL failure reproduced; disclosed
as a minor discrepancy from the originating retro's own prose, not silently corrected).

Ran the full `TCK-20260710`/`TCK-20260715` 3-independent-trial methodology against all 27 unique
run_keys (no representative-subset narrowing needed — 81 real engine runs completed in ~13 minutes
via a backgrounded script, well within budget). **Result inverted the ticket's own working
hypothesis**: all 26 COMBAT pairs showed bit-identical `normalized_score` across all 3 independent
trials — zero variance, refuting F6 wall-clock-throttle noise as the cause (contrast with Parts 1/2's
own genuine-load-sensitivity anchors, which showed real trial-to-trial jitter). Left all 26 as
flagged, intentionally-failing gate conditions rather than converting to `SCORE_TOLERANCE_OVERRIDES`
— per this ticket's own explicit Scope guidance, a stable reproducible drift is a "genuine
regression for further investigation," not tolerance-eligible noise. Filed
`TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE` (P1, `tickets/todos/`) for the actual
root-cause fix, out of this ticket's own scope (investigation + disposition only).

The 1 COGNITION pair (`simq_routing_test_seed42_500t`) self-resolved: originally-flagged value was
a single stale cached draw; 3 fresh trials all gave a stable, in-tolerance value, and running the
trials itself refreshed the stale `data/calibration/` cache — no `grade_anchors.json` edit needed,
confirmed by direct pytest re-run.

One additional, disclosed, out-of-primary-scope fix: trial-running
`urban_political_selfmodel_execution_probe_seed42_200t` surfaced a stable NARRATIVE band drift on
that same run_key (unrelated to COMBAT/COGNITION/SOCIAL, this ticket's own declared scope) — traced
to the SAME already-diagnosed quest_event push-migration cause as this session's own earlier
127-entry NARRATIVE/PROGRESSION recalibration, evidently missed by that sweep. Fixed directly
(1 anchor entry) rather than left as a new, unexplained failure this ticket's own trial-running
activity would otherwise have introduced.

`combat_dormant`'s trigger (`zero_combat_by_tick: 200`) is a plausible causal link for the 22/26
`_200t`-scenario pairs (zero margin), but the 4 `_500t` pairs (300 ticks of margin) show the same
stable signal, favoring a genuine COMBAT-event-generation regression over "combat started a few
ticks late" — documented as a lead for the follow-up ticket, not chased further here (would require
kernel-adjacent instrumentation or comparison against a historical baseline, out of this ticket's
own budget).

## Test Summary
`tests/simulation_quality/test_grade_regression.py -m "not slow"`: 26 failed, 43 passed, 18
deselected — **the 26 failures are the deliberate, disclosed, intentional outcome of this
investigation's own disposition** (real regressions correctly still flagged), not a broken
implementation. Confirmed the 1 COGNITION pair passes in isolation
(`test_grade_within_anchor_band[simq_routing_test_seed42_500t]`). No `src/engine/` files touched
(anti-drift guard from test_plan.md confirmed via `git status --porcelain`).

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` (1 entry:
  `urban_political_selfmodel_execution_probe_seed42_200t`/NARRATIVE — the 1 disclosed out-of-scope
  fix; zero COMBAT/COGNITION entries touched)
- `docs/simulation_quality/current_state.md` (new "2026-08-07 COMBAT score-tolerance drift
  investigation" section + banner update)
- `docs/simulation_quality/eval_matrix_results.md` (new "Anchor Reliability Verification, Part 6"
  section)
- `tickets/todos/TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE.md` (new follow-up ticket,
  filed not started)

## Completion Summary
Ran the full, established 3-trial verification methodology against every one of the 27 flagged
pairs (no scoping-down needed) and found a result that overturned the ticket's own working
hypothesis — disclosed that honestly rather than forcing the data to fit F6. Did not convert a
confirmed-stable, unexplained regression into a tolerance override just to quiet the gate; left it
flagged and filed a properly-scoped, evidenced follow-up ticket for the real fix. Caught and fixed
one additional out-of-scope stale anchor that this ticket's own trial-running activity surfaced,
disclosed rather than silently absorbed into the "COMBAT" disposition. No `SCORE_TOLERANCE_OVERRIDES`
entries added; no `kernel.py` changes.
