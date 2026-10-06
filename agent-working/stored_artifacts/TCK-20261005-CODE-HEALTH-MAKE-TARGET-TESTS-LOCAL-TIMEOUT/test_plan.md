---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | integration | run both tests under the default budget, no flag | `tests/conftest.py` budget hook | both pass (they run under 600 s) | `pytest tests/codebase/test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` |
| 2 | record | timing with `subprocess.run` wrapped | measured durations | cause written in the ticket | see Implementation Notes |

## Regression pins
`pytest tests/static tests/tools/test_conftest_resource_budget.py` (130 passed together with the workflow-coverage and scenario-lane tests).
