---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT
phase: done
date: 2026-10-05
tags: [testing]
---

# TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT

## Title
Two codebase make-target tests exceed their 60 s budget on the local VM

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
`tests/codebase/test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values` and `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` fail with `TimeoutError: Test execution exceeded the resource time limit` (`tests/conftest.py:90`) on the 6 vCPU / 11 GB VirtualBox guest, under the 2 GB memory cap, identically on clean `main`. CI is green, so they presumably fail only locally. No ticket tracked them; they were being called "known failures", which is how a real regression gets read as noise (testing review of PR #329, 2026-10-05). Find the cause (the `make` target runs ruff, complexipy and the snapshot over all of `src/`; the 60 s budget is a conftest limit) and decide: raise the budget for these two, mark them slow, or make the command cheaper.

Same local-load family, seen once: `tests/codebase/test_edit_ratchet_hook.py::test_stdout_is_exactly_one_json_object` failed in a loaded `tests/codebase` chunk on 2026-10-05 and passed alone (28 passed) and in the next full run; track it here so it is not an untracked known flake.

## Scope
- Measure both tests (and note the edit-ratchet hook flake) locally and in CI (duration), name the dominant cost
- Fix or re-budget with a reason; keep the assertions

## Out of Scope
- Any file under `src/`
- The code-health ratchet itself

## Acceptance Criteria
- [ ] Both tests pass locally under the 2 GB cap or are explicitly classified (slow marker, documented budget)
- [ ] The cause is written in the ticket

## Related Tickets
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING (names the two failures)
- TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET: same conftest mechanism (the default `medium` 60 s SIGALRM budget), different test sets; that fix covers `extra_slow` tests and does not cover these two.

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/codebase/test_codebase_health_baseline.py, tests/codebase/test_codebase_health_snapshot.py, tests/conftest.py

## Assumptions / Open Questions
- Hotfix versus standard: standard, because the cause is unknown (budget, resource cap or a real slowdown)

## Implementation Notes
**Measured 2026-10-06** on the 6 vCPU VM, `--resource-budget off`, sequential, base `origin/main` `7570beb90`, load average about 2.3-3.2 (other sessions running, so not idle). The `ast-grep` and `ruff` tools came from a CI-equivalent `uv sync --locked --no-install-project` (full install, as `tools-a-e` does) in a scratch environment; the shared `.venv` has neither.

| test | duration (budget off) | default budget |
|---|---|---|
| `test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values` | 58.98-59.1 s | at the limit |
| `test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` | 65.2 s | over (TimeoutError) |

**Dominant cost:** `git log --shortstat --pretty=format:...` (the full-history churn walk), measured by wrapping `subprocess.run`: **27.6-28.0 s per call**, about 90% of the work in each code path (`build_report` 30.5 s in-process, of which 28.2 s is that call; the snapshot's in-process run 31.7 s, of which 28.0 s). Each test pays it **twice**: once in-process (`chb.build_report` / `chs.main`) and once through the `make` target. That gives about 59 s and 65 s. Nothing else is close (the other git calls take under 0.1 s). It scales with history length, so the margin shrinks as the repo grows.

**CI:** CI runs these two in `tools-a-e` under the default 60 s budget and is green, on faster CPUs; per-test CI durations were not available (log hosts are TLS-blocked from this environment), so no CI duration is claimed.

**Fix (re-budget, existing mechanism):** `@pytest.mark.resource_budget_large` on both tests, with a comment giving the reason. No new budget tier, no assertion changed. Both tests pass under the default budget with no flag (snapshot 60.02 s, baseline 58.98 s: they now run under the 600 s limit).

**Not done, by scope:** making the churn walk cheaper (`codebase/reports/`, e.g. computing it once or bounding it) is a larger change; recorded as an option for the codebase domain, not filed.

**Edit-ratchet hook flake** (`tests/codebase/test_edit_ratchet_hook.py::test_stdout_is_exactly_one_json_object`): classified only. 3 consecutive runs alone, sequential, load about 2.5: 3 passed, 0.15 s each. It does not reproduce, so it is recorded as a load-dependent flake with no evidence of cause; no quarantine (regression_policy 6.1 requires an expiry check first).

**Tracking of the failing node IDs:** `tests/codebase/test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values` and `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` are tracked by this ticket.

## Test Summary
- Both re-budgeted tests, default budget, no flag: 2 passed (60.02 s and 58.98 s).
- `tests/static`, `tests/tools/test_conftest_resource_budget.py`, `tests/tools/test_ci_workflow_test_coverage.py`, `tests/unit/tools/test_scenario_lane_paths.py`: 130 passed.

## Files Changed
- `tests/codebase/test_codebase_health_baseline.py` (marker, `import pytest`), `tests/codebase/test_codebase_health_snapshot.py` (marker)

## Completion Summary
Cause: a 28 s `git log --shortstat` churn walk, paid twice per test (in-process and via `make`), giving 59 s and 65 s against a 60 s limit. Both tests re-budgeted with `resource_budget_large` and pass under the default budget; assertions unchanged. The edit-ratchet flake did not reproduce in 3 runs (classified, not quarantined). A cheaper churn walk is an option for the codebase domain, not filed.
