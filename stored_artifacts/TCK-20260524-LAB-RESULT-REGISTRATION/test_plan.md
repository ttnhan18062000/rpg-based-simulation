---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-RESULT-REGISTRATION
artifact_type: test_plan
tags: [lab, result, registration]
---

# Test Plan: RegisterSimulationResult Workflow (Milestone 98)

We will implement standard pytest-based integration tests at `tests/integration/lab_agent/test_register_simulation_result_workflow.py`.

## Test Cases

### 1. `test_registration_complete_success`
- Set up a completed run directory with valid `lab_run_manifest.json` and a matching number of child run subdirectories.
- Execute workflow in `"specific"` mode.
- Verify status is `"READY"`, integrity check result is `"COMPLETE"`, manifest linked runs are updated, and all output files are generated.

### 2. `test_registration_partial_run`
- Set up a run directory with a manifest indicating `run_count = 5` but only 3 child run subdirectories exist.
- Verify result integrity check status is `"PARTIAL"`.

### 3. `test_registration_missing_run_fails`
- Provide a non-existent path.
- Verify status is `"BLOCKED"`, classification is `"MISSING"`.

### 4. `test_registration_corrupted_manifest`
- Provide a directory with an invalid or malformed `lab_run_manifest.json`.
- Verify classification is `"CORRUPTED"`.

### 5. `test_registration_path_traversal_blocked`
- Provide target directory outside the workspace.
- Verify that `PermissionError` is raised.
