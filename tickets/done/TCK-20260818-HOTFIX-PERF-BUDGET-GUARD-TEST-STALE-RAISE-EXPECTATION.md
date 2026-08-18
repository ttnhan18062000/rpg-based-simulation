---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-PERF-BUDGET-GUARD-TEST-STALE-RAISE-EXPECTATION
phase: open
date: 2026-08-18
tags: [testing, bug]
---

# TCK-20260818-HOTFIX-PERF-BUDGET-GUARD-TEST-STALE-RAISE-EXPECTATION

## Title
`test_perf_budget_assert_within_budget_fail` tested `PerfBudget.assert_within_budget`'s
pre-stopgap raise behavior, broken by `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING`
changing that method's default to warn instead of raise

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure: "Unit · infra / observability" job (run 32099850713, commit 3c949d57).
`tests/unit/perf/test_perf_guard.py::test_perf_budget_assert_within_budget_fail` — a meta-test of
the `PerfBudget.assert_within_budget` mechanism itself — asserted `pytest.raises(AssertionError,
match="Performance gate failed")` on a budget breach. `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-
WARNING` (same session) changed that method's default behavior to emit
`PerformanceThresholdWarning` instead of raising (with a `hard=True` opt-in to restore the old
behavior) — that sub-agent's own investigation claimed `PerfBudget.assert_within_budget` had "zero
real callers" in `tests/perf/`, which was true for actual perf measurements, but missed that this
one unit test exercises the mechanism's own raise behavior directly with synthetic data. The
method's own new behavior is correct and intentional; the test was simply never updated to match.

## Scope
Update `test_perf_budget_assert_within_budget_fail` to cover the real, current behavior: default
(`hard=False`) breach emits `PerformanceThresholdWarning` (via `pytest.warns`), and `hard=True`
still raises `AssertionError` as before (via `pytest.raises`) — both paths verified in one test,
matching the mechanism's actual current contract.

## Out of Scope
- Any change to `PerfBudget.assert_within_budget` or `tests/tools/perf_assertions.py` — both
  correct and intentional, this is purely a stale-test-expectation fix.
- Any other file touched by `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING` — confirmed via
  a full local reproduction of this job that no other test in scope broke.

## Acceptance Criteria
- [x] `test_perf_budget_assert_within_budget_fail` passes and covers both the default-warn and
      `hard=True`-raise paths.
- [x] Full `tests/unit/perf/test_perf_guard.py` suite passes (6/6).
- [x] Full "Unit · infra / observability" job command reproduced locally end-to-end: 1875 passed,
      1 skipped, 0 failed.

## Related Tickets
- `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING` (the change that made this test's
  expectation stale)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `tests/unit/perf/test_perf_guard.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Added `from tests.tools.perf_assertions import PerformanceThresholdWarning` and split the single
`pytest.raises` check into a `pytest.warns(PerformanceThresholdWarning, ...)` check against the
default call, followed by a `pytest.raises(AssertionError, ...)` check against the same call with
`hard=True` — both against the same `budget` instance, matching the mechanism's real dual-mode
contract.

## Test Summary
- Pre-fix (real CI): `Failed: DID NOT RAISE <class 'AssertionError'>`.
- Post-fix: `tests/unit/perf/test_perf_guard.py` — 6 passed.
- Full job reproduction: `pytest tests/unit/domains tests/unit/observability
  tests/unit/optimization tests/unit/lab tests/unit/lab_agent tests/unit/api tests/unit/cli
  tests/unit/views tests/unit/diagnostics tests/unit/perf tests/unit/entity tests/unit/entities
  tests/unit/chronicle tests/unit/cognition tests/unit/docs tests/unit/certification
  tests/unit/tools -m "not slow and not extra_slow"` — 1875 passed, 1 skipped, 1 warning, 0
  failed.

## Files Changed
- `tests/unit/perf/test_perf_guard.py`

## Completion Summary
Found via a real CI failure surfaced immediately after the perf-threshold-warning-conversion
ticket landed — a single unit test exercising the changed mechanism's own raise behavior directly
was not updated to match its new, intentional default. Fixed by testing the actual current
contract (both the warn-by-default and `hard=True`-raise paths) instead of only the old one.
Verified against the full job command locally before considering this resolved, per this
session's established discipline of not relying on repeated real CI retries.
