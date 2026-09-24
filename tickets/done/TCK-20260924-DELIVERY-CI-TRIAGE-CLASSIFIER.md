---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER
phase: done
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER

## Title
Classify a CI failure into the four categories `CLAUDE.md` already defines, and name the path it
prescribes — advisory, with the agent still filing the ticket

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`CLAUDE.md`'s `### CI Failure Triage` (lines 399–417) defines a decision tree with four outcomes, and
getting the classification wrong is expensive in both directions: a real regression dismissed as flake
ships a defect, and a documented flake "fixed" as a regression edits a test for no reason — which is a
Gate Integrity violation.

The four categories, per `CLAUDE.md` step 3:

1. **A real regression caused by this session's own changes** → file a `hotfix`-tier ticket and run the
   full pipeline.
2. **A documented environment-dependent/flaky category** (per `docs/testing/regression_policy.md`,
   e.g. live-server subprocess tests) → do not code-fix; report as environment noise and let it re-run.
3. **A hardcoded test baseline that this session's own legitimate change caused to drift** → a small
   hotfix ticket updating the baseline with fresh evidence, never a silent edit.
4. **Environment/infrastructure**, including the cases where the diagnosis is *absence* rather than
   failure (`CONFLICTING` PR + `pull_request:`-only trigger → no run is created at all) and the
   Fortiguard TLS block on log hosts.

This classification is currently performed by an agent reading a paragraph and judging. It is
mechanically supportable: the categories have concrete signals — which job and step failed, whether the
failing path is named in `regression_policy.md`, whether the failing file is one this branch touched,
and whether a baseline assertion is involved.

## Scope
1. **The classifier module** under `tools/delivery/`, consuming
   `TCK-20260924-DELIVERY-STATUS-TOOL`'s `FAILING` output (job and step conclusions) rather than
   re-fetching state itself.
2. **Classification into the four categories** above, plus an explicit **`UNCLASSIFIED`** outcome. A
   failure the signals do not clearly place must land in `UNCLASSIFIED`, never be forced into the
   nearest category.
3. **Each classification names the path `CLAUDE.md` prescribes** for it, so the output is actionable:
   for category 1 and 3, "file a hotfix ticket"; for category 2, "do not code-fix, report as
   environment noise"; for category 4, the specific remedy (resolve the conflict / the log host is
   blocked, use step conclusions).
4. **Reads `docs/testing/regression_policy.md`** as the source for category 2 rather than carrying its
   own hardcoded list of known-flaky paths. A second copy of that list would drift.
5. **Changed-file correlation for category 1** — whether the failing test path is in, or imports from,
   a file this branch changed. Treated as a signal, not proof.
6. **Advisory output only.** The agent still files the ticket and still decides.

## Out of Scope
- **Filing the ticket.** Classification is not action. The agent reads the classification and files the
  hotfix through the normal pipeline.
- **Editing any test, assertion, baseline, or gate.** Absolutely excluded. The classifier's entire
  reason for existing is to make the *correct* path obvious; a tool that edited a test to resolve a
  failure would be the Gate Integrity violation it exists to prevent. Not even for category 3, where
  the prescribed path is a ticket with fresh evidence, never a silent edit.
- **Blocking.** Prints and exits zero, always.
- **Re-running or re-triggering a job.** Notably, never in response to an absent run — that pushes into
  the same conflicted state, produces no run again, and destroys the evidence.
- **Fetching PR/run state itself.** It consumes the status tool's output; two fetchers would drift.
- **Fetching log bodies.** Step-level conclusions are the intended input, precisely because they are
  metadata and survive the TLS block. If a log body is genuinely needed, report that instead of
  retrying.
- **Deciding a failure is acceptable.** No category means "ignore"; category 2 means "documented as
  environment-dependent, report it and let it re-run."

## Acceptance Criteria
1. Given a `FAILING` payload whose failing test path is listed as environment-dependent in
   `docs/testing/regression_policy.md`, the classification is category 2 and the output says not to
   code-fix it.
2. Given a failing test in a file this branch changed and not in `regression_policy.md`, the
   classification is category 1 and the output names filing a hotfix ticket.
3. Given a failing assertion recognisable as a hardcoded baseline drift, the classification is
   category 3 and the output requires a ticket with fresh evidence, explicitly not a silent edit.
4. Given an `ABSENT` verdict with a `CONFLICTING` reason, the classification is category 4 and the
   output names resolving the conflict, and states that a re-trigger commit or force-push will not
   help.
5. **Given a failure whose signals are ambiguous, the outcome is `UNCLASSIFIED`** — asserted by a test
   with a deliberately ambiguous fixture. The classifier must not guess; this criterion is the one that
   keeps the tool honest, and a classifier that always produces a confident category is worse than no
   classifier.
6. The category-2 list is read from `docs/testing/regression_policy.md` at runtime, proven by a test
   that alters a fixture policy file and observes the classification change.
7. No test file, baseline, gate, or assertion is modified by any code path — proven by a test asserting
   the working tree is unchanged after classification.
8. Exit code zero for every classification including `UNCLASSIFIED`.
9. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260924-DELIVERY-STATUS-TOOL` — **dependency**; supplies the `FAILING`/`ABSENT` payload
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` — the absent-run category-4 case

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.7, and §4's M5 row
- `CLAUDE.md` `### CI Failure Triage` lines 399–417 — the decision tree being encoded. Do **not** edit
  it here; `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` owns that.
- `docs/testing/regression_policy.md` — the authoritative category-2 source, read at runtime
- `.claude/skills/implement-ticket/SKILL.md` — the Gate Integrity rule this ticket must not violate

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/delivery/` — joins the status tool
- `docs/testing/regression_policy.md` — parsed, not duplicated
- `.github/workflows/test.yml` — the job/step names classification reasons over

## Assumptions / Open Questions
1. **Whether `regression_policy.md` is structured enough to parse reliably.** If it is prose, either a
   small machine-readable block is added to it (a doc change, in scope) or the classifier reports
   category 2 as "possible, see policy" rather than asserting it. Decide on inspection; do not assume a
   parseable shape exists.
2. **How confidently changed-file correlation implies category 1.** A test can fail because of a file
   this branch did *not* touch. The correlation is a signal; the honest output may be "category 1
   likely" with the evidence attached.
3. Whether baseline-drift (category 3) is recognisable generically or only from known patterns such as
   `tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count`. Start from the known
   patterns and report the rest as `UNCLASSIFIED` rather than over-generalising.
4. Whether the parked red "Slow regression" job should be special-cased. It is parked by user decision
   and is not news — at minimum the classifier must not present it as a new finding.

## Implementation Notes
Runs after `TCK-20260924-DELIVERY-STATUS-TOOL`, whose output it consumes.

The `UNCLASSIFIED` outcome is load-bearing and must not be quietly dropped for tidiness. A classifier
that always returns a confident category trains an agent to trust it, and the first confident
misclassification then costs more than the whole tool saves. Prefer saying less.

Note the asymmetry in the two failure directions, because it should shape the default: dismissing a
real regression as flake ships a defect, while mislabelling a flake as a regression wastes a ticket.
When the signals are weak, leaning toward "may be a real regression, investigate" is the cheaper error
— but that is a reason to report uncertainty, not to fabricate a category.

## Test Summary
- `python3 -m pytest tests/tools/test_delivery_ci_triage_classifier.py -v` (repo venv): **16
  passed** — one per Acceptance Criterion (AC1–AC9) plus regression-prone paths (TLS-vs-generic
  `UNKNOWN`, the parked-job note, no-write-side-effect).
- Sanity-checked both parsers against the **real** `docs/testing/regression_policy.md` (16 soft-
  monitor paths extracted) and the **real** `.github/workflows/test.yml` (15 jobs, correct
  `pytest` path extraction per job) before trusting the fixture-only test suite.
- Full regression: `python3 -m pytest tests/tools/ -m "not slow"` — **2994 passed, 25 skipped, 28
  deselected, 1 xfailed**, 0 failed.

## Files Changed
- `tools/delivery/ci_triage_classifier.py` (new) — the classifier module and CLI.
- `tests/tools/test_delivery_ci_triage_classifier.py` (new) — 16 tests.
- `staging_artifacts/TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER/{investigation,plan,test_plan}.md`
  (new).

## Completion Summary
Built `tools/delivery/ci_triage_classifier.py`, classifying a `pr_status.py` `FAILING`/`ABSENT`/
`UNKNOWN` payload into the four `CLAUDE.md`-defined categories plus a load-bearing `UNCLASSIFIED`
outcome, and naming the remedy each category prescribes. Resolved the real constraint that
`pr_status.py`'s payload carries only job/step-level detail, never an individual failing test
path (fetching one would require a log body) — changed-file correlation for category 1 therefore
operates at job granularity, parsing each job's actual `pytest <paths>` invocation from
`.github/workflows/test.yml` rather than guessing, with the coarser basis stated explicitly in the
output rather than implying false precision. Category 2 is read from
`docs/testing/regression_policy.md`'s `## 3. Soft Monitors` table at runtime (backtick-quoted
paths only — a narrow, honest parse of one structured section, not a claim the whole prose
document is machine-readable). Category 3 starts from a single named pattern
(`test_parity_index_baseline.py`) rather than generalizing, per the ticket's own instruction.
Multiple failing jobs that classify differently resolve to `UNCLASSIFIED` overall rather than
picking one job's category — a mixed signal is exactly the ambiguity `UNCLASSIFIED` exists to
protect. The parked "Slow regression" job is flagged `parked: true` with an explicit "not a new
finding" note without suppressing its underlying classification. No test, baseline, gate, or
assertion is ever written by this module — it only reads the payload, the two doc/workflow files,
and `git diff --name-only`.

No known material gap. `data_runs_clean` is expected to FAIL again on this close for the same
pre-existing, not-this-ticket's-own reason as the prior five closes in this batch.
