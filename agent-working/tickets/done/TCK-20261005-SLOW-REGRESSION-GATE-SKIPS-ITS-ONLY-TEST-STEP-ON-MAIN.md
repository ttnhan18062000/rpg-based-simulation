---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN
phase: done
date: 2026-10-05
tags: [testing, investigation]
---

# TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

## Title
In 35 of the last 40 `main` push runs the `Slow regression` job's corpus-diversity step failed or was
cancelled and its **only** test-running step was skipped — so the slow gate has been protecting
nothing, which is how at least three red tests stayed unreported

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**The measurement is `rpg-implementer`'s**, taken while closing
`TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED` on 2026-10-05 and reported to
`rpg-planner`. Filed separately because it is a CI-gating defect, not a test defect, and it explains
a pattern rather than one failure.

Measured over the last 40 `main` push runs of the `Slow regression` job:

- **35 runs**: step 5 (corpus diversity) **failed or was cancelled**, and step 6 — **the only step
  that runs the bravery differentiation guard and `test_behavioral_5k_regression`** — was
  **SKIPPED**.
- 5 runs have no step data.

So for effectively the whole recent history of `main`, the job reported on step 5 and never executed
the tests step 6 exists to run. **The gate is on paper and off in fact.**

**Why this is P1 rather than CI housekeeping.** It is the common cause behind several independently
discovered "red on `main` with nobody noticing" findings this week:

- `test_bravery_quartile_combat_rate_2x` — red on `main`, no owning ticket, found by three sessions
  independently before anyone filed it (`TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED`).
- `test_behavioral_5k_regression` — a 60 s conftest timeout, hit by **both** implementer lanes and
  assumed pre-existing by each because it fails identically on base.
- 15 `test_corpus_diversity` stability anchors red on untouched `origin/main`
  (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`, INPROGRESS — which diagnosed the family as
  `@slow` and ungated. **This ticket sharpens that**: there *is* a job, it *does* run, and its test
  step is skipped — which is a different and more fixable defect than "no job gates it").

A gate that silently stops executing is worse than an absent one: every session reads its green-or-
absent result as information and it carries none.

## Scope
**Re-scoped 2026-10-06 to the owner's decision** (relayed by `test-architecture-reviewer`: "restore steps 6-7 now"). Original items 1-5 are replaced by:

1. **Step 5's failure cause stays parked** under `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (owner deferral 2026-09-16, reconfirmed 2026-10-05). Not investigated here. Only the failed-versus-cancelled split is recorded (Implementation Notes).
2. **Mechanism, named:** in the `slow` job of `.github/workflows/test.yml`, steps 6 ("Slow tests (includes 5k behavioral regression)") and 7 ("Legacy regression") had no `if:`, so they inherited the default `success()` and were skipped whenever step 5 failed.
3. **Policy (owner decision):** steps 6 and 7 run whether step 5 passes or fails. Both get `if: ${{ !cancelled() }}`, not `always()`, so a cancelled run stays cancelled. The upload step keeps its `if: always()`.
4. **Make it loud:** a closing step (`if: ${{ !cancelled() }}`) writes one line per test step to `$GITHUB_STEP_SUMMARY`, read from `steps.<id>.outcome`.
5. **Pin it:** `tests/static/test_ci_slow_job_step_gating.py`, mutation-checked.
6. **Measurement after merge:** the first `main` push run's real outcome for steps 6-7 is measured by `test-architecture-reviewer` on the first `main` push run after merge; the record is committed by `test-architecture-implementer` in the next test-architecture batch (it may be red; that is information).

## Out of Scope
- Fixing `test_bravery_quartile_combat_rate_2x` (closed 2026-10-05, test-file-only fix),
  `test_behavioral_5k_regression`, or the 15 corpus-diversity anchors.
- The slow-regression **determinism** root cause, which is **parked by the owner**. Do not re-raise it.
- Making the job PR-gating. It is push-to-main-only by design and that is a separate policy question.
- Any test threshold or anchor value.
- Investigating step 5's failure cause (parked by the owner, see Scope 1).
- The job-level `if:`, `needs:`, the concurrency group, any test, threshold or anchor.

## Acceptance Criteria
- [x] Failed vs cancelled split recorded for step 5 (reviewer's REST jobs API measurement, below); cause not investigated (parked).
- [x] The skip mechanism for steps 6-7 is named (`.github/workflows/test.yml`, `slow` job, steps without `if:`).
- [x] Steps 6 and 7 carry `!cancelled()`; none of steps 5-7 uses `always()` or `continue-on-error`; a summary step reports the three outcomes (pinned by `tests/static/test_ci_slow_job_step_gating.py`; removing step 6's `if:` fails it).
- [x] The gating-policy decision is recorded with who decided: the owner, 2026-10-05, relayed by `test-architecture-reviewer`.
- [ ] Step 6's real result on the first `main` push after merge: **post-merge, measured by `test-architecture-reviewer` on the first `main` push run after merge; the record is committed by `test-architecture-implementer` in the next test-architecture batch**; cannot be known before the merge by construction. Whatever it is, a red result files its own ticket.

## Related Tickets
- `TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED` (closed 2026-10-05) — produced this
  measurement. Its own finding was that the guard hid two failures: the 60 s conftest timeout
  (missing `resource_budget_large`) and a seed-9 run ending with 7 live heroes (`q_size` 1). Bravery
  ratio measured **2.40** over 23 populated seeds against an asserted 1.5, so there was **no
  differentiation regression** — the guard's precondition was failing, exactly as the ticket framed it.
- `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` (INPROGRESS) — **read this first.** Same
  symptom family, different diagnosis; this ticket's measurement should be folded into its
  understanding rather than contradicting it. Its count was 13 of 15 at `e9db40f0a`; Lane B measured
  15 at `405cbd77b`, so the anchors are drifting further.
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` — prior work on this same job; check
  whether it introduced the step structure in question.

- `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN` is a **sibling** of `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`, which owns step 5's anchors; a correction paragraph was added there (2026-10-05).

## Related Docs
- `docs/guides/delivery_process.md` — "CI Failure Triage"
- `docs/testing/test_taxonomy.md` — what `@slow` means and what is expected to gate on it

## Related Stored Artifacts
_(none yet)_

## Related Code Areas
- `.github/workflows/test.yml` — the `Slow regression` job, steps 5 and 6
- `tests/unit/worldassembly/test_corpus_diversity.py` — step 5's subject
- `tests/integration/scenarios/test_entity_differentiation.py`, `tests/regression/test_behavioral_5k.py`
  — step 6's subjects

## Assumptions / Open Questions
- **Routing is genuinely open.** The affected tests are rpg-simulation tests, which is why
  `rpg-planner` filed it; but `.github/workflows/test.yml` is not in either rpg implementer lane's
  surface, and CI-gating policy has previously sat with the agent-working and testing tracks. **Confirm
  the owner before dispatching**, and do not assume it is an rpg lane's to implement just because the
  tests are ours.
- Whether 35-of-40 is stable or a recent regression is unmeasured. If the job used to work, finding
  when it stopped would localise the cause quickly — check whether the structure changed.
- `rpg-implementer` reports 5 of the 40 runs have no step data. Whether that is API pagination, log
  expiry, or runs that never started is unchecked.

## Implementation Notes
**Measurement (test-architecture-reviewer, REST jobs API, 40 `main` push runs of `Tests` up to run 37278526329):** 19 runs failed at step 5, 17 were cancelled at step 5, 1 was in progress, 3 had no step data. In all 36 with step data, steps 6 and 7 were `skipped`. The cancellations come from the workflow-level `concurrency: group: test-${{ github.ref }}, cancel-in-progress: true` (a newer push to `main` evicts the running job): an eviction, not a test result. The nightly `schedule` runs show the same pattern: 14 of the last 15 have step data (2026-09-20 to 2026-10-04); in all 14, step 5 failed or was cancelled and steps 6-7 were skipped. This replaces the original ticket's "35 of 40" figure. Log hosts are TLS-blocked from this environment, so step conclusions via the jobs API are the evidence.

**Change** (`.github/workflows/test.yml`, `slow` job): `id:` on steps 5-7; `if: ${{ !cancelled() }}` on steps 6 and 7 with a comment naming this ticket; a final step `Slow regression step outcomes`, `if: ${{ !cancelled() }}`, writing three lines to `$GITHUB_STEP_SUMMARY`. `tests/static/test_ci_step_summary_reporting.py::_EXPECTED_SLOW_YAML` (a whole-job pin) updated to the new steps. The job-level `if:`, `needs:`, concurrency group and the upload step are untouched. #338's skip-set pin does not include `slow`; `tests/static/test_ci_registry_resync_skip_jobs.py` still passes.

**Rebase note:** built on `origin/main` `7570beb90`, after #329 (`c8c35545`) changed `test.yml`; the `slow` job's step layout was re-read from the new file before editing.

**Folded into the same batch (all hand-relayed from `test-architecture-reviewer`):** hotfix `TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET`; `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT`; the maintenance-4 record paragraphs in `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md` (rows for #324-#349) and `TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC.md` (live observation); and the diagnosis-correction section in `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED.md`. The relayed figures in the record paragraphs are the reviewer's measurements, committed verbatim and not re-measured here.

## Test Summary
- `pytest tests/static tests/tools/test_conftest_resource_budget.py tests/tools/test_ci_workflow_test_coverage.py tests/unit/tools/test_scenario_lane_paths.py`: 130 passed.
- New `tests/static/test_ci_slow_job_step_gating.py`: 6 tests. Mutation check: removing step 6's `if:` makes `test_slow_tests_step_runs_even_when_corpus_diversity_fails` fail; workflow restored afterwards.
- Not verifiable before merge: a live run of the `slow` job (push-to-main only).

## Files Changed
- `.github/workflows/test.yml` (`slow` job)
- `tests/static/test_ci_slow_job_step_gating.py` (new)
- `tests/static/test_ci_step_summary_reporting.py` (expected-YAML pin)
- the record-only edits listed under Implementation Notes

## Completion Summary
Steps 6 (slow tests incl. 5k behavioral regression) and 7 (legacy regression) of the `slow` job now run unless the run is cancelled (`if: ${{ !cancelled() }}`), and a closing step writes the outcome of steps 5-7 to the job summary. Shape pinned by `tests/static/test_ci_slow_job_step_gating.py` (6 tests, mutation-checked) and the updated whole-job pin. Step 5's failure cause was not investigated (parked by the owner). **Known gap stated, not hidden:** the last acceptance criterion, step 6's real result on the first `main` push after merge, cannot be known before the merge; it is measured by `test-architecture-reviewer` on the first `main` push run after merge; the record is committed by `test-architecture-implementer` in the next test-architecture batch, and a red result files its own ticket. The batch also carried the hotfix and sibling tickets, the maintenance-4 record paragraphs and the SIMQ correction listed under Implementation Notes.
