---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M20
artifact_type: test_plan
tags: [sim, obs, phase4, m20]
---

# Test Plan - Scenario-Level Report and CI Gate

## Scope of Testing

### 1. Unit Testing (`tests/unit/observability/test_sweep_report_generator.py`)
- **Generator Parsing**: Ensure all 12 Markdown report sections are rendered properly in `sweep_report.md`.
- **JSON Structure**: Validate model compliance for `sweep_report.json` and `ci_gate_result.json`.
- **CI Gate Logic**: Verify that warning and insufficient data config flags appropriately convert status to FAIL.

### 2. Integration Testing (`tests/integration/observability/test_scenario_level_report_flow.py`)
- **CLI Subcommand Execution**: Run `rpg-observe gate` command using the standard Click runner.
- **Process Exit Codes**: Confirm exit code `0` for passing sweeps, exit code `1` for failures and configured warnings/insufficient data.
- **Artifact Verification**: Confirm files `sweep_report.md`, `sweep_report.json`, and `ci_gate_result.json` are written to disk under the correct directories.
