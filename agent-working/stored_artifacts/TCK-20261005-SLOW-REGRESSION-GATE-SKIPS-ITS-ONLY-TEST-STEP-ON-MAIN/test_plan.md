---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | record | read | reviewer's REST jobs API measurement | failed vs cancelled split recorded, cause not investigated | read Implementation Notes |
| 2 | static | `yaml.safe_load` pytest | `.github/workflows/test.yml` `slow` job | steps 6-7 carry `!cancelled()`; no `always()` / `continue-on-error` on steps 5-7; summary step reads all three outcomes | `pytest tests/static/test_ci_slow_job_step_gating.py` |
| 3 | mutation | remove step 6's `if:` | the same test | `test_slow_tests_step_runs_even_when_corpus_diversity_fails` fails | run once by hand, workflow restored |
| 4 | live CI | first `main` push run after merge | Actions jobs API | steps 6-7 ran; outcome recorded by the reviewer | post-merge, not runnable before merge |

## Regression pins
`pytest tests/static tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_conftest_resource_budget.py tests/unit/tools/test_scenario_lane_paths.py` (130 passed), including `test_ci_registry_resync_skip_jobs.py` and `test_ci_step_summary_reporting.py`.
