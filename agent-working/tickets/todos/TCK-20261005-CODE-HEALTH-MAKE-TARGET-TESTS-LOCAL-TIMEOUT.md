---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT
phase: open
date: 2026-10-05
tags: [testing]
---

# TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT

## Title
Two codebase make-target tests exceed their 60 s budget on the local VM

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
`tests/codebase/test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values` and `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` fail with `TimeoutError: Test execution exceeded the resource time limit` (`tests/conftest.py:90`) on the 6 vCPU / 11 GB VirtualBox guest, under the 2 GB memory cap, identically on clean `main`. CI is green, so they presumably fail only locally. No ticket tracked them; they were being called "known failures", which is how a real regression gets read as noise (testing review of PR #329, 2026-10-05). Find the cause (the `make` target runs ruff, complexipy and the snapshot over all of `src/`; the 60 s budget is a conftest limit) and decide: raise the budget for these two, mark them slow, or make the command cheaper.

## Scope
- Measure both tests locally and in CI (duration), name the dominant cost
- Fix or re-budget with a reason; keep the assertions

## Out of Scope
- Any file under `src/`
- The code-health ratchet itself

## Acceptance Criteria
- [ ] Both tests pass locally under the 2 GB cap or are explicitly classified (slow marker, documented budget)
- [ ] The cause is written in the ticket

## Related Tickets
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING (names the two failures)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/codebase/test_codebase_health_baseline.py, tests/codebase/test_codebase_health_snapshot.py, tests/conftest.py

## Assumptions / Open Questions
- Hotfix versus standard: standard, because the cause is unknown (budget, resource cap or a real slowdown)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
