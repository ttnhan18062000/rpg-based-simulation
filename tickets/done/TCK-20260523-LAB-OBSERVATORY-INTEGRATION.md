# TCK-20260523-LAB-OBSERVATORY-INTEGRATION

## Title

Scenario Lab Observatory Integration

## Status

DONE

## Request Summary

Connect Scenario Lab execution with the simulation's Observatory artifacts and analysis pipeline (Milestone 79). This requires:
1. Ensuring every child run creates standard Observatory artifacts.
2. Executing post-run diagnostic analysis after each completed child run.
3. Automatically compiling comprehensive child run reports (`run_report.json` and `run_report.md`).
4. Compiling aggregated lab-level summary diagnostics (`lab_summary.json` and `lab_summary.md`) across all sweeps/seeds.
5. Establishing clean robust validation policies for health scores and failure classifications, protecting storage and budget integrity.

## Scope

- Modify `src/lab/orchestrator.py` to:
  - Aggregate diagnostic statistics across child runs (average health, counts of criticals/warnings, best/worst run ID, storage footprint, and top anomalies frequency).
  - Write complete, robust, standardized `lab_summary.json` and `lab_summary.md` summaries in the lab run output directory.
  - Enforce strict behavior when all child runs fail: the overall lab status must NOT be success (it must be `FAILED`).
  - Report missing or corrupted run reports gracefully in the summary without silent swallowing.
- Create full integration test suite:
  - `tests/integration/lab/test_lab_observatory_integration.py`
  - Verifying child run Observatory artifacts, post-run reports, aggregation, failure handling, and anti-misdirection policies.

## Out of Scope

- High-level scenario mutation balance lab matrix engine.
- Parallel worker scheduling/execution concurrency model.
- Long-term database storage/indexing.

## Acceptance Criteria

- [x] Every successfully executed seed run records standard Observatory artifacts in the lab-specific directory.
- [x] Every completed seed run undergoes analysis and generates `run_report.json` and `run_report.md`.
- [x] The orchestrator compiles and writes a comprehensive `lab_summary.json` containing:
  - `lab_run_id`, `world_id`, `scenario_id`, `experiment_id`
  - `status`, `total_runs`, `completed_runs`, `failed_runs`
  - `average_health_score`, `critical_count_total`, `warning_count_total`
  - `top_anomalies` (most frequent top 5), `worst_run_id`, `best_run_id`
  - `storage_usage_mb`
- [x] The orchestrator compiles and writes a beautifully styled executive `lab_summary.md`.
- [x] If all child runs fail, the lab status is correctly marked as `FAILED` rather than success, and health/metrics are represented accurately.
- [x] Missing run reports are explicitly reported and logged, not swallowed.
- [x] All integration tests in `test_lab_observatory_integration.py` pass without any failures.

## Related Tickets

- `TCK-20260523-LAB-ORCHESTRATOR.md`

## Related Docs

- `lab_phase12.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/orchestrator.py`
- `tests/integration/lab/test_lab_observatory_integration.py`

## Assumptions / Open Questions

- We assume sequential execution mode is active and resource budgets are strictly handled.

## Implementation Notes

- We leveraged `AnalysisPipeline` and the `RunReportGenerator` inside `AnalysisPipeline`.
- We parsed `run_report.json` directly from each run directory to calculate aggregations.
- Kept legacy properties in `lab_summary.json` for backwards compatibility with existing test suites.

## Test Summary

- All tests in `test_lab_observatory_integration.py` pass successfully (100% pass).

## Files Changed

- `src/lab/orchestrator.py`
- `tests/integration/lab/test_lab_observatory_integration.py`

## Completion Summary

- Successfully completed the Scenario Lab Observatory Integration (Milestone 79).
- Built robust aggregates across all successfully analyzed child runs, generated beautiful markdown summary scorecards, and implemented strict failure status safeguards.
