---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW
phase: open
date: 2026-10-09
tags: [testing, regression]
---

# TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW

## Title
A daily scheduled job and an on-demand dispatch run the rpg gate report, advisory, with a rolling issue

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 5 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. Reuse the #464 pattern (a `gate` job that skips a scheduled run when main's head was already reported within 24 h; fail open; pipefail) and the slow suite's rolling issue.

## Scope
1. A new workflow (for example `.github/workflows/rpg-gate-report.yml`): `schedule` once a day at an off-hour minute, plus `workflow_dispatch` with a `ref` input (a batch author runs it on their branch and links the report in the PR).
2. The gate job for scheduled runs only (reuse `tools/test_architecture/slow_regression_gate.py`, parameterised by workflow and suite job name, rather than copy it).
3. A matrix sized from child 3's measured cost (by world, or a shard of (world, seed) pairs); an aggregate job runs child 4's evaluation and writes the step summary.
4. One rolling issue for main's scheduled runs only (dispatch runs on a branch write the step summary and an artifact, never the issue). It records NEW/RESOLVED per metric, as #390 does for tests.
5. Advisory: the workflow is not a required check. The job is red only per child 4's verdict rule.
6. A shape test for the workflow (triggers, gate, permissions, no push/pull_request trigger).

## Out of Scope
- Making it required (principle 8).

## Acceptance Criteria
1. One live scheduled run and one live dispatch run on a branch, with ids recorded in the ticket.
2. The rolling issue was created or updated by the scheduled run, and untouched by the dispatch run.
3. A gate-skip on an unchanged head (live, or unit-tested if main keeps moving for 3 days after merge).
4. Roadmap §4.1/§4.2 updated with the new evidence layer (the epic's AC4).
5. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN; reuses TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN's gate

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/slow-regression.yml` (pattern), `tools/test_architecture/slow_regression_gate.py`, `tools/test_architecture/slow_regression_report.py`

## Assumptions / Open Questions
None.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
