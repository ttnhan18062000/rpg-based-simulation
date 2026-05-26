# Test Plan - Milestone 18: Baseline Comparator and Drift Detector

We will verify both repository operations and end-to-end integration flows.

## Unit Tests

### `tests/unit/observability/test_baseline_comparator.py`
- Mock baseline and run indexes/reports.
- Test that missing metrics produce `INSUFFICIENT_DATA` rather than returning a false pass.
- Test that run reports with critical violation or status FAILED correctly yield `FAIL` status.
- Test that outliers are correctly identified within sweeps.
- Test drift magnitude and direction detection logic.

## Integration Tests

### `tests/integration/observability/test_baseline_comparison_flow.py`
- Execute a 5-seed sweep of scenario `"idle"`.
- Generate a baseline from the sweep.
- Inject fake variations or execute another sweep to trigger outlier/drift comparisons.
- Run CLI commands `compare-run` and `compare-sweep`.
- Verify that comparative JSON files are saved.
- Verify CLI prints out exact comparisons.
- Verify exit codes are correct (0 for pass/warning, 1 for fail).
