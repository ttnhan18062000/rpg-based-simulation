---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG
phase: open
date: 2026-10-08
tags: [testing]
---

# TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG

## Title
An hourly watchdog starts the Slow regression workflow when GitHub has dropped its scheduled run

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`.github/workflows/slow-regression.yml` runs on the cron `0 3,9,15,21 * * *` (owner decision D2) plus `workflow_dispatch`. GitHub's scheduled triggers are best-effort: on 2026-10-08 the 03:00Z run was never created, and observed runs start 1 to 3.5 h late. No slow run followed 00:46Z for more than 7 h, so the first run carrying #417/#420/#422/#424/#426 was delayed with nobody told. The owner asked (2026-10-08) for a job that keeps the slow run happening without anyone pinging a session. Filed by testing-planner, which now also holds git CI testing (owner assignment, 2026-10-08).

## Scope
1. A new workflow `.github/workflows/slow-regression-watchdog.yml`: `schedule` hourly at an off-minute (for example `23 * * * *`) plus `workflow_dispatch`; job permissions `actions: write` and `contents: read` only; no checkout of the slow suite and no test run in this workflow.
2. The decision as a small pure function in `tools/test_architecture/` (for example `slow_regression_watchdog.py`): given the recent Slow regression runs on `main` (id, event, status, created_at) and `now`, return `dispatch` or `skip` with a one-line reason. The workflow calls it and, on `dispatch`, runs `gh workflow run slow-regression.yml --ref main` with `GITHUB_TOKEN` (GitHub allows `GITHUB_TOKEN` to trigger `workflow_dispatch`).
3. The rule:
   - `skip` if any Slow regression run on `main` is `queued` or `in_progress`;
   - `skip` if the newest run on `main` (any event, any conclusion) was created less than **10 h** ago;
   - otherwise `dispatch`.
   - Why 10 h: the schedule period is 6 h, and observed lateness is up to 3.5 h. A shorter threshold would dispatch while a late scheduled run is still on its way, and that late run would follow and double the cost. 10 h = 6 h + 3.5 h + 0.5 h grace. Record this derivation in the module docstring.
4. The workflow writes the decision and reason to the step summary, so a skipped watchdog run still shows why it skipped.
5. Unit tests under `tests/unit/tools/` for the decision function. They must cover: no runs at all (`dispatch`); newest run 9 h 59 m old (`skip`) and 10 h 1 m old (`dispatch`); a queued run and an in-progress run (`skip`, whatever the age); a `workflow_dispatch` run that counts as the newest run (`skip`); runs on other branches are ignored; malformed or missing timestamps fail loud, not silent `dispatch`.

## Out of Scope
- The D2 cadence itself, the slow suite's content, its known-reds file and its report step (the rolling issue).
- Any alerting beyond the step summary; the existing report step already keeps one rolling issue for result changes.
- A Claude-side or cloud scheduled agent; the in-session hourly check of testing-planner is separate and session-only.
- Retrying a failed slow run; a red run counts as a run.

## Acceptance Criteria
1. The watchdog workflow exists with only the triggers and permissions in Scope 1, and passes the repo's workflow lint, if there is one.
2. The decision function matches Scope 3 and is covered by the Scope 5 tests, which pass.
3. Budget: when the schedule fires as designed, the watchdog dispatches nothing. Shown by the tests (a 6 h gap and a 9.5 h late-slot gap give `skip`). Worst case, one extra run per dropped slot, which replaces the dropped run and does not add to it.
4. Live proof, recorded in the ticket: one watchdog run on `main` that skips with the reason in its summary. Plus, either a real dropped slot that it filled (run ids of the watchdog run and the Slow regression run it dispatched), or a manual `workflow_dispatch` of the watchdog that shows the decision output. Pushing or merging needs the user.
5. `docs/testing/` or the slow workflow's header comment gains one paragraph that names the watchdog, the 10 h rule and why.

## Related Tickets
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (the slow workflow's own reporting path; D2/D3)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (older slow-job failure, BLOCKED; unrelated cause)

## Related Docs
- `.github/workflows/slow-regression.yml` (header comment: D2, D3, concurrency group)
- `docs/plans/test_architecture/roadmap.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/`
- `tools/test_architecture/`
- `tests/unit/tools/`

## Assumptions / Open Questions
- Assumed: `gh` is available on `ubuntu-latest` and `GITHUB_TOKEN` with `actions: write` can dispatch another workflow in the same repo. Check this during implementation; if it does not hold, stop and report rather than adding a PAT.
- The watchdog's own hourly cron can be dropped too; with about 10 chances inside each 10 h window, this is accepted.
- Open (owner): whether the watchdog may also dispatch on non-`main` refs. Default: `main` only.
- Open (testing-planner review): a Slow regression run stuck forever in queued/waiting would make the watchdog skip forever. Possible hardening: treat a non-completed run older than the job timeout (240 min) plus a margin as stale. Left as is for now.

## Implementation Notes
- Decision function `tools/test_architecture/slow_regression_watchdog.py::decide(runs, now)`; input is `gh run list --json databaseId,event,status,createdAt,headBranch`. Any status other than `completed` counts as active (covers waiting/requested too). Exactly 10 h dispatches ("less than 10 h" skips). Timestamps are parsed for every main run first, so bad data fails loud even when an active run would skip.
- Workflow uses a sparse checkout of the two module files only; no suite checkout, no tests. Decision and reason go to the step summary and to `$GITHUB_OUTPUT`.
- AC5: paragraph added to the header comment of `slow-regression.yml`.
- AC4 (live proof) is open: needs the branch merged to main (schedule/dispatch run only from the default branch). Not yet verified that `GITHUB_TOKEN` can dispatch; first live run decides that.

## Test Summary
`tests/unit/tools/test_slow_regression_watchdog.py`: 20 passed (all Scope 5 cases plus exactly-10 h, naive timestamps, CLI).

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
