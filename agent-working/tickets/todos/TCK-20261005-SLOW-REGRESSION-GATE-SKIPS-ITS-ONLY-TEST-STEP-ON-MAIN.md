---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN
phase: open
date: 2026-10-05
tags: [testing, investigation]
---

# TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

## Title
In 35 of the last 40 `main` push runs the `Slow regression` job's corpus-diversity step failed or was
cancelled and its **only** test-running step was skipped — so the slow gate has been protecting
nothing, which is how at least three red tests stayed unreported

## Status
OPEN

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
1. Establish **why step 5 fails or is cancelled** on `main`. `rpg-implementer` explicitly did not
   investigate this and it is the root question. Distinguish *failed* from *cancelled* — a cancellation
   is usually a timeout or a concurrency-group eviction and has a different fix from a test failure.
2. Establish why step 6 is **skipped** rather than run: an `if:` condition, a missing `if: always()`,
   step dependency, or job-level `continue-on-error` interacting with step ordering. Name the exact
   mechanism in `.github/workflows/test.yml`.
3. Decide and record whether step 6 **should** run when step 5 fails. It probably should — the two
   steps test unrelated things — but that is a gating-policy decision, so record it rather than
   assume it.
4. Report what step 6 actually does once it runs. It may be red, and that is the point: the honest
   outcome may be "the gate now reports three pre-existing failures", which is information, not a
   regression this ticket caused.
5. Do **not** fix the underlying test failures here. Each has or needs its own ticket. This ticket
   restores the signal.

## Out of Scope
- Fixing `test_bravery_quartile_combat_rate_2x` (closed 2026-10-05, test-file-only fix),
  `test_behavioral_5k_regression`, or the 15 corpus-diversity anchors.
- The slow-regression **determinism** root cause, which is **parked by the owner**. Do not re-raise it.
- Making the job PR-gating. It is push-to-main-only by design and that is a separate policy question.
- Any test threshold or anchor value.

## Acceptance Criteria
- [ ] Step 5's failure/cancellation cause is named, with *failed* distinguished from *cancelled* and
      the evidence cited (run ids, or the step conclusion from the API — note GitHub's log hosts are
      TLS-blocked from this environment, so step-level conclusions via
      `gh api repos/:owner/:repo/actions/jobs/<id>` may be the only available evidence; say so if the
      logs cannot be fetched rather than guessing).
- [ ] The skip mechanism for step 6 is named by `file:line` in `.github/workflows/test.yml`.
- [ ] Step 6 runs on `main` after the change, and its real result is reported **whatever it is**.
- [ ] The gating-policy decision from Scope 3 is recorded with who decided.
- [ ] A follow-up exists for each failure step 6 surfaces that does not already have a ticket.
- [ ] The 40-run measurement is reproduced at the current `main` before and after, so "the gate now
      works" is a measured claim and not an inference from a single green run.

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
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
