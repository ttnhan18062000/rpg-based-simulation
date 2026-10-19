---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-API-SLO-BUCKET-AT-300-MS-FOR-THE-REQUEST-HISTOGRAM
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-API-SLO-BUCKET-AT-300-MS-FOR-THE-REQUEST-HISTOGRAM

## Title
The request-duration histogram gets a 0.3 s bucket so the API SLO alert measures exactly "p95 <= 300 ms" (issue #622, R2 follow-up).

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Owner decision 2026-10-19 (relayed by lead-planner and platform-planner on issue #622): add a 0.3 s bucket to R2's histogram. Buckets jump from 0.25 to 0.5, and histogram_quantile interpolates linearly across that range, which is too coarse for an alert threshold. One line in src/api/http_metrics.py `_BUCKETS`.

## Scope
- `_BUCKETS` gains 0.3 after 0.25; a test pins the 300 ms edge. No test pinned the old tuple.
- Carries three todo tickets from the planner seat (D80C, D80D, the catalog arena smoke budget), filed as todos only, plus a known-reds entry in tools/test_architecture/slow_known_reds.yaml for the arena smoke ticket.

## Out of Scope
- The SLO alert and runbook (platform), R3 (OTel).

## Acceptance Criteria
- 0.3 is a bucket edge of http_request_duration_seconds; the R2 tests, mypy and the two tools drift tests pass.

## Related Tickets
- TCK-20261018-API-RECORDS-REQUEST-DURATION-BY-ROUTE-TEMPLATE (R2, #654)

## Related Docs
- None.

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- src/api/http_metrics.py, tests/unit/api/test_http_metrics.py

## Assumptions / Open Questions
- Series count per route grows by one bucket line; still bounded.

## Implementation Notes
One-line change as given in issue #622 (comment of 2026-10-19T05:39Z).

## Test Summary
tests/unit/api/test_http_metrics.py (7, one new: the 300 ms edge) and tests/api/test_request_duration_histogram.py pass; tests/tools/test_perf_inventories_committed_in_sync.py and test_generate_registry.py pass; tests/unit/tools/test_slow_regression_report.py 53 passed (lints the new known-reds entry); mypy_gate rc 0.

## Files Changed
src/api/http_metrics.py, tests/unit/api/test_http_metrics.py, three todo tickets, docs/REGISTRY.yaml.

## Completion Summary
0.3 added to _BUCKETS after 0.25 and pinned by a test. Also carries the planner's three todo tickets and a slow_known_reds.yaml entry for the catalog arena smoke tick-3 budget overrun (owner ticket TCK-20261019-CATALOG-ARENA-SMOKE-TICK-3-BUDGET-OVERRUN-AFTER-645; testing-planner reviews that hunk).
