---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP
phase: open
date: 2026-07-15
tags: [simulation-quality, calibration, determinism]
---

# TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP

## Title
14 `grade_anchors.json` scenarios drifted beyond score tolerance during
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s Step 7 recalibration sweep, for reasons
unrelated to that ticket's weight-collision fix — likely the same F6 load-sensitive kernel
watchdog/throttle mechanism `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` already
identified and partially guarded, now observed on additional anchors

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While closing out `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s Step 7 (re-anchoring
`tests/simulation_quality/fixtures/grade_anchors.json` after fixing the cross-pillar weight
collision), all 76 anchors were regenerated in one session via
`tools/evaluate_simq.py` (46×200t + 12×500t scenarios run back-to-back, then 12×1000t + 6×2000t
run back-to-back — roughly 20 minutes of sustained sequential engine execution). Kernel
tick-budget warnings (`Tick N exceeded budget: ... Aborting next tick if sustained`) were
observed in this session's very first timing probe run, confirming the environment was under
load during at least part of the sweep.

`pytest tests/simulation_quality/test_grade_regression.py -v` against the regenerated
calibration data produced 61 pillar-level score-tolerance diffs across 76 anchors. 41 of these
diffs (spanning 39 unique anchors, all COGNITION-pillar) were mechanically reconciled and
re-anchored in TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION — each diff's magnitude exactly
matched the expected arithmetic of the corrected pillar-scoped weight substitution (verified
per-event via each anchor's `data/calibration/<run_key>/quality_scores.jsonl`).

The remaining **20 pillar-level diffs across 14 unique anchors do NOT reconcile against that
arithmetic** — they involve pillars the weight-collision fix never touches (SOCIAL, COMBAT,
PROGRESSION, NARRATIVE), or COGNITION/ECONOMY diffs whose reconstructed pre-fix value already
equals the current post-fix value (proving the weight fix caused zero change to that specific
number) or is off by an amount the 7-key substitution cannot explain. Per
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s scope guards, these were left untouched
(not re-anchored, not investigated further) and are carved out to this ticket instead.

**Working hypothesis (not yet confirmed — this ticket's first task):** `docs/audits/D06_longrun_health.md`
§F6 — the same wall-clock-driven kernel watchdog/throttle mechanism
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` traced `urban_political_seed123_500t`'s
COGNITION anomaly to (`src/engine/kernel.py`'s tick-budget watchdog interacting with
`decision_divergence_detected`'s by-design missing dedup gate) — that ticket found this specific
anchor's COGNITION output was bit-identical under both idle and induced 2x/4x-core-load repro
conditions, and added a bit-identical regression guard for it alone
(`test_urban_political_seed123_500t_cognition_bit_identical_under_load`,
`tests/unit/worldassembly/test_corpus_diversity.py`). It explicitly did not sweep other anchors
or other pillars. Given this recalibration ran under exactly the kind of sustained sequential
load F6's mechanism is triggered by, F6 (or a same-class variant affecting other event types
under the same throttle, not just `decision_divergence_detected`) is the most likely explanation
for these 14 anchors' drift — but this has not been confirmed with a controlled idle-vs-load
repro for any of them, unlike the prior ticket's rigor.

## Scope
- For each of the 14 anchors below, reproduce a controlled idle-vs-induced-load repro (same
  method as `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s `repro_sweep.md`: idle
  repeats + escalating core-oversubscription load runs via `tools/calibrate_simq.py`'s internal
  helpers) to determine whether the drifted pillar's output is genuinely load-sensitive
  (F6-class) or reflects some other, unrelated cause (e.g. stale anchor unrelated to any known
  mechanism, or a second undiscovered nondeterminism source).
- If F6-class: apply the same established remedy pattern
  (`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s precedent, reused by
  `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`) — either a bit-identical regression
  guard (if bit-identity holds across load levels) or a tolerance-based multi-trial guard (if it
  does not), per-anchor, and record reliability status in
  `docs/simulation_quality/eval_matrix_results.md`.
- If not F6-class: investigate root cause fresh and file (or fold into this ticket) whatever fix
  or guard is appropriate; do not silently force-fit F6's explanation onto a different cause.
- Anchors/pillars in scope (from the Step 7 scan, `data/calibration/` reports as generated
  2026-07-15 in `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s session — ephemeral,
  regenerate before use):
  - COGNITION (4 diffs, all seed42, likely F6/`decision_divergence_detected`-class per the
    established precedent's exact signature): `simq_routing_test_seed42_500t`,
    `simq_routing_test_seed42_1000t`, `hero_guild_routing_seed42_1000t`,
    `unit_selfmodel_pilot_seed42_1000t`.
  - Non-collision pillars (16 diffs across 10 unique anchors — SOCIAL/COMBAT/PROGRESSION/
    NARRATIVE/ECONOMY; not proven F6-class, needs its own repro since F6's documented mechanism
    is specific to `decision_divergence_detected`): `urban_political_seed42_200t` (SOCIAL),
    `urban_political_seed42_1000t` (SOCIAL), `urban_political_seed123_1000t` (ECONOMY, SOCIAL),
    `frontier_extended_seed42_200t` (NARRATIVE), `frontier_extended_seed123_200t` (COMBAT,
    PROGRESSION, NARRATIVE), `frontier_living_world_seed42_200t` (SOCIAL),
    `frontier_living_world_seed123_200t` (COMBAT, NARRATIVE),
    `urban_political_selfmodel_probe_seed42_200t` (SOCIAL), `frontier_marches_seed42_200t`
    (NARRATIVE), `generated_frontier_3_42_seed123_200t` (COMBAT).

## Out of Scope
- Re-litigating `urban_political_seed123_500t`'s already-closed COGNITION guard
  (`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`) — not reopened, it stays as-is.
- Any change to `src/engine/kernel.py`'s tick-budget watchdog/throttle mechanism itself (F6 is
  documented, intentional engine behavior per `docs/audits/D06_longrun_health.md`,
  `docs/engine/kernel.md`, `docs/engine/performance_contract.md` §7) — same precedent as the
  prior ticket; only per-anchor regression guards may be added, not the mechanism changed.
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s own diff (`src/simulation_quality/weights.py`,
  the 41 already-reconciled COGNITION anchors) — closed, not reopened here.
- Re-tuning any `scoring_weights.yaml` value.

## Acceptance Criteria
- [ ] Each of the 14 anchors' drifted pillar(s) has a controlled idle-vs-load repro result
      recorded (bit-identical or genuinely variable).
- [ ] Each anchor either gets a bit-identical regression guard or a tolerance-based multi-trial
      guard (matching the established pattern), and `grade_anchors.json` is updated only after
      the guard is in place (not as a bare re-anchor without a guard, per the precedent ticket's
      "not left as an unstyled unguarded single-run point comparison" standard).
- [ ] `docs/simulation_quality/eval_matrix_results.md` records reliability status for all 14.
- [ ] `pytest tests/simulation_quality/test_grade_regression.py -v` is fully green after this
      ticket closes (assuming the recalibrated `data/calibration/` reports from this session, or
      freshly regenerated ones, are used).

## Related Tickets
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (in progress at time of filing) — Step 7's
  regression scan surfaced these 14 anchors as unreconciled-against-the-weight-fix; this ticket
  is the named follow-up its plan's Design Decision #3 required.
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (done) — established the F6 root-cause
  finding and remedy pattern this ticket's working hypothesis and Scope directly reuse.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — original precedent for the
  tolerance-based multi-trial guard pattern.

## Related Docs
- `docs/audits/D06_longrun_health.md` §F6 — the documented load-sensitive divergence finding.
- `docs/engine/kernel.md`, `docs/engine/performance_contract.md` §7 — watchdog/throttle
  mechanism F6 attributes the variance to.
- `docs/simulation_quality/eval_matrix_results.md` — reliability-status record to be extended.
- `tests/simulation_quality/fixtures/grade_anchors.json` — the fixture with the 14 pending
  anchors' pillar entries currently left untouched (stale, pre-`TCK-20260714` values).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` — repro
  methodology template to reuse.

## Related Code Areas
- `src/engine/kernel.py` (watchdog/throttle, read-only investigation per Out of Scope).
- `src/observability/event_extractor.py` (`decision_divergence_detected` and any other
  no-dedup-gate event types feeding the drifted non-COGNITION pillars).
- `tools/calibrate_simq.py`, `tools/evaluate_simq.py` — repro harness.

## Assumptions / Open Questions
- Whether the 16 non-COGNITION diffs share F6's exact mechanism (`decision_divergence_detected`
  is COGNITION-specific per the prior ticket's Implementation Notes) or a same-class-but-distinct
  no-dedup-gate event type per affected pillar is unresolved — first investigation task, not
  assumed.
- Whether all 14 anchors are genuinely load-sensitive, or some are simply stale for unrelated
  reasons (e.g. drift from unrelated engine/content changes since the anchor was last
  calibrated, with no load-sensitivity at all) is open — the repro step must distinguish these,
  not assume F6 uniformly.

## Implementation Notes
(Investigation not started — filed as a scoped follow-up from
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`'s Step 7 scan.)

**Additional evidence gathered during that ticket's Test-gate verification (2026-07-15, same
day, independent of this ticket's own future repro work):** the Test phase re-generated
calibration data for all 14 anchors listed above via separate, individual
`tools/evaluate_simq.py --scenario <run_key>` invocations (not the original session's continuous
~20-minute sequential batch sweep), then re-ran `pytest tests/simulation_quality/test_grade_regression.py`
against the fresh data. Result: only **8 of the 14** anchors failed this second time
(`simq_routing_test_seed42_500t`, `simq_routing_test_seed42_1000t`, `hero_guild_routing_seed42_1000t`,
`unit_selfmodel_pilot_seed42_1000t`, `urban_political_seed42_1000t`, `urban_political_seed123_1000t`,
`generated_frontier_3_42_seed123_200t`, `urban_political_selfmodel_probe_seed42_200t`) — the other
**6 passed cleanly** (`urban_political_seed42_200t`, `frontier_extended_seed42_200t`,
`frontier_extended_seed123_200t`, `frontier_living_world_seed42_200t`,
`frontier_living_world_seed123_200t`, `frontier_marches_seed42_200t`). No anchor outside the
original 14 failed in either run. This is independent confirmation that the drift is genuinely
load/timing-sensitive (the same anchor set produces a different pass/fail split depending on
sustained-sequential-load vs. isolated-per-scenario execution) rather than a stable, reproducible
value error — consistent with, and reinforcing, the F6 working hypothesis. Worth noting the split
skews toward the 1000t/500t (longer-running) anchors plus 2 of the 200t anchors, which may narrow
the repro investigation's starting point.

## Test Summary
(Not started.)

## Files Changed
(Not started.)

## Completion Summary
(Not started.)
