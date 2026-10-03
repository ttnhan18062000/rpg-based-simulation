---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M15
artifact_type: test_plan
tags: [sim, obs, phase4, m15]
---

# Test Plan - Milestone 15: Scenario Run Matrix and Sweeper

We will verify both unit-level configuration constraints and e2e integration flow outcomes.

## Unit Tests

### `tests/unit/observability/test_sweep_config.py`
- Validate that Pydantic properly accepts a complete, valid `ScenarioSweepConfig` structure.
- Assert rejection of empty seed lists.
- Assert rejection of non-positive ticks or negative max parallel bounds.
- Assert validation of known scenario types vs custom designations.

### `tests/unit/observability/test_scenario_sweeper.py`
- Verify conversion of `ScenarioSweepConfig` into individual `ScenarioRunSpec` records.
- Assert stable run ID patterns mapped uniquely per seed.

## Integration Tests

### `tests/integration/observability/test_sweep_execution_flow.py`
- Run a 3-seed simulation sweep on the `"idle"` scenario under `LIGHT` mode.
- Verify that individual run directories (`run_sets/<sweep_id>/runs/<run_id>`) are created and contain complete run outputs.
- Verify the generated `run_set_manifest.json` correctly maps run IDs, seeds, ticks requested, completed count, and execution statuses.
- Verify error boundary handling by mocking a scenario failure (e.g. invalid scenario ID) and checking that:
  - When `stop_on_first_critical` is False, the sweep records the failure and proceeds to execute other seeds.
  - When `stop_on_first_critical` is True, the sweep terminates early.
