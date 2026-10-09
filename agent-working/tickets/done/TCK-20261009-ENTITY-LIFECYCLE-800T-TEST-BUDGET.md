---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-ENTITY-LIFECYCLE-800T-TEST-BUDGET
phase: done
date: 2026-10-09
tags: [testing]
---

# TCK-20261009-ENTITY-LIFECYCLE-800T-TEST-BUDGET

## Title
The 800-tick entity-lifecycle tool test takes about 48 s under a 60 s default budget and times out locally under host load

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
agent-working-implementer saw
`tests/tools/test_entity_lifecycle_score.py::TestRealIntegration::test_sandbox_world_800t_end_to_end_produces_sane_output`
time out locally. testing-planner routed it here, because `tests/tools/**` is agent-working's suite.

Measured 2026-10-09 by agent-working-planner, with `--resource-budget off` and `--durations=1`, on a 6-core host at load
about 3–4:

| Tree | Call time |
|---|---|
| origin/main `f446a2bc8` | 47.99 s |
| `0b4f12af7` (#454, before #457 and #458) | 50.35 s |

So the simulation did not get slower, and there is nothing to send to rpg. The test has no marker, so
`tests/conftest.py::pytest_runtest_setup` gives it the **medium** budget, a 60 s SIGALRM. That leaves about 12 s of
headroom, which host load easily uses up. The repo already has a marker for this case: `resource_budget_large` forces
the 600 s / 8 GB budget (pyproject marker text: "for tests inherently >60s").

## Scope
1. Add `@pytest.mark.resource_budget_large` to that test.
2. Time the rest of `tests/tools/test_entity_lifecycle_score.py` with `--durations=0 --resource-budget off`. Mark any
   other test that runs a real Kernel and takes more than 30 s the same way. Record each test's duration in the
   Test Summary.

## Out of Scope
- Adding `slow` or `extra_slow`. Those change which CI lane selects the test, and CI composition is testing's.
  `resource_budget_large` changes only the timeout, so lane selection stays the same.
- Shortening the test (fewer ticks) or speeding up the simulation.
- `test_autonomous_loop_determinism_drift_guard` (routed by testing-planner to rpg-planner).

## Acceptance Criteria
- AC1: The 800-tick test carries `resource_budget_large`, and it passes under the default CLI budget (no
  `--resource-budget` flag).
- AC2: The Test Summary lists the measured durations from scope item 2, and every test over 30 s carries the marker.
- AC3: `pytest tests/tools/test_entity_lifecycle_score.py tests/tools/test_conftest_resource_budget.py` passes.
- AC4: `-m "not slow and not extra_slow" --collect-only` selects the same set of tests before and after (no lane change).

## Related Tickets
- TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET (the extra_slow-to-large budget rule)
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (introduced `resource_budget_large`)

## Related Docs
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tests/tools/test_entity_lifecycle_score.py`
- `tests/conftest.py` (`pytest_runtest_setup`, read only)

## Assumptions / Open Questions
- Assumes testing is fine with a budget-only marker in our suite. testing-planner gets an fyi when this closes.
- The `search_docs` index is not built and this worktree has no graphify graph. The duplicate scan was a grep over
  `agent-working/tickets/` for "entity_lifecycle" and "800t"; no duplicate was found.

## Implementation Notes
Added `@pytest.mark.resource_budget_large` to `TestRealIntegration::test_sandbox_world_800t_end_to_end_produces_sane_output` (one line). No `slow`/`extra_slow`, no lane change.

## Test Summary
Durations (`--durations=0 --resource-budget off`, 25 passed in 61.08 s, this host): 800t end-to-end 42.28 s (real Kernel, over 30 s: marked); `test_midrun_spawned_entity_gets_real_metadata` 13.71 s (real Kernel, under 30 s: not marked); `test_run_for_analysis_returns_final_entities` 2.36 s; `test_dedicated_run_driver_reports_dropped_count` 1.68 s; everything else 0.66 s or less. Only the 800t test is over 30 s.
AC1/AC3: `pytest tests/tools/test_entity_lifecycle_score.py tests/tools/test_conftest_resource_budget.py` (no `--resource-budget` flag): 31 passed in 60.68 s. AC4: `-m "not slow and not extra_slow" --collect-only` over those two files lists the same 31 tests before and after (diff empty). Note the 800t test ran 42 s here against 48 s measured by the planner, so the 60 s medium budget was passing here; the marker is headroom for host load, not a fix I could reproduce failing.

## Files Changed
`tests/tools/test_entity_lifecycle_score.py`

## Completion Summary
The 800-tick test now has the 600 s budget via `resource_budget_large`; CI lane selection unchanged. testing-planner gets an fyi from the planner.
