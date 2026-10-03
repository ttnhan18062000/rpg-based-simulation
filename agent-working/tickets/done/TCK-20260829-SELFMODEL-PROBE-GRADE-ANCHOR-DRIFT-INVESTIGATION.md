---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION
phase: done
date: 2026-08-29
tags: [simulation-quality, information, social, grade-thresholds, calibration, feature-flags]
---

# TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION

## Title
Investigate INFORMATION/SOCIAL Grade-Anchor Drift on urban_political_selfmodel*_probe Run Keys

## Status
DONE

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
Implemented Steps 1 and 2 of `staging_artifacts/.../plan.md` exactly as written (Step 3, the
`docs/architecture/rollout_flag_decisions_m1.md` update, is handled separately by the
Document-Update phase and was not touched here). The coordinator's Option A decision (recorded at
the bottom of plan.md's Unresolved Questions section) was followed: `SOCIAL`'s anchor was left
completely unchanged for both `urban_political_selfmodel_probe_seed42_200t` and
`urban_political_selfmodel_execution_probe_seed42_200t`.

**Step 1** — In `tests/simulation_quality/fixtures/grade_anchors.json`, changed only the
`urban_political_selfmodel_probe_seed42_200t` entry's `INFORMATION` sub-block from
`{"grade": "C", "score": 0.0}` to `{"grade": "B", "score": 0.2}` via a surgical `Edit` (not a
full-file rewrite), anchored on the unique preceding `SOCIAL: 17.895` context so only this one
sub-block changed (confirmed via `git diff` — a 4-line diff). The file has no `event_count` key in
its schema (grade/score only), so the "event_count: 1" language in the ticket/plan refers to the
calibration report's observed value, documented in the test docstring, not a new fixture field.
Confirmed the file still parses (`python3 -c "import json; json.load(...)"` → success) and that no
other run key was perturbed by running the full `test_grade_within_anchor_band`/
`test_grade_within_score_tolerance` FAST_ANCHOR_KEYS sweep (60 passed; the only failure was the
pre-existing, separately-ticketed `highland_traverse_seed42_200t` SOCIAL drift, unrelated to this
edit).

**Step 2** — In `tests/simulation_quality/test_grade_regression.py`,
`test_urban_political_selfmodel_cognition_isolated_grade_anchor` (lines ~424-463): removed the two
hard-coded structural asserts (`pillars["INFORMATION"]["grade"] == "C"` and
`pillars["INFORMATION"]["event_count"] == 0, ...`) that previously raised before the shared
`band_failures`/`score_failures` loop ever ran. Left `assert pillars["COGNITION"]["grade"] == "S"`
in place, unchanged, per the plan. Updated the docstring to remove the now-incorrect "INFORMATION
anchors at C" claim and replace it with an accurate note that `SelfModelUpdatePhase`'s own
Knowledge Assimilation step (`self_model_phase.py:103-141`) fires independently of
`ENABLE_BELIEF_ASSIMILATION`, and that this run key now anchors `INFORMATION` at `B/0.2`
(`event_count=1`) per this ticket's re-anchor. Did not touch
`test_urban_political_selfmodel_execution_isolated_grade_anchor` or any of the shared helper
functions (`_load_calibration_report`, `_extract_pillar_grades`, `_extract_pillar_scores`,
`_within_band`, `_format_score_failures`) — none needed changes.

**Fresh test run confirms the intended outcome.** Re-running
`test_urban_political_selfmodel_cognition_isolated_grade_anchor` after both steps: `INFORMATION`
and `COGNITION` no longer appear in `band_failures`/`score_failures` (the INFORMATION mismatch is
fully resolved). The test still fails, but now on `score_failures` only, and the failure list
includes `SOCIAL: actual_score=12.625 outside tolerance of anchor_score=17.895` alongside three
pre-existing, already-classified `[known tick_budget ceiling]` entries (COMBAT/ECONOMY/PROGRESSION)
that are unrelated to this ticket. This exactly matches investigation.md's fresh numbers
(`SOCIAL=12.625` vs `anchor=17.895`) and is the correct, intended, disclosed outcome per the
coordinator's Option A decision — SOCIAL was deliberately left un-re-anchored so its real,
pre-existing drift (root-caused to `CooperationPhase`'s retry-without-cooldown gap, tracked
separately by `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`) is now visible in pytest
output instead of masked by the removed hard-coded `INFORMATION` assert. This is not a new bug
introduced by this ticket — it is the unmasking this ticket's Step 2 was designed to produce.

No `src/` files were touched; no runtime/simulation behavior changed. Step 3 (doc update to
`docs/architecture/rollout_flag_decisions_m1.md`) remains for the separate Document-Update phase.

## Test Summary
- `pytest tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor -v`
  — `test_urban_political_selfmodel_cognition_isolated_grade_anchor` fails on `SOCIAL` score
  tolerance only (expected/intended per Option A — INFORMATION and COGNITION no longer implicated).
  `test_urban_political_selfmodel_execution_isolated_grade_anchor` fails on pre-existing
  `[known tick_budget ceiling]` COMBAT/ECONOMY/PROGRESSION entries only (unaffected by this ticket's
  changes, SOCIAL/INFORMATION both within tolerance on this run key already).
- `pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band or test_grade_within_score_tolerance"`
  — 60 passed, 1 failed (`highland_traverse_seed42_200t`, pre-existing SOCIAL drift tracked by
  `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`, unrelated to and unperturbed by this
  ticket's `grade_anchors.json` edit), 18 skipped (long-run keys, calibration reports not present),
  10 deselected. Confirms the Step 1 hand-edit did not perturb any other run key.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` — re-anchored `INFORMATION` for
  `urban_political_selfmodel_probe_seed42_200t` from `C/0.0` to `B/0.2`.
- `tests/simulation_quality/test_grade_regression.py` — removed the two hard-coded `INFORMATION`
  structural asserts and updated the docstring in
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor`.
- `docs/architecture/rollout_flag_decisions_m1.md` — Document-Update phase: rewrote the "Honest
  gap" section under `ENABLE_SELF_MODEL_COGNITION — Validation Trial Result` to record that
  `INFORMATION`'s drift was traced (via `git log`/`git blame` on `self_model_phase.py`) to the
  original anchor's incorrect assumption about `ENABLE_BELIEF_ASSIMILATION` gating — not a later
  regression — and is now resolved/re-anchored; and that `SOCIAL`'s drift was root-caused to
  `CooperationPhase`'s cooperation-offer retry-without-cooldown gap
  (`src/domains/cooperation/phase.py`/`services.py`), the same mechanism tracked for
  `highland_traverse_seed42_200t` by `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`, and
  is deliberately left un-re-anchored pending that fix landing.
- `tickets/inprogress/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION.md` — this
  Implementation Notes/Test Summary/Files Changed/Completion Summary/Status update.
- `staging_artifacts/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION/plan.md` — no
  changes made by this implementer pass (the "RESOLVED — Coordinator Decision" section was already
  present, appended by the coordinator prior to this implementer run); no Deviations section was
  needed since implementation followed Steps 1/2 exactly as written.

## Completion Summary
Steps 1 and 2 of the approved plan were implemented exactly as specified: `INFORMATION` was
re-anchored to `B/0.2` for `urban_political_selfmodel_probe_seed42_200t` in `grade_anchors.json`
(a single surgical sub-block edit, confirmed parseable and non-perturbing to the other ~79 entries),
and `test_urban_political_selfmodel_cognition_isolated_grade_anchor`'s two hard-coded
`INFORMATION` asserts were removed so the shared band/score-tolerance loop is now reachable for
every pillar including `SOCIAL`. Per the coordinator's Option A decision, `SOCIAL`'s anchor was
deliberately left unchanged for both `urban_political_selfmodel*_probe` run keys — the test now
correctly and visibly fails on `SOCIAL`'s pre-existing score-tolerance drift
(`actual=12.625` vs `anchor=17.895`) instead of masking it behind the stale `INFORMATION` assert.
This is a disclosed, intended outcome, not a new bug: `SOCIAL`'s root cause (a `CooperationPhase`
cooperation-offer retry-without-cooldown gap) is already tracked separately by
`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`. Step 3 (the
`docs/architecture/rollout_flag_decisions_m1.md` Honest Gap language update) has since been
completed by the Document-Update phase: the "Honest gap" section under `ENABLE_SELF_MODEL_COGNITION
— Validation Trial Result` now states that `INFORMATION` is resolved/re-anchored (traced to the
original anchor's incorrect `ENABLE_BELIEF_ASSIMILATION` gating assumption, confirmed via `git
log`/`git blame` on `self_model_phase.py` as never having been true, not a later regression), and
that `SOCIAL` remains open — root-caused to `CooperationPhase`'s retry-without-cooldown gap and
deliberately left un-re-anchored pending that fix landing and a post-fix re-measurement. No `src/`
files were touched and no runtime/simulation behavior changed — this ticket only re-anchors a test
fixture value, restructures test asserts, and updates the rollout-decision doc's disclosure
language.

**Gate results (this Finalize pass):** Review APPROVED, Architecture-Verify APPROVED, Test 113/116
passed (3 disclosed pre-existing/accepted failures, none introduced by this ticket), Parity skipped
(no `src/` change, no P0 parity-ledger intersection — the change is test-fixture/doc only), Verify
READY_TO_CLOSE.
