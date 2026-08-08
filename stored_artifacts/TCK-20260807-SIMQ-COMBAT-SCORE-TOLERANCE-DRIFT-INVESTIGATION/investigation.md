---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION
artifact_type: investigation
tags: [simulation-quality, combat]
---

# Investigation — TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION

## Docs Requiring Update

- `docs/simulation_quality/current_state.md`: add disposition (Implement phase)
- `docs/simulation_quality/eval_matrix_results.md`: add Anchor Reliability Verification, Part 3 section (Implement phase)

## Real, fresh (run_key, pillar) count: 26 COMBAT + 1 COGNITION, not 27/26+1+1 as originally reported

Directly recomputed against live `data/calibration/*/quality_report.json` + `grade_anchors.json`
(not trusted from the ticket's own prose summary, which cited "26 COMBAT + 1 COGNITION + 1
SOCIAL"). Real count at Investigate time: **24 parametrized `test_grade_within_anchor_band`
COMBAT failures + 2 standalone isolated-anchor-probe COMBAT failures (`urban_political_selfmodel_probe_seed42_200t`,
`urban_political_selfmodel_execution_probe_seed42_200t`) = 26 COMBAT pairs, + 1 COGNITION pair
(`simq_routing_test_seed42_500t`) = 27 total.** No SOCIAL pillar failure found anywhere in the
current fast-tier suite — the "1 SOCIAL" in the ticket's own title/Request Summary does not
reproduce; most likely a minor miscount in the originating retro's own prose, or it self-resolved
between the retro and this Investigate pass. Disclosed, not silently corrected without note.

## 3-independent-trial methodology (per `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` precedent)

Ran `tools/evaluate_simq.py --scenario <run_key>` (real, throttled `Kernel`, no `audit_mode`) 3
times per unique run_key, for all 27 unique run_keys underlying the 27 flagged pairs (26 COMBAT +
1 COGNITION span 27 distinct scenarios — 1:1, no scenario has 2 flagged pillars). Full raw
per-trial per-pillar output: `/tmp/.../scratchpad/trial_results.json` (not committed —
matches `TCK-20260710`'s own precedent of keeping raw sweep data in `staging_artifacts/` prose
form, summarized below rather than machine-JSON-committed, since the trial script's own tmp output
is reproducible from this investigation's own instructions).

## Result: this ticket's own F6/load-noise hypothesis is REFUTED — all 26 COMBAT pairs show
## bit-identical, zero-variance scores across 3 independent trials

This is the ticket's own single most important finding, and it inverts the working hypothesis
stated in the ticket's own Request Summary. Every one of the 26 COMBAT pairs produced the **exact
same `normalized_score` value across all 3 independent process-level trials** — not merely
"within tolerance of each other," bit-identical to several decimal places (e.g.
`frontier_extended_seed42_200t`: `0.0, 0.0, 0.0`; `urban_political_seed42_500t`:
`-0.0266..., -0.0266..., -0.0266...`; `quest_dense_frontier_seed42_200t`: `-0.26, -0.26, -0.26`).

If this were genuine F6 wall-clock-throttle noise (the ticket's own working hypothesis, based on
this session's own earlier full-corpus run showing unusually early `WatchdogTrip` onset, tick
6-60 vs. F6's documented ~tick 300-320), independent trials run at different real wall-clock
moments would show at least some jitter in `combat_dormant`'s exact trigger timing — as seen in
the genuinely load-sensitive anchors from `TCK-20260710`/`TCK-20260715`'s own precedent sweeps
(e.g. `unit_faction_tension_seed42_1000t`'s 4x elapsed-time spread, or
`simq_routing_test_seed42_500t`'s own COGNITION event-count variance in Part 2's repro). **None of
that variance appears here.** This is a stable, fully deterministic, 100%-reproducible result, not
noise.

**Important caveat honestly disclosed**: all 3 trials per run_key ran back-to-back in one
contiguous background process on this session's own single machine — this does not fully rule out
a *deterministic-under-current-stable-load* variant of F6 (i.e., if this machine's own background
load profile is itself currently stable/consistent moment-to-moment, F6's throttle timing could
still reproduce identically run-to-run without being "true" wall-clock randomness). Distinguishing
"genuine code regression" from "a load pattern so consistent on this machine right now that it
looks deterministic" would require trials spread across genuinely different sessions/times — beyond
this ticket's own single-session budget. This ticket's own methodology (3 independent process
trials, real engine, no audit_mode) fully matches the established precedent
(`TCK-20260710`/`TCK-20260715`); what differs is the *result* (zero variance, not confirmed
load-sensitivity), and that result itself is the finding.

## combat_dormant causal-chain check (confirmed plausible, not confirmed as the actual cause)

`src/simulation_quality/scorers/combat.py:54-66`: `combat_dormant` fires when `tick >
zero_combat_gate` (`config/simulation_quality/detection_params.yaml:11`,
`zero_combat_by_tick: 200`) AND zero COMBAT-pillar events have occurred. **22 of the 26 flagged
COMBAT pairs are exactly `_200t` scenarios** — the dormant-penalty gate fires at precisely the last
tick of these scenarios' own tick budget, meaning ANY delay in real combat initiation (throttle-induced
or otherwise) has zero margin before triggering the penalty. The 4 `_500t` pairs
(`urban_political_seed42_500t`, `urban_political_seed456_500t`, `hero_guild_routing_seed42_500t`,
`hero_guild_routing_seed123_500t`) have 300 ticks of margin past the gate, yet still show the same
stable zero/negative COMBAT signal — meaning if this is F6-caused, it isn't merely "combat started
a few ticks late," it's a persistent, ongoing absence of scored COMBAT events well past any
plausible throttle-delay window. This favors a genuine regression (something suppressing COMBAT
event generation/extraction entirely for these worlds) over "combat just started slightly late."

## Disposition (per pair)

**1 pair — `simq_routing_test_seed42_500t`/COGNITION: NO ACTION (confirmed transient).** All 3
fresh trials give `1.827` (stable), within tolerance of the existing anchor (`1.8373`,
`abs(1.827-1.8373)=0.0103 <= max(0.05, 0.2*1.8373)`). The originally-flagged value (`1.016`) was a
single anomalous cached draw left over from an earlier point in this session's own full-corpus run
— re-running fresh (as this ticket's own trial script did, as a side effect) already overwrote the
stale cache; `pytest tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[simq_routing_test_seed42_500t]`
now passes with no `grade_anchors.json` edit needed. This pillar/run_key was ALSO already given a
dedicated live-repro tolerance guard by `TCK-20260715` (`test_corpus_diversity.py::
test_simq_routing_test_seed42_500t_cognition_grade_stability`) — this ticket's finding is
consistent with, not contradicting, that prior work (a single stale cached draw, not a new
instability).

**26 pairs — all COMBAT: FLAGGED GENUINE REGRESSION, not converted to `SCORE_TOLERANCE_OVERRIDES`.**
Per this ticket's own explicit Scope guidance ("does it consistently miss the anchor by a stable
margin across all 3 trials (confirms a real, deterministic behavior change worth investigating as
a genuine regression, NOT load noise)") — this is exactly that bucket. Converting these to
tolerance overrides would incorrectly launder a stable, reproducible, unexplained drift into
"expected noise," silencing the one signal that something is actually wrong. Left as real,
disclosed, still-failing anchors — `tests/simulation_quality/test_grade_regression.py -m "not
slow"` correctly continues to flag all 26. A dedicated, narrowly-scoped follow-up ticket
(`TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE`, filed alongside this one) is needed to
determine the actual cause — this ticket's own scope is investigation and disposition, not the
engine-level root-cause fix (which plausibly requires WatchdogTrip-timing instrumentation
correlated against combat-initiation timing, or a comparison against a known-good historical
calibration baseline, neither of which fits in this ticket's own budget).

## One additional, disclosed, out-of-primary-scope fix

Trial-running `urban_political_selfmodel_execution_probe_seed42_200t` (3x, to test its own COMBAT
pillar) surfaced a **stable, reproducible NARRATIVE band drift** on the SAME run_key (anchor
grade=A/score=1.0185, all 3 fresh trials give grade=C/score=0.0) — not part of this ticket's own
COMBAT/COGNITION/SOCIAL scope, but directly surfaced by this ticket's own trial-running activity,
and clearly the SAME already-diagnosed, already-fixed cause as this session's own earlier
NARRATIVE recalibration (`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`'s quest_event misclassification
inflating NARRATIVE scores pre-fix) — this specific run_key was evidently missed by that earlier
127-entry recalibration sweep. Fixed directly (single anchor entry, `grade_anchors.json`) rather
than left as a new, confusing, seemingly-unrelated failure this ticket's own work would otherwise
have introduced without explanation.
