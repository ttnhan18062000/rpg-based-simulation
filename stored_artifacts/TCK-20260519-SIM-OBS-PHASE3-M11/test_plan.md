# Test Plan - Milestone 11: Analysis Pipeline Orchestrator

## Unit Tests (`tests/unit/observability/test_analysis_pipeline.py`)
- **Loader Validation**:
  - Test loading a fully completed run context.
  - Test failure when `run_manifest.json` is missing.
  - Test failure when status is partial (`"RUNNING"`) by default.
  - Test successful load of partial status when `allow_partial=True` is provided.
- **Registry & Order**:
  - Test that registering and executing custom analyzers keeps stable ordering.
  - Test that an analyzer throwing an exception is handled gracefully (does not crash pipeline, writes error to `AnalysisResult`).
- **Default Analyzers**:
  - Test `BasicRuntimeAnalyzer` generating anomalies on high average CPU usage or excessive memory max RSS.

## Integration Tests (`tests/integration/observability/test_analysis_pipeline_flow.py`)
- **End-to-End Orchestration**:
  - Setup a mock completed run directory with manifest, events, metrics, and violations.
  - Execute `AnalysisPipeline.run(run_id)`.
  - Assert that `anomalies.json`, `anomaly_summary.md`, `run_report.json`, and `run_report.md` are all created.
  - Assert that the manifest status is updated to `"ANALYZED"`.
