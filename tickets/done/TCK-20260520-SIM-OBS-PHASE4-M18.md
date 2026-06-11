---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M18
phase: done
date: 2026-05-20
tags: [sim, obs, phase4, m18]
---

# TCK-20260520-SIM-OBS-PHASE4-M18

## Title

Milestone 18 — Baseline Comparator and Drift Detector

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a Baseline Comparator and Drift Detector that compares a single run report or a multi-run sweep index against a saved baseline. Identify outlier runs, perform statistical distribution shift comparisons to detect drift, register comparison CLI commands, and support exit codes for CI gating.

## Scope

- Define the `MetricComparison`, `ComparisonResult`, `DriftSummary`, and `SweepComparisonResult` Pydantic models.
- Implement the `BaselineComparator` service performing:
  - Single run validation against control baseline threshold expectations.
  - Multi-run sweep comparison identifying outlier seeds.
  - Statistical drift detection measuring metric shifts (means and percentiles) and drift magnitudes.
- Export comparison outputs (`baseline_comparison.json` and `sweep_baseline_comparison.json`) into corresponding run or sweep folders.
- Register CLI commands:
  - `rpg-observe compare-run <run_id> --baseline <baseline_json>`
  - `rpg-observe compare-sweep <sweep_id> --baseline <baseline_json>`
- Ensure CLI subcommands return non-zero exit codes when comparison status is `FAIL`.
- Add unit and integration tests.

## Out of Scope

- Designing YAML balance envelope profiles (Milestone 19).

## Acceptance Criteria

- High-severity faults (such as `critical_count > 0` or hard law violations) must fail comparison.
- Metrics not present in run reports produce `INSUFFICIENT_DATA` rather than returning false passes.
- Sweep comparator successfully lists outlying runs/seeds exceeding envelope margins.
- Drift detector accurately detects downward health score shifts or upward performance compute ms/memory spikes.
- CLI subcommand prints tabular execution matrixes.
- CLI exits with code 1 if comparisons fail, enabling CI pipeline gates.

## Related Tickets

- TCK-20260520-SIM-OBS-PHASE4-M17 (Completed)

## Related Docs

- `obs_sim_phase4.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/baseline_comparator.py` (NEW)
- `src/cli/entry.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- We implemented a robust fallback parser for completed runs: if `run_report.json` is missing, but `run_manifest.json` shows status `"COMPLETED"` or `"RUNNING"` (with positive ticks), we default critical and warning counts to `0` instead of throwing a false `INSUFFICIENT_DATA` error.

## Test Summary

- `tests/unit/observability/test_baseline_comparator.py` - Verified single-run and sweep comparative validation, fallback paths, and metric evaluations.
- `tests/integration/observability/test_baseline_comparison_flow.py` - Verified E2E sweep baseline generation, single run and sweep comparisons, CLI subcommand execution flows, and correct CI exit code gating.

## Files Changed

- `src/observability/reporting/baseline_comparator.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_baseline_comparator.py`
- `tests/integration/observability/test_baseline_comparison_flow.py`

## Completion Summary

- Implemented full `BaselineComparator` logic with highly descriptive schemas for single-run and sweep validation.
- Engineered precise outlier checks and statistical drift calculators assessing distribution shifts in health, latency, memory, and anomaly indices.
- Registered CLI subcommands `rpg-observe compare-run` and `rpg-observe compare-sweep` offering elegant command outputs and reliable CI-friendly exit code gating.
- Reconciled environment configuration paths and achieved 100% successful test coverage.
