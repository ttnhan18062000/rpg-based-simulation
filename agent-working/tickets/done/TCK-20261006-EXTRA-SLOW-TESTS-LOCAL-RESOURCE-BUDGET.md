---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET
phase: done
date: 2026-10-06
tags: [testing]
---

# TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET

## Title
`extra_slow` tests without `resource_budget_large` time out at the 60 s default budget when run locally, a false base-red for every session

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/conftest.py::pytest_runtest_setup` applies `--resource-budget` (default `medium`: 60 s via SIGALRM). `large` is 600 s and the `resource_budget_large` marker forces `large`. `tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` and `tests/integration/world/test_long_run_stability.py::test_long_run_stability` are `@pytest.mark.extra_slow` without that marker; `rpg-implementer` measured both at about 60.2 s (a `TimeoutError`) on its branch and on a clean `origin/main`. Every session that runs them locally without `--resource-budget large` sees a false base-red. CI's `slow` job step 6 already passes `--resource-budget large`, so on CI they are not at the 60 s limit. Brief and measurements from `test-architecture-reviewer` (verified on `origin/main` `054b49146`).

## Scope
- Audit which `extra_slow` tests lack `resource_budget_large` (below).
- **Fix chosen:** in `pytest_runtest_setup`, treat `extra_slow` like `resource_budget_large` (one choke point) instead of adding the marker to each test. Reason: `extra_slow` is defined as ">60s" in `pyproject.toml`, so a 60 s budget contradicts the marker's own meaning; the audit found 10 unmarked tests across 7 files, and a per-test marker would need to be remembered for every future `extra_slow` test; CI already runs them at `large`, so this aligns local runs with CI. `--resource-budget off` still wins.
- Update the `extra_slow` marker description in `pyproject.toml`.
- Test both outcomes in `tests/tools/test_conftest_resource_budget.py`.

## Out of Scope
- Whether these tests pass at 600 s. The first `main` run of `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN` answers that for step 6.
- The two `make`-target tests in `tests/codebase`: they are not `extra_slow`, so this fix does not cover them; they are `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT`.

## Acceptance Criteria
- [x] An `extra_slow` item gets 600 s under the default budget (test added; fails on the unfixed conftest).
- [x] An unmarked item still gets 60 s; `--resource-budget off` still disables enforcement.
- [x] Audit recorded in the ticket.

## Related Tickets
- `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT`: same conftest mechanism (the default `medium` 60 s SIGALRM budget), different test sets.
- `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN`: same batch; its first `main` run shows whether step 6 passes at 600 s.
- `TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED` (closed): found the 60 s timeout on `test_behavioral_5k_regression`.

## Related Docs
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/conftest.py` (`pytest_runtest_setup`), `tests/tools/test_conftest_resource_budget.py`, `pyproject.toml` (marker text)

## Assumptions / Open Questions
- Hotfix: the intent is self-evident (the marker already says ">60s") and the change is one condition plus tests.
- Not in scope: the CI skips of `tests/integration/world/test_long_run_stability.py::test_long_run_stability` and `tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity` (both `skipif(CI == "true")`, citing the mid-tick emergency throttle at `src/engine/kernel.py` ~618-626, which drops work by wall clock outside `audit_mode`). The owner adopted perf's plan to make that throttle report-only (PR #355, plan only; the slice is PERF-M1-T03b plus a throttle ticket perf is filing). Trigger: when that slice merges to `main`, test-architecture re-evaluates both skips. Removing them needs the governor's remaining host-dependence (perf's open "input 1") ruled out as a source of CI flakiness, measured on CI rather than assumed. With this ticket's marker, `test_long_run_stability` would then run in CI at the 600 s budget for the first time.

## Implementation Notes
Audit (`pytest --collect-only -m extra_slow tests` with a collection hook, 2026-10-06, base `7570beb90`): 13 `extra_slow` tests; 3 already carry `resource_budget_large` (`test_bravery_quartile_combat_rate_2x`, `test_perf_metropolis_longevity`, `test_perf_metropolis_stress`); **10 do not**: `tests/arena/test_arena_quests.py::test_arena_quest_progression`, `tests/arena/test_arena_regional_control.py::test_arena_conquest_and_debuff` and `::test_arena_regional_control`, `tests/arena/test_arena_stress.py::test_arena_stress_50v50`, `tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity`, `::test_long_run_pure_stability`, `::test_long_run_runtime_stability` (all three `skipif`), `tests/integration/kernel/test_long_run_determinism.py::test_1000_tick_determinism`, `tests/integration/world/test_long_run_stability.py::test_long_run_stability` (`skipif`), `tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression`. The reviewer's "11 files use `extra_slow`, 10 reference `resource_budget_large`" counts file mentions including static tests that only name the markers; the per-test audit above is the real set. No `skipif` was removed.

## Test Summary
- `pytest tests/tools/test_conftest_resource_budget.py`: 6 passed (3 new). The `extra_slow` test fails on the unfixed `tests/conftest.py` (checked by reverting the fix).

## Files Changed
- `tests/conftest.py`, `tests/tools/test_conftest_resource_budget.py`, `pyproject.toml`

## Completion Summary
`pytest_runtest_setup` now gives `extra_slow` items the `large` budget (600 s) under the default, like `resource_budget_large`; `--resource-budget off` still wins and ordinary tests keep 60 s. Audit: 10 of 13 `extra_slow` tests lacked the marker. Both outcomes tested; the new test fails on the unfixed conftest. No `skipif` removed.
