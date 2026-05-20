# TCK-20260520-SIM-OBS-PHASE4-M17

## Title

Milestone 17 — Baseline Generator

## Status

DONE

## Request Summary

Implement a Baseline Generator that parses multi-run index records and telemetry outputs from successful runs of a scenario, calculates distribution summaries (p10, p50, p90, p95, mean, etc.), recommends auto-generated control thresholds, and exports a structured `baseline.json` file.

## Scope

- Define the `DistributionSummary`, `BaselineThresholdSpec`, and `BaselineConfig` models using Pydantic.
- Implement the `BaselineGenerator` service that selects eligible runs (filtering out failed runs and runs with critical hard law violations by default) and handles include/exclude overrides.
- Compute statistical distributions for health score, critical counts, warning counts, law violations, tick compute times (p95), peak memory RSS, event counts, and anomaly counts.
- Generate threshold recommendations based on standard distribution metrics and scaling tolerances.
- Implement `BaselineRepository` to save and load `baseline.json` under the sweep folder or a shared baselines directory.
- Expose the CLI subcommand `rpg-observe generate-baseline <sweep_id>`.
- Add comprehensive unit and integration test coverage.

## Out of Scope

- Real-time online regression comparisons (Milestone 18).
- Multi-scenario baseline crossing.

## Acceptance Criteria

- `BaselineGenerator` excludes failed or critical-fault runs by default.
- Statistical distributions (min, max, mean, median, standard deviations, and percentiles p10, p50, p90, p95) are calculated accurately.
- Samples with run count below a specified threshold (e.g. 5) are clearly flagged as "weak" baselines.
- Threshold recommendations are automatically compiled with correct data types.
- Saving and loading of `baseline.json` works correctly.
- CLI command `rpg-observe generate-baseline` launches cleanly and displays output paths.

## Related Tickets

- TCK-20260520-SIM-OBS-PHASE4-M16 (Completed)

## Related Docs

- `obs_sim_phase4.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/baseline_generator.py` (NEW)
- `src/cli/entry.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- `numpy` is not strictly guaranteed to be installed; we will implement a clean, pure-Python percentile and standard deviation calculator to ensure absolute zero dependency overhead and full compatibility!

## Test Summary

- `tests/unit/observability/test_baseline_generator.py`
- `tests/integration/observability/test_baseline_generation_flow.py`

## Files Changed

- `src/observability/reporting/baseline_generator.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_baseline_generator.py`
- `tests/integration/observability/test_baseline_generation_flow.py`

## Completion Summary

- Implemented `DistributionSummary`, `BaselineThresholdSpec`, and `BaselineConfig` models.
- Developed the pure-Python distribution analyzer and percentile interpolation helper methods to compute correct parameters without external libraries.
- Implemented robust eligible run filtering rules and developer inclusion/exclusion overrides in `BaselineGenerator`.
- Wired the `rpg-observe generate-baseline <sweep_id>` subcommand and registered execution handlers inside `entry.py`.
- Wrote thorough unit and integration test coverages validating mathematical formulas, fallback safety, exclusions, overrides, and CLI subcommands. All 69 tests pass beautifully.
