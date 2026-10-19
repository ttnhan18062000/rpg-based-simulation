---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-JOB-RUNTIME-BUDGET-WARN-ONLY
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# TCK-20261019-CI-JOB-RUNTIME-BUDGET-WARN-ONLY

## Title
A committed per-job runtime budget for test.yml, plus a scheduled report that warns, and never fails, when a job's rolling median runs over its budget.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 2 of TCK-20261019-CI-RUNTIME-EPIC. The median PR wall time grew about 30% in three weeks (W36-W41 6.3-8.0 min, W42 9.2 min) and nothing noticed. A budget makes that growth visible.

Per lead-planner-u24 (2026-10-19), it is **warn-only** at first: GitHub runner timings are noisy, and `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19 (rollout to 2026-11-19). **The baseline is taken after that shift and after child 1**, so it doesn't record a speed that is about to change.

## Scope
1. `tools/test_architecture/ci_job_runtime_budget.py`:
   - reads the jobs of the last N completed `test.yml` runs through the GitHub API (`gh api`), and only counts runs that succeeded and were not cancelled;
   - computes each job's median and p90;
   - compares them with a committed budget file;
   - writes a markdown report.
   It never exits non-zero for an over-budget job. It exits non-zero only on its own errors, such as an unreadable budget file or no runs found.
2. `tools/test_architecture/ci_job_runtime_budget.yaml`: per job, `median_budget_min`, `baseline_median_min`, `baseline_window` (dates and run count), `runner_image`, and `set_by` (a ticket). A job with no entry is reported as "unbudgeted", never ignored.
3. Run it on a weekly schedule. Either add a job to an existing scheduled run of test.yml, or use a `workflow_dispatch`/schedule-only workflow that testing owns. Choose whichever adds no PR-time job. The report goes to `$GITHUB_STEP_SUMMARY` and an artifact.
4. **Baseline:** taken once child 1 has merged AND test.yml's jobs report an Ubuntu 26 image, using a 7-day window after both. Budget = baseline median × 1.25, rounded up to 0.5 min. The multiplier is recorded in the yaml and can only change through a ticket.
5. Document the method in investigation.md: the same counting rules as the epic's baseline.

## Out of Scope
- Failing CI on budget. Moving to blocking is a later ticket, after at least 4 weekly reports, and needs lead-planner's and the user's yes.
- Other workflows. The slow-regression lane may be added later.

## Acceptance Criteria
- [ ] AC1: the tool has unit tests built on canned API JSON. They cover: over budget, under budget, an unbudgeted job, cancelled and failed runs excluded, no runs found (a tool error), a malformed budget file (a tool error), and an over-budget job that still exits 0.
- [ ] AC2: the budget yaml records each test.yml job's baseline from a window that starts after child 1's merge and after the Ubuntu 26 image appears. Quote the window and the image name.
- [ ] AC3: the scheduled report has run once on main and its summary shows every job. Quote the run id.
- [ ] AC4: no PR-time job is added.
- [ ] AC5: **lead-planner-u24 reviews the PR by comment**, in addition to testing-planner, before the user merges. Record the link.

## Related Tickets
- TCK-20261019-CI-RUNTIME-EPIC (parent)
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (must merge first)
- TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

## Related Docs
- docs/plans/codebase_health/ubuntu_26_runner_precheck.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/investigation.md (method, first baseline)

## Related Code Areas
- tools/test_architecture/ (new tool and budget yaml)
- .github/workflows/test.yml (schedule side only) or a new testing-owned schedule workflow

## Assumptions / Open Questions
- A new workflow file would need a testing owns-glob in `registries/session_roles.yaml` (agent-working's file). Prefer a scheduled job inside test.yml so no glob is needed.
- The `gh api` token has read access to Actions in the scheduled job (`actions: read` permission).

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
