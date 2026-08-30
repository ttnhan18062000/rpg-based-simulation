---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION
phase: open
date: 2026-08-29
tags: [simulation-quality, information, social, grade-thresholds, calibration, feature-flags]
---

# TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION

## Title
Investigate INFORMATION/SOCIAL Grade-Anchor Drift on urban_political_selfmodel*_probe Run Keys

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Filed from `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`'s trial evidence (see
`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`, "Honest
gap" section). That ticket ran 2 fresh corpus trials against `urban_political_selfmodel_probe`
(materialization-only) and `urban_political_selfmodel_execution_probe` (full-stack) and found
both no longer reproduce their committed `grade_anchors.json` values for the `INFORMATION` and
`SOCIAL` pillars, with `un-skipped` `tests/simulation_quality/test_grade_regression.py`
assertions now failing:

```
FAILED test_urban_political_selfmodel_cognition_isolated_grade_anchor
  assert pillars["INFORMATION"]["grade"] == "C"
  AssertionError: assert 'B' == 'C'

FAILED test_urban_political_selfmodel_execution_isolated_grade_anchor
  COMBAT/ECONOMY/PROGRESSION drift carries an existing known tick_budget ceiling classification
  (pre-existing, unrelated) — but SOCIAL: actual_score=13.35 outside tolerance of
  anchor_score=16.815, with lookup_ceiling() returning None for SOCIAL/INFORMATION on both run
  keys (no existing ceiling classification covers this drift).
```

The prior ticket traced the `INFORMATION` drift's proximate cause: both runs' identical
`belief_assimilated`/`belief_updated` event pair (subject `bandit_road_danger`, actor 22, tick 1)
is produced by `SelfModelUpdatePhase.run()`'s own Step 1 ("Knowledge Assimilation",
`self_model_phase.py:103-141`, via `KnowledgeModelService.assimilate()`), which is gated only by
`ENABLE_SELF_MODEL_COGNITION` — **not** by `ENABLE_BELIEF_ASSIMILATION` as the anchor's
`urban_political_selfmodel_probe_seed42_200t` value (`INFORMATION=C/0.0`,
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) apparently assumed at the time it was set. It
fired identically on both legs (reproducible, not run-to-run noise). `SOCIAL`'s drift was not
traced beyond confirming it also lacks a ceiling classification — root cause unknown.

## Scope
- Re-run `test_urban_political_selfmodel_cognition_isolated_grade_anchor` and
  `test_urban_political_selfmodel_execution_isolated_grade_anchor` to confirm the drift is still
  live (do not assume the prior ticket's numbers are still current).
- Trace `SOCIAL`'s drift on the `_execution_probe` run key to a root cause (unlike
  `INFORMATION`, this was left untraced by the filing ticket).
- Determine whether `SelfModelUpdatePhase.run()`'s Step 1 firing independent of
  `ENABLE_BELIEF_ASSIMILATION` is: (a) intended coupling (the flag boundary between
  "self-model cognition" and "belief assimilation" was never meant to gate this specific
  knowledge-assimilation step) — in which case re-anchor `INFORMATION`/`SOCIAL` for both
  `urban_political_selfmodel*_probe` run keys with fresh evidence and update
  `grade_anchors.json`/the parity ledger accordingly; or (b) an unintended regression (the flag
  boundary was meant to gate this step and something changed it) — in which case fix the gating
  and keep the existing anchors.
- Check whether any other `*_probe` or archetype-world run key sharing the same
  `pending_self_model_information_events`-seeded content is similarly affected (i.e. is this
  drift isolated to these 2 run keys or wider).

## Out of Scope
- Flipping `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, or any other feature
  flag's default — that decision belongs to the flag-validation tickets, not this one.
- Re-running the `unit_selfmodel_pilot` world's own calibration — its evidence is out of this
  drift's scope per the filing ticket.

## Acceptance Criteria
- Both currently-failing grade-anchor tests are either passing again (fix applied) or have an
  updated, evidence-backed anchor value with `git blame`-traceable justification for the new
  number (re-anchor applied) — never silently loosened without evidence.
- `SOCIAL` drift has a stated root cause, not just "unresolved."
- If re-anchored: `grade_anchors.json`, the relevant parity ledger entry, and
  `docs/testing/regression_policy.md` (if this fits an existing drift-documentation pattern) are
  updated in the same ticket.
- If fixed as a regression: the fix is consistent with `ENABLE_BELIEF_ASSIMILATION`'s documented
  gating contract and does not reintroduce the `INFRA-267` query-routing issue it previously
  resolved.

## Related Tickets
- TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION (filing ticket, disclosed this finding)
- TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE (set the original `INFORMATION=C/0.0` anchor)
- TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE (INFRA-266, prior real-world trial)
- INFRA-267 (fixed the query-routing issue referenced above)

## Related Docs
- `docs/architecture/rollout_flag_decisions_m1.md` ("ENABLE_SELF_MODEL_COGNITION — Validation
  Trial Result" section)
- `docs/testing/regression_policy.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`

## Related Code Areas
- `src/cognition/self_model_phase.py` (`SelfModelUpdatePhase.run()`, `self_model_phase.py:103-141`)
- `src/domains/optimization/feature_flags.py`
- `tests/simulation_quality/test_grade_regression.py`

## Assumptions / Open Questions
- Whether `KnowledgeModelService.assimilate()`'s firing was always latent (anchor was set before
  some seeded-content or code-path change surfaced it) or is a new regression from recent work —
  not yet determined; first investigative step.

## Implementation Notes
(Not yet implemented — filed and deferred, per session's "verify follow-up tickets, then SimQ" sequencing.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
