---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-BUDGET-GUARDRAILS
artifact_type: test_plan
tags: [world, budget, guardrails]
---

# Test Plan — Milestone 74 Resource and Storage Guardrails

We will create a new test module `tests/unit/worldbuilding/test_world_budget_guardrails.py`.

## Targets Verified
- `test_local_dev_rejects_oversized_world`: Validates that a world containing 1,500 workers is rejected under `local_dev` profile (entity count exceeds 1,000 threshold).
- `test_long_run_lab_allows_larger_world`: Validates that the same 1,500 workers spec is successfully allowed under the `long_run_lab` profile (threshold is 10,000).
- `test_estimated_artifact_size_warning`: Generates warnings when forecasted ticks/counts forecast log storage sizes over the limit.
- `test_budget_report_included_in_validation`: Asserts that validation issues cleanly report active rule details.
