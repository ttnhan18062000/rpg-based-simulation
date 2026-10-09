---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN
phase: open
date: 2026-10-09
tags: [testing]
---

# TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN

## Title
The Slow regression schedule moves off the hour, and a scheduled run skips the suite when main has not changed since a run that already tested it

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision (2026-10-09): keep the 6 h cadence (D2), but (1) move the schedule off the top of the hour and (2) skip the suite on a scheduled slot when main has not changed. testing-planner proposed both.
- (1) The cron `0 3,9,15,21 * * *` fires at the busiest minute of GitHub's scheduler. On 2026-10-08/09 the slots started 1.5 to 5.5 h late, and one was never created.
- (2) This is a private repo, so minutes are billed: about 2 runner-hours per run, and 3 to 4 runs a day. Two consecutive runs on 2026-10-08/09 (37840201957, 37867736198) both tested the same commit `42ce987b6`. The rule must still keep one same-commit rerun per day, because exactly those two runs exposed that the failing set flaps on an unchanged commit (rolling issue #390). Without same-commit reruns, that flapping would go unseen.

## Scope
1. **Off-hour cron (done by testing-planner in this ticket's first PR).** The cron becomes `41 2,8,14,20 * * *`, with the same 6 h period. Updated in the same change: `tests/static/test_ci_slow_workflow_shape.py` (it pins the cron string) and the docstring of `tools/test_architecture/slow_regression_watchdog.py`. The watchdog's 10 h threshold is unchanged.
2. **Skip-when-main-is-unchanged gate (testing-implementer).**
   - A pure decision function in `tools/test_architecture/` (a new module, or an extension of `slow_regression_watchdog.py` if that reads better). Inputs: main's head SHA, the recent Slow regression runs on `main` (id, head SHA, created_at, status, and whether the run *actually tested*; see below), and `now`. Returns `run` or `skip` with a one-line reason.
   - The rule:
     - `run` if no completed run that actually tested main's current head SHA exists;
     - `run` if the newest run that actually tested that SHA was created **24 h or more** ago (one same-commit rerun per day, which keeps flapping visible);
     - otherwise `skip`.
   - "Actually tested" means the slow test job ran. A run whose gate decided `skip` must not count, or the gate would keep counting its own skips as coverage. Decide how to tell them apart (job conclusions from the jobs API, a gate output, or similar) and record the choice in the module docstring.
   - `slow-regression.yml`: a new first job `gate` (ubuntu-latest, short timeout, `actions: read`, `contents: read`) runs the decision **only for `schedule` events**. A `workflow_dispatch` always runs the suite: a human asked for it, or the watchdog already decided. The existing slow job `needs: gate` and runs only when the decision is `run` or the event is `workflow_dispatch`. On `skip`, the step summary states the decision and the reason. The failing-set report, and with it the rolling issue #390, is not touched on a skipped run.
   - `slow_regression_watchdog.py`: before `dispatch`, also apply the gate rule. Do not dispatch when main's head was actually tested less than 24 h ago. Update its docstring. The existing 10 h staleness rule stays, but a gate-skipped scheduled run must still count as "the schedule fired" (it is evidence the slot was not dropped). State that explicitly in the docstring, since it is the subtle part.
3. Unit tests for the decision (head untested; tested 2 h ago; tested 25 h ago; only gate-skipped runs at head; an in-progress run at head; no runs at all) and for the watchdog's new branch. A shape test asserting the `gate` job, the slow job's `needs: gate`, and the `if:` that lets `workflow_dispatch` through.

## Out of Scope
- Changing the 6 h cadence, the watchdog's 10 h threshold, or the known-reds policy.
- Skipping on anything other than "main's head SHA is unchanged" (for example path-based skips; the slow suite covers all of `src/`).
- Required-check changes.

## Acceptance Criteria
1. Scope 1 merged (cron off the hour, the shape test and the docstring agree).
2. The decision function exists with the unit tests in Scope 3, all passing. The rule and the "actually tested" definition are in its docstring.
3. `slow-regression.yml` has the `gate` job. A scheduled run on an unchanged, recently tested head runs only the gate (about one billed minute), writes the reason to the step summary, and leaves issue #390 untouched. A `workflow_dispatch` run always runs the suite.
4. The watchdog does not dispatch when main's head was tested less than 24 h ago, and its unit tests cover that branch.
5. Live evidence, recorded in the ticket with run ids: one scheduled run where the gate decided `run`, and one where it decided `skip` (main unchanged). If no `skip` occurs within 3 days of merge because main kept changing, record that and close on the unit tests.
6. Standard close.

## Related Tickets
- TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG (the watchdog this extends; its AC4 dispatch evidence is still open)
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (owner decisions D1/D2: alert channel and 6 h cadence)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (the parked determinism cause behind the same-commit flapping)

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/guides/delivery_process.md` (CI sections)

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/slow-regression.yml`
- `.github/workflows/slow-regression-watchdog.yml`
- `tools/test_architecture/slow_regression_watchdog.py`
- `tools/test_architecture/slow_regression_report.py` (must not run on a skipped run)
- `tests/static/test_ci_slow_workflow_shape.py`
- `tests/unit/tools/` (watchdog and report tests)

## Assumptions / Open Questions
- testing-planner's retire rule (a known-red entry retires only after 3 consecutive green slow runs on main) counts only runs that actually tested. A gate-skipped run is neither green nor red for that rule.
- A gate job costs about one billed minute per skipped slot, against about 120 minutes for a full run.
- Rolling issue #390's "last seen" stays at the last run that tested. That is intended.

## Implementation Notes
Scope 1 (testing-planner, 2026-10-09): cron `0 3,9,15,21 * * *` -> `41 2,8,14,20 * * *` in `.github/workflows/slow-regression.yml`, plus the pinned string in `tests/static/test_ci_slow_workflow_shape.py` and the watchdog docstring. `pytest tests/static/test_ci_slow_workflow_shape.py tests/unit/tools -k "slow_regression or watchdog or slow_workflow"`: 84 passed.
Scope 2 (testing-implementer, 2026-10-09):
- New `tools/test_architecture/slow_regression_gate.py`: pure `decide(head_sha, runs, now, exclude_run_id)` plus `collect()` (shells out to `gh`) and a CLI (`decide`, `collect`). "Actually tested" = the run is `completed` and its job named `Slow regression` concluded `success` or `failure`; a gate-skipped run has that job `skipped` (run-level conclusion is `success` for both, so it cannot tell them apart), a cancelled run does not count. Recorded in the module docstring. Jobs are fetched only for completed runs at main's head. An in-progress run at head is not a completed test; the caller's own run is excluded by id, and the workflow's non-cancelling concurrency group means no other run is in flight while the gate runs.
- `slow-regression.yml`: new `gate` job (10 min, `actions: read`, `contents: read`, sparse checkout of the gate module). Its decide step runs only for `schedule` events; the job always exists so `needs: gate` never skips the suite for a dispatch. `slow` gets `needs: gate` and `if: !cancelled() && (dispatch || needs.gate.outputs.decision != 'skip')`, so only an explicit `skip` stops the suite (fail open on a gate error). A skipped run has no report step, so issue #390 is untouched.
- `slow_regression_watchdog.py`: `decide(runs, now, head_sha=None)`; after the 10 h rule says dispatch, the gate rule can turn it into skip (head tested under 24 h ago). The docstring states that a gate-skipped scheduled run still counts as "the slot fired" (the 10 h rule reads the newest run of any conclusion) while not counting as coverage. The watchdog workflow now resolves main's head, runs `slow_regression_gate collect`, and passes `--head-sha`.
- Existing shape test that pinned "no `needs`" now pins `needs == "gate"`.

## Test Summary
Scope 2: `pytest tests/unit/tools/test_slow_regression_gate.py tests/unit/tools/test_slow_regression_watchdog.py` 52 passed (the gate: head untested, other commit tested, tested 2 h / 23 h 59 / exactly 24 h / 25 h ago, only gate-skipped runs, a gate-skipped run newer than the tested one, in-progress run at head, own run excluded, other branch, malformed input, per-conclusion `actually_tested`, `collect` job fetching, CLI; the watchdog: stale-but-head-tested skips, tested over a day dispatches, untested head dispatches, gate-skipped newest run counts as the slot firing, no `--head-sha` unchanged, CLI flag). `tests/static/test_ci_slow_workflow_shape.py` plus the gate and watchdog tests: 128 passed. Other readers of the slow workflows (`test_impact_report`, `test_ci_workflow_test_coverage`, `test_ci_split_tools_jobs`, `test_ci_narrow_path_filtered_jobs`, `test_corpus_diversity_ci_isolation`, `test_ci_step_summary_reporting`): 100 passed.
Live check of the collector against the real repo (before merge): the suite job is named `Slow regression` and reports its conclusion; main head 22a1d1853 (untested) -> `run`; head 42ce987b6 (tested by run 37867736198, 4.5 h earlier) -> `skip`. AC5's scheduled-run evidence is open until the merged workflow produces one `run` and one `skip` decision.

## Files Changed
Scope 1: `.github/workflows/slow-regression.yml`, `tests/static/test_ci_slow_workflow_shape.py`, `tools/test_architecture/slow_regression_watchdog.py`, this ticket.
Scope 2: `tools/test_architecture/slow_regression_gate.py` (new), `tools/test_architecture/slow_regression_watchdog.py`, `.github/workflows/slow-regression.yml`, `.github/workflows/slow-regression-watchdog.yml`, `tests/unit/tools/test_slow_regression_gate.py` (new), `tests/unit/tools/test_slow_regression_watchdog.py`, `tests/static/test_ci_slow_workflow_shape.py`, this ticket.

## Completion Summary
(implementer)
