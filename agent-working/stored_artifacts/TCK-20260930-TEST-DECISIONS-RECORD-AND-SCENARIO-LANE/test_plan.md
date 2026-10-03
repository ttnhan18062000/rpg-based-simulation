---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE
artifact_type: test_plan
tags: [testing]
---

# Test plan

## Proof Plan
- **proof kind:** unit tests for the classifier (trigger, irrelevant, unknown, fail-open on empty diff and on error) and for the report renames; a workflow-shape test for the job condition (single run, fail open).
- **oracle source:** roadmap §11 D-R2 text and reviewer conditions 1-4; no Bible chapter applies (test tooling only, no simulation behaviour).
- **expected effect:** `tests/mechanic_scenarios`-only and `src/**` PRs run the lane exactly once; docs-only PRs skip it; unknown paths run it and are named; a file absent from supplied runs reads `not-in-supplied-runs`.
- **selected commands:** `pytest tests/unit/tools/test_scenario_lane_paths.py tests/unit/tools/test_core_rpg_report.py tests/unit/tools/test_impact_report.py tests/tools/test_ci_workflow_test_coverage.py -q`; docs and frontmatter validators.
- **fixtures:** none shared; synthetic tmp repos already used by the report tests.
