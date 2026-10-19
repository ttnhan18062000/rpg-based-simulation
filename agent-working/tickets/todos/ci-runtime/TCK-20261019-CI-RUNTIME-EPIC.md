---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-RUNTIME-EPIC
phase: open
date: 2026-10-19
tags: [testing, workflows, performance, planning]
---

# TCK-20261019-CI-RUNTIME-EPIC

## Title
CI runtime: shorten the PR wait in test.yml, warn on job-runtime growth, and stop spending main-push runs on informational work, without losing the post-merge safety net.

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The user asked on 2026-10-19 whether the effective CI runtime, counting parallel and concurrent jobs, is large and should be optimized. testing-planner measured 7 days of every workflow. The method and the numbers are in `agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/investigation.md`.

Findings:
- 228 runner-hours a week, of which `test.yml` is 189 h.
- The median PR wall time is 9.5 min. It was 6.3-8.0 min in W36-W41 and 9.2 min in W42, about 30% growth.
- The critical path runs through Integration (8.4 min), Tools f–z (6.7 min) and API/CLI/engine (6.3 min). None of them uses pytest-xdist.
- Main-push re-runs cost about 58 h a week. The informational SimQ drift job adds about 10 min to every main push.
- Money and queueing are not the problem today. The repo is public, and the median job queue time is 2 s.

The user asked for this to be proposed to lead-planner. lead-planner-u24 agreed with its placement (testing owns test.yml) and its priority (a shorter wait mostly helps RPG PRs), and gave five sequencing points, all folded in below. The user then dispatched the epic. The user also asked that **lead-planner review the deliveries**. Every child PR therefore carries a lead-planner-u24 review by comment, alongside testing-planner's review, before the user merges. Ticket 3 is also reviewed by lead-planner (ubuntu).

## Scope
Three children, in `SEQUENCE.md` order:
1. TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS: pytest-xdist inside the existing slow jobs, after a shared-state audit. No net new jobs.
2. TCK-20261019-CI-JOB-RUNTIME-BUDGET-WARN-ONLY: a warn-only job-runtime budget, with its baseline taken after child 1 and after the Ubuntu 26 runner shift.
3. TCK-20261019-CI-MAIN-PUSH-RERUN-TRIM: drop only the informational and wasted work on main pushes. The full suite stays on every main push unless the owner rules otherwise.

## Out of Scope
- The slow-regression lane. It is scheduled and nobody waits on it.
- A merge queue, or any reduction of the full post-merge suite on main. These are owner decisions; child 3 can only bring them to the owner.
- Paid or larger runners.
- Other workflows: platform's, agent-working's, and rpg-gate-report.yml.

## Acceptance Criteria
- [ ] AC1: all three children are DONE, or closed with a recorded reason.
- [ ] AC2: the measured median PR wall time for test.yml is at or below 6 min over a 7-day window after child 1. If it isn't, the shortfall and its cause are recorded in the epic.
- [ ] AC3: no CI lane loses coverage. The collected-test counts per job are equal before and after, as shown in child 1, and main still runs the full suite on every push (child 3).
- [ ] AC4: lead-planner-u24 reviewed every child PR by comment, and lead-planner (ubuntu) reviewed child 3. The comment links are recorded here.

## Related Tickets
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (the changed-files gate)
- TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT
- TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
- TCK-20261019-TEST-YML-NODE-24-IN-FRONTEND-AND-JSCPD-LANES

## Related Docs
- docs/plans/codebase_health/ubuntu_26_runner_precheck.md
- docs/guides/delivery_process.md (CI Failure Triage)

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/ (the baseline measurement)

## Related Code Areas
- .github/workflows/test.yml
- tests/conftest.py (resource budget, run-dir handling)
- tools/ci_junit_summary.py

## Assumptions / Open Questions
- Queue position: after V8 AC4/AC5, the Node 24 hotfix and the phase19 OFF-mode check. SIMQ-COMPARE (#649) must merge first; it is approved and awaiting the user's merge.
- Free-plan concurrency: Tests already starts 21 jobs against a 20-job limit. No child may add jobs net (lead-planner-u24, point 2).

## Implementation Notes
Scope-only. Comment links for AC4 go here as the children land.

## Test Summary
n/a (epic)

## Files Changed
n/a (epic)

## Completion Summary
(open)
