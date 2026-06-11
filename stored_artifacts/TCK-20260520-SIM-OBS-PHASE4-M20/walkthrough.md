---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [sim, obs, phase4, m20]
---

# Walkthrough: Scenario-Level Reporting and CI Gate (Milestone 20)

We have successfully implemented and thoroughly verified **Milestone 20: Scenario-Level Reporting and CI Gate** for the observability suite. This completes the full multi-run sweep execution, analysis, baseline comparative reporting, and continuous integration validation gating lifecycle.

## Overview of Completed Work

### 1. Sweep Report Generator (`sweep_report.py`)
- Created `src/observability/reporting/sweep_report.py` containing the core `SweepReportGenerator` and the `CIGateResult` Pydantic model.
- Automatically generates:
  - **`sweep_report.md`**: An exhaustive Markdown report compiling 12 key sections (Executive Summary, Sweep Metadata, Run Distribution, Baseline Summary, Comparison Result, Outlier Seeds, Most Common Anomalies, Performance/Memory/Health Drifts, Failed Expectations, and Recommended Investigation Points).
  - **`sweep_report.json`**: An structured JSON compilation of the sweep results containing outlier listings and metric drifts.
  - **`ci_gate_result.json`**: A concise CI-oriented JSON file storing the final gating status, messages, and failed metrics/runs.

### 2. E2E CLI Integration (`entry.py`)
- Registered the `gate` subcommand inside the CLI entry handler parser (`src/cli/entry.py`).
- Added robust support for specific process exit codes and configurations:
  - `--warn-as-fail`: Escapes warning results as non-zero process exits (exit code 1).
  - `--insufficient-as-fail`: Escapes insufficient data results as non-zero exits (exit code 1).
- Integrates gracefully with all scenario sweep indexing repositories and error isolation wrappers.

### 3. Comprehensive Verification & Regression Tests
- **Unit Tests (`test_sweep_report_generator.py`)**: Covers mocking setups, distribution evaluations, and report validation checks.
- **Integration Tests (`test_scenario_level_report_flow.py`)**: Tests CLI arguments parsing, warning conditions, and exit code accuracy.

---

## Verifying report generation and CI Gating

### CLI Command Options
You can run the new scenario gating and report compilation directly from the command line using:
```bash
rpg-observe gate <sweep_id> --baseline <baseline_path> [--envelope <envelope_path>] [--warn-as-fail] [--insufficient-as-fail]
```

### Passing Tests Summary
Run the complete suite of observability checks to certify parity and stability:
```bash
pytest -v tests/unit/observability/ tests/integration/observability/
```

**Key Execution Proof**:
```text
tests/unit/observability/test_sweep_report_generator.py::test_sweep_report_generator_success PASSED
tests/unit/observability/test_sweep_report_generator.py::test_ci_gate_gating_warnings_and_failures PASSED
tests/integration/observability/test_scenario_level_report_flow.py::test_cli_gate_scenario_level_flow PASSED
tests/integration/observability/test_scenario_level_report_flow.py::test_cli_gate_warn_as_fail PASSED

============================== 85 passed in 7.78s ==============================
```
