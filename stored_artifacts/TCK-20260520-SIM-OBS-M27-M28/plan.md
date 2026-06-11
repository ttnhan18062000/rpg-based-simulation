---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M27-M28
artifact_type: plan
tags: [sim, obs, m27, m28]
---

# Implementation Plan - Storage Export and Local Analytics

## Goal
Implement Milestone 27 (Storage Export Layer) and Milestone 28 (DuckDB / Parquet Local Analytics) to provide a modular storage abstraction and high-performance offline analytics query pipeline using Parquet and DuckDB.

## Proposed Changes

### `src/observability/analytics/exporter.py` [NEW]
- Define `ExportJob` and `ExportManifest` Pydantic models.
- Implement `ArtifactExporter` registry mapping formats (`jsonl`, `parquet`) to specialized exporter implementations.
- Implement `JSONLArtifactExporter` copying raw run artifacts to JSONL format.
- Implement `ParquetArtifactExporter` converting raw run artifacts to schema-conforming Parquet files.

### `src/observability/analytics/dataset.py` [NEW]
- Define schema structures and type definitions for tables: `runs`, `metric_windows`, `anomalies`, and `simulation_events`.
- Implement `AnalyticsDatasetBuilder` reading a scenario sweep, loading its run set index and individual run directories, normalizing raw data, and writing structured Parquet tables under `data/analytics/<dataset_id>/`.
- Generate `dataset_manifest.json` under the dataset folder detailing record counts and table file paths.

### `src/observability/analytics/query.py` [NEW]
- Implement `DuckDBQueryService` using DuckDB's in-process SQL engine to query Parquet files.
- Support pre-defined SQL templates:
  - `worst-runs`: `SELECT run_id, seed, health_score, status, critical_count FROM runs ORDER BY health_score ASC, critical_count DESC`
  - `anomaly-summary`: `SELECT rule_id, severity, COUNT(*) as count FROM anomalies GROUP BY rule_id, severity ORDER BY count DESC`
- Return JSON-safe list of dictionaries for query responses.

### `src/cli/entry.py` [MODIFY]
- Register the new command sub-parsers under standard CLI:
  - `export` (run_id, format)
  - `export-sweep` (sweep_id, format)
  - `build-dataset` (sweep_id)
  - `query-dataset` (dataset_id, query)
- Route the command sub-parsers to corresponding handlers `_run_export`, `_run_export_sweep`, `_run_build_dataset`, and `_run_query_dataset`.

---

## Verification Plan

### Automated Tests
- **Unit Tests**:
  - `tests/unit/observability/test_artifact_exporter.py`: Verify JSONL and Parquet export matching schemas, manifest creation, and format rejection.
  - `tests/unit/observability/test_parquet_dataset_builder.py`: Validate dataset table generation, manifest building, and empty/missing runs tolerances.
  - `tests/unit/observability/test_duckdb_query_service.py`: Verify that predefined SQL queries fetch correct counts and sort orders on mock Parquet files.
- **Integration Tests**:
  - `tests/integration/observability/test_export_flow.py`: Run full end-to-end command invocations via CLI checking paths, manifests, and exit codes.
