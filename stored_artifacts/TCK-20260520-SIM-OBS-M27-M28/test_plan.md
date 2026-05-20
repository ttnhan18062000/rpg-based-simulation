# Test Plan - Storage Export and Local Analytics

## Scope of Testing

### 1. Unit Testing
- **Artifact Exporter (`tests/unit/observability/test_artifact_exporter.py`)**:
  - `test_export_jsonl_success`: Confirm a mock run gets copied to JSONL files and writes a valid `export_manifest.json` with correct record counts.
  - `test_export_parquet_success`: Verify PyArrow converts raw events and metrics into highly-typed Parquet files matching target schemas.
  - `test_exporter_unsupported_format`: Confirm registering and querying invalid formats results in descriptive `ValueError` or registry failure.
  - `test_exporter_missing_artifact_tolerance`: Validate that missing non-mandatory artifacts are skipped gracefully and recorded as `skipped` in the manifest without breaking the run export.
- **Dataset Builder (`tests/unit/observability/test_parquet_dataset_builder.py`)**:
  - `test_dataset_builder_full_sweep`: Build a complete scenario dataset from a sweep, validating table creation, indexing, manifest compilation, and file structures.
- **DuckDB Query Service (`tests/unit/observability/test_duckdb_query_service.py`)**:
  - `test_query_worst_runs`: Mock Parquet files containing various health scores and verify the sorting logic and returned list of dicts.
  - `test_query_anomaly_summary`: Validate aggregation logic grouping anomalies by rule ID and severity.

### 2. Integration Testing (`tests/integration/observability/test_export_flow.py`)
- **CLI Command Executions**:
  - Run `rpg-observe export <run_id> --format parquet` and verify command stdout and output files.
  - Run `rpg-observe export-sweep <sweep_id> --format parquet` and verify sweep runs are successfully exported.
  - Run `rpg-observe build-dataset <sweep_id>` and verify dataset generation.
  - Run `rpg-observe query-dataset <dataset_id> --query worst-runs` and verify formatted terminal output.
- **Process Exit Code Safeguards**:
  - Ensure all successful commands exit with code `0`.
  - Ensure malformed IDs or unsupported requests exit with code `1` or raise clean Click exceptions.
