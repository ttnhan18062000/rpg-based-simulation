---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-ORCHESTRATOR
artifact_type: test_plan
tags: [lab, orchestrator]
---

# Test Plan — Milestone 78 Orchestrator

## Test Cases

### 1. Unit Tests (`tests/unit/lab/test_scenario_lab_orchestrator.py`)
- Orchestrator validates world specification before compilation, blocking execution and raising `InvalidWorldSpecError` on failure.
- Orchestrator raises validation errors when Scenario or Experiment specs are invalid.
- Safe path-traversal checks.

### 2. Integration Tests (`tests/integration/lab/test_scenario_lab_single_run_flow.py`)
- Executes single-run workflows from end-to-end.
- Validates that completed run artifacts are saved inside the run directory.
- Runs post-simulation analysis pipeline.

### 3. Integration Tests (`tests/integration/lab/test_scenario_lab_multi_seed_flow.py`)
- Runs sweeps across multiple seeds.
- Verifies that any failed runs mark the lab status as `PARTIAL` or `FAILED`.
- Writes lab summary correctly.
