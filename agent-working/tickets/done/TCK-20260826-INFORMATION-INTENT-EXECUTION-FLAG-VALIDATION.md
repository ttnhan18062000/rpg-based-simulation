---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
phase: done
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_INFORMATION_INTENT_EXECUTION` before deciding its
default

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_INFORMATION_INTENT_EXECUTION`
was kept `OFF` by default -- real call site
(`src/engine/pipeline_phases/information_intent_execution.py`), 5 test files, but no corpus
profile turns it on and no SHADOW-validation history exists. Note this flag is a distinct system
from `ENABLE_BELIEF_ASSIMILATION` (already flipped ON this same ticket, `DEV-003`) -- both live in
the information/belief domain but gate different phases; do not conflate them when investigating.

## Scope
- Confirm precisely (read, not assume) what `information_intent_execution` actually does
  differently from the now-ON `information_belief`/`ENABLE_BELIEF_ASSIMILATION` phase, since both
  share a domain and the distinction matters for a correct trial design.
- Run a real corpus-profile trial with the flag `ON` against at least one world, now that
  `ENABLE_BELIEF_ASSIMILATION` (a related, same-domain flag) is globally ON -- confirm no
  unexpected interaction between the two.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Re-litigating `ENABLE_BELIEF_ASSIMILATION`'s own already-decided ON default.

## Acceptance Criteria
- [x] The distinction from `ENABLE_BELIEF_ASSIMILATION`/`information_belief` is confirmed and
      documented, not assumed
- [x] A real corpus-profile ON trial is run and documented, with `ENABLE_BELIEF_ASSIMILATION` left
      at its now-ON default (not artificially turned off for the trial)
- [x] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral; also flipped the related
  `ENABLE_BELIEF_ASSIMILATION` ON)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/engine/pipeline_phases/information_intent_execution.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Whether this flag and `ENABLE_BELIEF_ASSIMILATION` were ever meant to ship together as one
  logical unit, or are genuinely independent -- not resolved here.

## Implementation Notes
Executed `staging_artifacts/plan.md`'s 9 steps as a real, no-fabrication evidence-gathering trial —
no `src/` code was touched. Confirmed the venv `pydantic` precedent
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`, pydantic 2.12.5) still holds;
bare `python3` still lacks `pydantic`. Ran the 5 scoped pytest commands as a pre-trial baseline
(Step 1), created the temporary OFF-leg probe profile
`config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml`
(Step 2, verified its `feature_flags:` block has exactly 3 keys and omits
`ENABLE_INFORMATION_INTENT_EXECUTION`), ran the OFF leg (Step 3,
`data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t`,
`run_1788026423_5169`) and the ON leg (Step 4, reusing the existing permanent
`urban_political_selfmodel_execution_probe.yaml` fixture,
`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t`, `run_1788026439_5169`),
tallied the evidence (Step 5: pillar grades/scores/events, 0 `action_intent`/`ActionIntentAdapter`
traces in both legs, ON-leg cross-check against `grade_anchors.json`), re-ran the 5 scoped pytest
commands post-trial (Step 6, identical tallies to Step 1 except the anchor test's own failure
detail — see Deviations), updated `docs/architecture/rollout_flag_decisions_m1.md` (Step 7: table
row + new dedicated section), wrote `trial_evidence.md` (Step 8), and deleted the temporary OFF-leg
profile YAML (Step 9, confirmed via `git status --porcelain` no trace remains).

Deviation from plan.md's own expectation: Step 1's baseline observed
`test_urban_political_selfmodel_execution_isolated_grade_anchor` already `FAIL` (not the expected
`SKIP`) because a `quality_report.json` for this exact run key already existed on disk — leftover
output from the separately-tracked, still-`OPEN`
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` ticket's own prior run (dated
2026-08-29, one day before this ticket's own execution). This ticket's own fresh ON-leg run (Step
4) independently reproduced the identical `SOCIAL`-pillar drift (`actual=13.35` vs
`anchor=16.815`, `lookup_ceiling()` returns `None` for `SOCIAL` — no existing ceiling
classification covers it), confirming the drift is real and deterministic, not stale-data noise.
This ticket's own ON leg does **not** reproduce the drift ticket's `INFORMATION`-pillar half — that
half was only reported on the sibling `urban_political_selfmodel_probe` (materialization-only) run
key, not this `_execution_probe` (full-stack) one, and this trial's `INFORMATION` cross-check is an
exact match with its anchor. Full detail in `trial_evidence.md`'s Honest Gap section and
`plan.md`'s new Deviations section. No fix or re-anchor was attempted — that remains
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`'s own separately-tracked job.

`data/calibration/` output for both legs was left in place (not deleted), matching the actual
precedent set by the SELF-MODEL-COGNITION and WORLD-EMERGENCE sibling tickets (their own
`data/calibration/*` directories remain on disk today, not deleted at their Finalize despite
plan.md's Step 9 template language) and the orchestrator's own explicit instruction to match that
precedent rather than plan.md's literal `rm -rf` text. `data/runs/*`/`reports/release_proof/*`
cleanup was left for Finalize — 3 of 5 directories in this shared worktree's `data/runs/` at
Implement time were not attributable to this ticket's own 2 `calibrate_simq.py` invocations,
consistent with a concurrent session actively writing to the same shared directory.

## Test Summary
Pre-trial baseline (Step 1) and post-trial re-run (Step 6) of the 5 scoped pytest commands produced
identical tallies both times:
- `tests/unit/engine/test_information_intent_execution_phase.py` — 3 passed
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — 5 passed
- `tests/unit/config/test_phase10_feature_flags.py` — 7 passed
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — 67 passed
- `tests/simulation_quality/test_grade_regression.py -k "information_intent_execution or selfmodel_execution"`
  — 1 failed (`test_urban_political_selfmodel_execution_isolated_grade_anchor`, the pre-existing
  `SOCIAL`-pillar anchor drift described above and in `trial_evidence.md`), 1 passed
  (`test_information_intent_execution_fires_through_kernel_tick_once`), 87 deselected.

No test file was edited. No assertion, tolerance, skip condition, or allowlist was modified.

**Formal Test-phase gate (orchestrator-run, post-Implement)**: the corpus-content-drift-sensitive
`test_urban_political_selfmodel_execution_isolated_grade_anchor` is excluded from this ticket's
formal blocking Test-phase gate scope — it fails for a reason wholly independent of this ticket's
own (zero `src/`) diff (the pre-existing, already-filed, still-`OPEN`
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`), matching the same scoping
precedent `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION` established (its own formal Test
Summary excludes any corpus-trial-triggered path; the trial's crash finding lives only in
`trial_evidence.md`). The failure itself is not hidden — it is reported above, in
`trial_evidence.md`'s Honest Gap section, and in `plan.md`'s Deviations section, exactly as found,
with no edit made to the test, its tolerance, or `grade_anchors.json`. Re-run with the corpus-anchor
test excluded:
```
.venv/bin/python3 -m pytest tests/unit/engine/test_information_intent_execution_phase.py \
  tests/integration/domains/information/test_phase5_information_belief_phase.py \
  tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_world_profile_feature_flag_guardrail.py \
  tests/simulation_quality/test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once \
  -q
=> 83 passed
```

## Files Changed
- `docs/architecture/rollout_flag_decisions_m1.md` (table row updated + new
  "ENABLE_INFORMATION_INTENT_EXECUTION — Validation Trial Result" section added)
- `staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/trial_evidence.md` (new)
- `staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/plan.md` (Deviations
  section added)
- `staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/investigation.md`
  (pre-existing, created during this run's own Investigate phase — no further edits by Implement)
- `staging_artifacts/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION/test_plan.md`
  (pre-existing, created during this run's own Plan phase — no further edits by Implement; not
  re-read/re-quoted in this Implementation Notes section beyond what plan.md already carries)
- `tickets/inprogress/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION.md` (this file)
- `config/simulation_quality/profiles/urban_political_information_intent_execution_off_probe.yaml`
  (created as a temporary trial fixture in Step 2, then deleted in Step 9 — does not exist at the
  end of this run; confirmed via `git status --porcelain -- config/simulation_quality/profiles/`
  showing no trace, staged or unstaged)

## Completion Summary
Ran a real, single-variable OFF-vs-ON corpus calibration trial for
`ENABLE_INFORMATION_INTENT_EXECUTION` against `urban_political` (seed 42, 200 ticks), holding
`ENABLE_BELIEF_ASSIMILATION` ON in both legs. Confirmed by direct code read that the flag is
structurally distinct from `ENABLE_BELIEF_ASSIMILATION` (production vs. execution of Branch B's
`ActionIntent`). Found 0 `action_intent`/`ActionIntentAdapter` traces in both legs (Branch B does
not route a query in this corpus/seed/window, matching prior `INFRA-266`/`INFRA-270` findings) and
no suppression regression from wiring the phase into the pipeline gated ON. The ON leg's fresh run
reproduced the already-disclosed, still-open `SOCIAL`-pillar grade-anchor drift tracked by
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` — confirmed as real and
deterministic, not fixed (out of this ticket's own scope). Recommendation: Keep OFF, deferred — no
shipped profile turns this flag on anywhere, the same DEV-003 gap the other 4 originally-deferred
flags share. This is the 5th and final of the 5 flags `TCK-20260824-ROLLOUT-FLAG-DECISIONS`
originally deferred; all 5 now carry real trial evidence on file. No `src/` file was modified —
`behavior_changed` is `false`.
