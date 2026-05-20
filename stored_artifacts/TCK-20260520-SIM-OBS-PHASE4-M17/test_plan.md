# Test Plan - Milestone 17: Baseline Generator

We will verify both repository operations and end-to-end integration flows.

## Unit Tests

### `tests/unit/observability/test_baseline_generator.py`
- Verify pure-Python percentile and standard deviation helper calculations match expected statistics.
- Mock index records (some completed, some failed, some with violations).
- Verify successful filtering and that failed or violation-ridden runs are excluded by default.
- Verify custom override manual includes/excludes.
- Verify "is_weak_baseline" flags correctly based on sample run counts.

## Integration Tests

### `tests/integration/observability/test_baseline_generation_flow.py`
- Execute a 5-seed sweep of scenario `"idle"`.
- Invoke the CLI `generate-baseline` command on this sweep ID.
- Verify that `baseline.json` is generated correctly in the sweep directory.
- Verify that all core metrics contain valid stats (count, min, max, mean, percentiles).
- Verify CLI prints warnings when sample size is low (< 5 for development, < 30 for balance).
