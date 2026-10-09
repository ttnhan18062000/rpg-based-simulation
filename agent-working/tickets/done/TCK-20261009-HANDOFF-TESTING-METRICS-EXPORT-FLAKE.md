---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-HANDOFF-TESTING-METRICS-EXPORT-FLAKE
phase: done
date: 2026-10-09
tags: [delivery]
---

# TCK-20261009-HANDOFF-TESTING-METRICS-EXPORT-FLAKE

## Title
Hand the order-dependent `test_metrics_endpoint_integration` failure over to testing

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Perf reported a connection refused from `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration` when it runs after `tests/unit/resource` and `tests/unit/observability` in one pytest invocation (repro on `8754f94f2`). `tests/observability/` belongs to testing, so codebase records the facts in the testing handoff and does not touch the test. Owner-approved batch `ci-runner-26-precheck`, brief by codebase-planner 2026-10-09.

## Scope
- Append `## Update 2026-10-09: order-dependent failure in test_metrics_endpoint_integration` to `docs/plans/codebase_health/handoffs/handoff_to_testing.md`
- Re-run the repro once on current main and record the result as seen
- Point testing at the Ubuntu 26.04 precheck doc

## Out of Scope
- Any edit to `tests/**` or `src/**`
- Fixing the flake; the suggested fix is testing's to decide

## Acceptance Criteria
- [x] The handoff update exists in the style of the earlier updates, with the facts, the suggested fix and the pointer to the precheck doc
- [x] The repro was re-run once on current main and the result (pass or fail) is recorded, with stderr or port state if it failed
- [x] `git diff --stat` lists no path under `src/` or `tests/`

## Related Tickets
- TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_testing.md
- docs/plans/codebase_health/ubuntu_26_runner_precheck.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/observability/test_metrics_export.py (read only)

## Assumptions / Open Questions
- CI runs the two suites as separate steps, so CI is not affected today (planner's brief; not re-verified here).

## Implementation Notes
- Repro run from the batch worktree with the main checkout's `.venv`: `pytest tests/unit/resource tests/unit/observability tests/observability/test_metrics_export.py -s -q -x`, 2 GB cgroup cap.

## Test Summary
- Repro on `0c3a5654b`: passed (1267 passed, 2 skipped, 55.85 s); port 8011 free afterwards. Not reproduced, so no cause is recorded.

## Files Changed
- `docs/plans/codebase_health/handoffs/handoff_to_testing.md`

## Completion Summary
Handoff update appended; the failure was not reproduced on `0c3a5654b` (one run, passed, port 8011 free afterwards), so it records the report, the source facts and the suggested fix, with no cause claimed. The update links the Ubuntu 26.04 precheck doc. No `src/` or `tests/` path changed.
