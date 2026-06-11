---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M20
artifact_type: plan
tags: [sim, obs, phase4, m20]
---

# Implementation Plan - Scenario-Level Report and CI Gate

## Goal
Build a working system that compiles individual runs into a comprehensive Markdown and JSON scenario-level sweep report, and provides a CI gate enforcing statistical and custom envelope expectations.

## Proposed Changes

### `src/observability/reporting/sweep_report.py` [NEW]
- Define `CIGateResult` and `SweepReportData` schemas.
- Build `SweepReportGenerator` orchestrating sweep comparison, Markdown report compiling, JSON sweep report generation, and CI gate logic.
- Implement highly structured Markdown rendering covering all 12 requested sections.

### `src/cli/entry.py` [MODIFY]
- Register the `rpg-observe gate <sweep_id> --baseline <baseline.json> [--envelope <envelope.json>]` CLI subcommand.
- Support options: `--warn-as-fail` and `--insufficient-as-fail`.
- Exit the Python process with exit code 0 on PASS, 1 on FAIL / WARNING / INSUFFICIENT_DATA as configured.

## Verification Plan

### Automated Tests
- Unit tests under `tests/unit/observability/test_sweep_report_generator.py` covering report data building, Markdown section completeness, and CI Gate configuration responses.
- End-to-end integration tests under `tests/integration/observability/test_scenario_level_report_flow.py` running the `rpg-observe gate` command under various pass, warn, and fail conditions.
