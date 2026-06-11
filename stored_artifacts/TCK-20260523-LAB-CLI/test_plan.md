---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-CLI
artifact_type: test_plan
tags: [lab, cli]
---

# Test Plan - Lab CLI (Milestone 81)

We will verify all subcommand executions via command-line simulation tests.

## Test Cases

1. **`validate-world`**:
   - Exit code `0` on valid world id.
   - Non-zero exit code on missing or invalid world id.
2. **`validate-scenario`**:
   - Exit code `0` on valid scenario.
   - Non-zero on invalid scenario.
3. **`validate-experiment`**:
   - Exit code `0` on valid experiment.
   - Non-zero on invalid experiment.
4. **`run`**:
   - Verifies orchestrator runs successfully, prints `lab_run_id`, returns `0` or `1` on status.
5. **`status` / `report` / `inspect` / `list`**:
   - Verifies text prints of manifest status, markdown path, raw json, and run listing respectively.
