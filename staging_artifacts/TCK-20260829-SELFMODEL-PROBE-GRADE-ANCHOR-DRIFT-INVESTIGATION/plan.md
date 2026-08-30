---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION
artifact_type: plan
tags: [simulation-quality, information, social, grade-thresholds, calibration, feature-flags]
---

# Implementation Plan — TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION

## Summary

This plan implements only the parts of the investigation's findings that are confidently
resolvable now: (1) re-anchoring `INFORMATION` for `urban_political_selfmodel_probe_seed42_200t`
to `B/0.2/event_count=1`, the value the investigation confirmed stable across every measurement
taken (fresh run + the 2026-08-26 trial, byte-identical); (2) restructuring
`test_urban_political_selfmodel_cognition_isolated_grade_anchor`'s hard-coded `INFORMATION`
asserts so they no longer raise before the shared band/score-tolerance loop runs — this loop
already iterates every pillar in `grade_anchors.json` (including `SOCIAL`), so removing the early
hard-coded raise is sufficient to make `SOCIAL`'s existing tolerance failure on this run key
visible in pytest output instead of masked; and (3) updating the "Honest Gap" language in
`docs/architecture/rollout_flag_decisions_m1.md` to state both root causes now on file
(INFORMATION: anchor's original assumption was wrong, not a regression; SOCIAL: a
`CooperationPhase` retry-cooldown gap in a different subsystem, separately ticketed). It does
**not** re-anchor `SOCIAL` for either run key, does not touch `src/domains/cooperation/`, and does
not flip any feature flag — those are out of scope per the ticket and are surfaced as an
Unresolved Question for human decision below, since the investigation could not confidently pick a
single path forward for SOCIAL.

## Steps

### Step 1 — Re-anchor INFORMATION for the cognition_probe run key in grade_anchors.json

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`

**Change:** In the `urban_political_selfmodel_probe_seed42_200t` entry, change the `INFORMATION`
block from `{"grade": "C", "score": 0.0}` to `{"grade": "B", "score": 0.2}` (verified current
values via direct read of the file, entry starts at the `urban_political_selfmodel_probe_seed42_200t`
key; the `INFORMATION` sub-block is currently `"grade": "C", "score": 0.0`). This matches
`investigation.md`'s Root Cause Determination: `SelfModelUpdatePhase.run()`'s Step 1 Knowledge
Assimilation (`self_model_phase.py:103-141`) has never in its git history referenced
`ENABLE_BELIEF_ASSIMILATION` (confirmed via `git log`/`git blame` on that file — 2 total commits,
neither touching lines 100-145 after original authorship) — the original `C/0.0` anchor's
assumption that this step was gated by `ENABLE_BELIEF_ASSIMILATION` was simply wrong from the
start, not a later regression. `B/0.2` is the value both this investigation's fresh run and the
independent 2026-08-26 trial produced, byte-for-byte identical both times — the single most stable
figure in the entire investigation.

Do not touch the `urban_political_selfmodel_execution_probe_seed42_200t` entry's `INFORMATION`
block — it already reads `B/0.2` (confirmed via direct read) and needs no change; investigation
confirms it already matches current behavior.

**Do NOT touch:** Any other pillar block in either of these two run-key entries (`COGNITION`,
`AGENCY`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`, `SOCIAL`, `WORLD`, `NARRATIVE`), and no
other run key anywhere else in this ~80-entry shared file. Run
`python3 -c "import json; json.load(open('tests/simulation_quality/fixtures/grade_anchors.json'))"`
immediately after editing to confirm the file still parses before running any test.

**Verify:** `tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor`
no longer fails on the `INFORMATION`-grade mismatch (its remaining pass/fail status now depends on
Step 2, since the test still contains a hard-coded `INFORMATION` assert until that step lands). Run
the full `FAST_ANCHOR_KEYS`-parametrized `test_grade_within_anchor_band`/`test_grade_within_score_tolerance`
sweep to confirm no other run key's block was accidentally perturbed by the hand edit.

### Step 2 — Restructure the cognition_probe test so SOCIAL's tolerance check is reachable

**Files:** `tests/simulation_quality/test_grade_regression.py`

**Change:** In `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
(`tests/simulation_quality/test_grade_regression.py:424-463`), remove the two hard-coded
structural asserts that currently raise before the shared band/score-tolerance loop runs:
- `assert pillars["INFORMATION"]["grade"] == "C"` (line 446)
- `assert pillars["INFORMATION"]["event_count"] == 0, ...` (lines 447-450)

Both are now factually wrong post-Step-1 (`INFORMATION` is `B`/`event_count=1`, not `C`/`0`) and,
per `investigation.md`'s Anti-Drift Hazards section, the first of the two is what masks `SOCIAL`'s
independent score-tolerance failure on this same run key today — the function currently raises at
line 446 before it ever reaches the generic `band_failures`/`score_failures` loop at lines
452-463. That loop already iterates `anchors.items()` for every pillar the run key has an anchor
for (confirmed by reading lines 455-463: `for pillar, anchor in anchors.items()`), which includes
`SOCIAL` — no new loop logic is needed, only removing the early hard-coded raise that currently
prevents execution from ever reaching it. This mirrors the sibling
`test_urban_political_selfmodel_execution_isolated_grade_anchor` (lines 466-504), which has no
hard-coded per-pillar asserts at all and relies solely on the shared band/score loop — bring the
cognition test's structure in line with it for consistency, per `test_plan.md`'s new test #3
(`test_urban_political_selfmodel_probe_social_score_reachable_by_band_check`).

Leave the `assert pillars["COGNITION"]["grade"] == "S"` hard-coded assert (line 445) in place —
`COGNITION` is unaffected by this investigation (confirmed stable at `S`/`28.05` across every
measurement) and removing it is not required to unmask `SOCIAL`; changing it is out of this
ticket's narrow scope. Note as a residual, not-yet-fixed masking risk (see Anti-Drift Notes) that a
future `COGNITION` drift on this run key would still mask `SOCIAL`/others the same way `INFORMATION`
did — out of scope to generalize further here.

Update the test's docstring (lines 425-435) to remove the now-incorrect claim "INFORMATION
anchors at C (zero belief_*/route_new_query events)" and replace it with a short note that
`INFORMATION` fires independently of `ENABLE_BELIEF_ASSIMILATION` via `SelfModelUpdatePhase`'s own
Knowledge Assimilation step (cite `self_model_phase.py:103-141`), so this run key anchors
`INFORMATION` at `B/0.2/event_count=1` per `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`'s
re-anchor.

**Do NOT touch:** `test_urban_political_selfmodel_execution_isolated_grade_anchor` (lines 466-504)
— it has no hard-coded per-pillar asserts and needs no structural change. Do not touch the
`_load_calibration_report`, `_extract_pillar_grades`, `_extract_pillar_scores`, `_within_band`, or
`_format_score_failures` helper functions used by the shared loop — they are correct as-is per the
investigation (the mechanism works; only the anchors/test structure were stale).

**Verify:** Re-run
`tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor`.
Per `investigation.md`'s own fresh numbers, `SOCIAL` on this run key (`actual=12.625` vs
`anchor=17.895`, `|diff|=5.27 > tolerance=3.579`) is expected to now **fail** the
`score_failures` assert — this is the correct, intended outcome of unmasking it (Acceptance
Criteria bullet 2, "SOCIAL drift has a stated root cause, not just unresolved," is satisfied by
Step 3's doc update, not by this test passing). Confirm the failure message names `SOCIAL`
specifically, proving the check is now reachable, and that it is the *only* failure (i.e.
`INFORMATION`/`COGNITION` no longer appear in `band_failures`/`score_failures`).

### Step 3 — Update the Honest Gap language in rollout_flag_decisions_m1.md

**Files:** `docs/architecture/rollout_flag_decisions_m1.md`

**Change:** In the "ENABLE_SELF_MODEL_COGNITION — Validation Trial Result" section's Honest Gap
paragraph (`docs/architecture/rollout_flag_decisions_m1.md:156-174`, confirmed via direct read),
update the two sentences that currently read as unresolved:

1. The `INFORMATION` sentence (lines 158-166, ending "...the anchor evidently predates whatever
   seeded-content or code-path change now causes it to fire once within this 200-tick window.")
   should be corrected: this is not a code-path change surfacing latent behavior — `git log`/`git
   blame` on `self_model_phase.py` show the Knowledge Assimilation step has never referenced
   `ENABLE_BELIEF_ASSIMILATION` in its history (2 total commits, neither touching this logic after
   original authorship). State plainly that `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`
   confirmed the original anchor's assumption (that this step was gated by
   `ENABLE_BELIEF_ASSIMILATION`) was incorrect from the start, and that `INFORMATION` has been
   re-anchored to `B/0.2/event_count=1` for `urban_political_selfmodel_probe_seed42_200t`
   accordingly (the `_execution_probe` run key's `INFORMATION` anchor was already correct and is
   unchanged).
2. The `SOCIAL` sentence (lines 166-168, "`SOCIAL` also drifted beyond score tolerance on both run
   keys ... not traced further, out of this ticket's scope.") should be corrected to state that
   `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` has now traced `SOCIAL`'s root
   cause to `CooperationPhase`'s cooperation-offer retry-without-cooldown gap
   (`src/domains/cooperation/phase.py`/`services.py`), the same mechanism separately ticketed as
   `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` for `highland_traverse_seed42_200t` and
   now known to also affect both `urban_political_selfmodel*_probe` run keys — **not** related to
   `SelfModelUpdatePhase`/`ENABLE_SELF_MODEL_COGNITION` at all. State that `SOCIAL` has
   deliberately **not** been re-anchored yet (link to the Unresolved Questions section of this
   plan / whatever ticket ultimately decides that path), pending either the cooperation fix landing
   or a deliberate disclosed pre-fix re-anchor decision.

Also update the summary sentence at lines 200-202 ("Separately, the fresh trial's
`INFORMATION`/`SOCIAL` anchor drift (Honest Gap above) is a real, disclosed finding needing its
own follow-up ticket before these two grade anchors can be trusted as regression guards again —
not addressed by this ticket.") to reflect that the follow-up ticket
(`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`) has now run and resolved
`INFORMATION` (re-anchored) while `SOCIAL` remains open pending the cooperation-domain fix.

**Do NOT touch:** Any other section of this file (e.g. `ENABLE_WORLD_EMERGENCE`,
`ENABLE_ADVENTURE_ROUTING`, or other flags' validation sections at lines 176+, 204+) — this file
covers multiple unrelated flag validations; only the `ENABLE_SELF_MODEL_COGNITION` section's
Honest Gap language is in scope. Do not change the "Recommendation: Keep OFF, deferred" line
itself (line 191) — this ticket's Out of Scope explicitly forbids flipping any flag default or
its recommendation.

**Verify:** No automated test covers doc prose; verify by re-reading the edited section for
internal consistency (the paragraph must not still say `SOCIAL` was "not traced further" once
Step 3 lands) and cross-check against `investigation.md`'s Root Cause Determination section to
confirm no claim in the doc update goes beyond what the investigation actually found (e.g. do not
claim SOCIAL is "fixed" — it is only root-caused, per Acceptance Criteria bullet 2's own wording).

## Scope Guards

- Do **not** touch `src/domains/cooperation/phase.py`, `src/domains/cooperation/services.py`, or
  any other file under `src/domains/cooperation/` — the retry-cooldown fix belongs entirely to
  `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`, which is scoped to
  `highland_traverse_seed42_200t` only. This plan may *cite* that mechanism in docs but must not
  implement any part of its fix.
- Do **not** re-anchor `SOCIAL` for `urban_political_selfmodel_probe_seed42_200t` or
  `urban_political_selfmodel_execution_probe_seed42_200t` in `grade_anchors.json` as part of these
  3 steps — see Unresolved Questions below. `SOCIAL`'s current committed anchor values (`S/17.895`
  and `S/16.815` respectively) stay unchanged by this plan.
- Do **not** flip `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`,
  `ENABLE_SOCIAL_COOPERATION`, or any other feature flag's default anywhere (`src/domains/optimization/feature_flags.py`
  or any profile YAML). `tests/unit/config/test_phase10_feature_flags.py` is the guard for this —
  it must show zero diff in default values after this plan's steps.
- Do **not** touch `unit_selfmodel_pilot`'s own calibration or anchors — explicitly out of scope
  per the filing ticket, and the investigation's Blast Radius section confirms it is not currently
  drifted.
- Do **not** touch any `grade_anchors.json` entry other than the single `INFORMATION` sub-block
  named in Step 1.
- Do **not** modify `docs/parity_ledger/strategic_cognition.yaml`'s `INFRA-259` entry or add a new
  `social_narrative.yaml` entry — the investigation confirmed `INFRA-259` is already accurate as-is
  and any `SOCIAL`/cooperation-retry parity ledger addition belongs to
  `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s own scope, not this ticket's.
- Do **not** add the new architecture-guard unit test
  (`test_information_assimilation_independent_of_belief_assimilation_flag`, `test_plan.md` new
  test #1) or the cooperation-domain unit test (new test #2) as part of *this* plan unless a
  follow-up revision explicitly adds a step for it — this plan's 3 steps cover only the
  confidently-resolvable re-anchor/test-masking/doc-update work the investigation and ticket scoped
  as resolvable now. (If the coordinator wants test #1 added in this same ticket, that is a small
  additional step, not a reason to broaden scope elsewhere — flag it back to the planner rather
  than having the implementer decide unilaterally.)

## Dependency Map

- Step 1 and Step 2 are tightly coupled but must run in this order: Step 2's docstring update and
  removal of the `event_count == 0` assert reference the `B/0.2/event_count=1` values Step 1
  writes into `grade_anchors.json` — running Step 2 before Step 1 would leave the test referencing
  anchor values that don't yet exist in the fixture. Step 1 alone (without Step 2) leaves the test
  still failing on the stale hard-coded `INFORMATION == "C"` assert, so Step 1's own "Verify" is
  necessarily partial until Step 2 lands.
- Step 3 (doc update) depends on Step 1 and Step 2 being complete and verified — it documents the
  re-anchor and the now-unmasked `SOCIAL` finding as accomplished facts, not as pending work.
- No step depends on any part of `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s own
  implementation — this plan only *cites* that ticket, it does not wait on it.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "Both currently-failing grade-anchor tests are either passing again (fix applied) or have an updated, evidence-backed anchor value with git-blame-traceable justification ... never silently loosened without evidence" | Step 1 (re-anchor INFORMATION, evidence-backed per investigation.md's Root Cause Determination) + Step 2 (test restructure) | **Partially satisfied only.** `test_urban_political_selfmodel_cognition_isolated_grade_anchor` will still fail after these 3 steps — on `SOCIAL`'s score-tolerance check, which this plan deliberately does not re-anchor (see Unresolved Questions). `test_urban_political_selfmodel_execution_isolated_grade_anchor` is unaffected by this plan (its own currently-observed pass/fail status depends on run-to-run SOCIAL nondeterminism per investigation.md, not on any step here) and is out of this plan's step set entirely. This AC is **not fully met** by this plan alone; full satisfaction requires a follow-up decision per Unresolved Questions. |
| "SOCIAL drift has a stated root cause, not just 'unresolved'" | Step 3 (doc update states the CooperationPhase retry-cooldown root cause) | Manual re-read of `docs/architecture/rollout_flag_decisions_m1.md`'s Honest Gap section per Step 3's Verify — no automated test covers doc prose. **Fully satisfied** by this plan — a root cause is now stated, even though the anchor itself is deliberately not yet changed. |
| "If re-anchored: grade_anchors.json, the relevant parity ledger entry, and docs/testing/regression_policy.md (if this fits an existing drift-documentation pattern) are updated in the same ticket" | Step 1 (grade_anchors.json) | `test_grade_within_anchor_band`/`test_grade_within_score_tolerance` FAST_ANCHOR_KEYS sweep confirms no unrelated entry perturbed. Per `investigation.md`'s Docs Requiring Update / Parity Ledger Overlap sections, no `strategic_cognition.yaml` parity entry needs a status change (INFRA-259 already accurate) and `regression_policy.md` needs no *new* pattern added (§9-10 already covers this drift class) — so this AC's parity-ledger and regression-policy clauses are satisfied by explicitly *not* needing changes, not by an omission. |
| "If fixed as a regression: the fix is consistent with ENABLE_BELIEF_ASSIMILATION's documented gating contract and does not reintroduce the INFRA-267 query-routing issue" | N/A | Not applicable — investigation.md's Root Cause Determination concluded INFORMATION is **not** a regression (the anchor's original assumption was simply wrong), so this AC's "if fixed as a regression" branch does not apply; the "if re-anchored" branch above governs instead. |

## Anti-Drift Notes

- **Do not conflate the two drift mechanisms.** INFORMATION's drift is `SelfModelUpdatePhase`
  firing independent of a flag gate that was never meant to cover it. SOCIAL's drift is a
  completely separate subsystem (`CooperationPhase`) with a completely separate bug (retry
  cooldown). A fix or re-anchor for one says nothing about the other — do not let the doc update in
  Step 3 imply a shared cause.
- **The COGNITION hard-coded assert (line 445) is left in place deliberately, not by oversight.**
  It is not currently masking anything (COGNITION is stable at S/28.05), but it sits in the exact
  same structural position the INFORMATION assert did — a future COGNITION drift on this run key
  would reproduce the same masking hazard for SOCIAL/other pillars this ticket just fixed for
  INFORMATION. This is a known residual gap, explicitly out of this narrow plan's scope; do not
  expand Step 2 to "fix all hard-coded asserts in this file" without a separate ticket scoping that
  decision.
- **After Step 2 lands, `test_urban_political_selfmodel_cognition_isolated_grade_anchor` is
  *expected* to still fail** (on SOCIAL, not INFORMATION) — this is the correct, intended result of
  unmasking a real pre-existing failure, not a regression introduced by this plan. Do not treat this
  test's continued failure after Step 2 as evidence the plan is wrong; treat it as evidence the
  masking fix worked. Report this explicitly at Verify time so it is not mistaken for a new bug.
- **SOCIAL's magnitude is not currently stable** — three same-seed measurements across sessions
  gave 13.35, 13.35, then 13.87 on the execution-probe run key, and the two probe legs (which
  previously matched exactly) now disagree with each other (12.625 vs 13.87). This is plausibly
  connected to the already-known, deliberately-unaddressed Kernel wall-clock mid-tick throttle
  nondeterminism bug (`kernel.py:585-596`, fires when `audit_mode=False` — user has said "let it
  sit," not this ticket's to fix). Any future SOCIAL re-anchor decision must account for this before
  trusting a single fresh draw.
- **`data/calibration/` reports are gitignored/transient** and were regenerated very recently by a
  concurrent session's own corpus re-run (per investigation.md's Report Freshness section) — if the
  implementer re-runs the two target tests and gets numbers that differ from those cited in this
  plan and in investigation.md, do not assume this plan is stale; re-verify against a fresh
  `data/calibration/<run_key>/quality_report.json` read before concluding anything, and note any
  material discrepancy in the Completion Summary rather than silently reconciling it.

## Unresolved Questions

**SOCIAL's re-anchor path for `urban_political_selfmodel_probe_seed42_200t` and
`urban_political_selfmodel_execution_probe_seed42_200t` is not decided by this plan and requires
human input before any implementer touches `SOCIAL`'s anchor values.** The investigation's own
Root Cause Determination is explicit that SOCIAL's classification is genuinely mixed — neither
cleanly "(a) intended coupling, re-anchor" nor "(b) unintended regression, fix and keep anchor" in
the ticket's own binary framing. The root mechanism (CooperationPhase retry-without-cooldown) is
high confidence, but the exact score to re-anchor to is not, given a real nondeterminism risk the
investigation could not rule out (Risks item 1). Three real options exist:

- **Option A — Leave SOCIAL's anchor as-is for both run keys in this ticket.** Do not touch
  `grade_anchors.json`'s SOCIAL blocks at all. Close this ticket having satisfied "SOCIAL drift has
  a stated root cause" (AC bullet 2) via Step 3's doc update naming the CooperationPhase
  retry-cooldown finding. Let `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` (once
  implemented) be the trigger for a future, separately-scoped SOCIAL re-measurement/re-anchor
  ticket if still needed post-fix. `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  stays failing on SOCIAL after this ticket closes — disclosed, not silently left broken.
- **Option B — Re-anchor SOCIAL now for the cognition_probe run key only** (the one currently
  reproducibly outside tolerance: `12.625` vs anchor `17.895`, a 5.27 gap far outside the 3.579
  tolerance band — unlike the execution_probe run key's SOCIAL, which is currently within
  tolerance by a 0.42 margin and would not need a change), using this investigation's single fresh
  draw, with an explicit disclosure note in `grade_anchors.json`'s update commit and in Step 3's doc
  update (matching the `highland_traverse` precedent's "deliberately left/disclosed" language) that
  this anchor may need revision once the cooperation retry-cooldown fix lands. Accepts the
  single-draw nondeterminism risk the investigation flagged in Risks item 1.
- **Option C — Run a proper multi-draw sweep (3+ independent fresh runs) for SOCIAL on both run
  keys before deciding anything**, matching the rigor
  `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` applied to its own SOCIAL/NARRATIVE
  re-baselines (which used exactly this "gather independent fresh evidence before widening/moving
  an anchor" discipline), then re-anchor with that evidence per `SCORE_TOLERANCE_OVERRIDES`'
  existing derivation pattern (module docstring + `abs_floor` entry keyed on `(run_key, "SOCIAL")`,
  per `test_plan.md` new test #5).

**Recommendation: Option A.** Reasoning: (1) the ticket's own Acceptance Criteria only require a
*stated* root cause for SOCIAL, not a re-anchor — Option A satisfies that bullet cleanly via Step
3's doc update without taking on re-anchor risk; (2) the investigation itself explicitly
recommends *against* re-anchoring SOCIAL in this ticket (Root Cause Determination: "do not
re-anchor SOCIAL for either run key in this ticket"), and Option B would directly contradict that
recommendation for the sake of closing one test fully green; (3) the nondeterminism risk in Risks
item 1 is real and unresolved — a single-draw re-anchor (Option B) risks committing another anchor
that drifts again on the next run, which is exactly the kind of "loosened without evidence"
re-anchor the ticket's own AC bullet 1 forbids; (4) Option C is the methodologically cleanest but
costs a multi-draw sweep this ticket's own investigation phase did not budget for, and its result
would likely be moot anyway once `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` lands and
changes SOCIAL's true score regardless. Option A defers the cost to the point where it is actually
needed (post-cooperation-fix) rather than spending it twice. This is a recommendation, not a
decision — the coordinator should confirm before the implementer proceeds, since Option B is a
legitimate, evidence-disclosed alternative if the coordinator weighs "close this test fully green
now" more heavily than this plan does.
