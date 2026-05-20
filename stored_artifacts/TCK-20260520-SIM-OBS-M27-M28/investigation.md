# Investigation - Storage Export and Local Analytics

## Architecture & Code Boundaries
- **Artifact Isolation**: The export layer reads directly from the artifact repository (`RunArtifactRepository` / `RunSetArtifactRepository`) which contains completed JSON/JSONL runs and sweeps. This decouples the core simulation, live telemetry, and engine execution loops completely from storage serialization and query concerns.
- **Durable State Rule**: Exported records must follow the strict typing structures of `ExportJob` and `ExportManifest`. Schema version tracking is enforced so that downstream consumers can inspect artifacts safely.
- **Registry Extensibility**: The exporter registry acts as a factory, dynamically matching format parameters to specialized exporter implementations. This guarantees that new format extensions (e.g. CSV or direct database ingestion) can be registered in the future without modifications to the main registry.

## Local Dependency Analysis
- **`pyarrow`**: Used as the storage engine for Parquet files. Python dictionary records are converted into PyArrow tables with explicit schemas before writing to Parquet.
- **`duckdb`**: In-process analytical query engine. DuckDB loads the `.parquet` files directly without requiring a running database server. SQL execution is rapid, isolated, and highly performant.

## Normalized Data Model & Parquet Schemas
1. **runs**:
   - `run_id` (string, primary identifier)
   - `sweep_id` (string, references parent sweep)
   - `scenario_name` (string)
   - `scenario_type` (string)
   - `seed` (int64)
   - `status` (string)
   - `ticks_completed` (int64)
   - `health_score` (double)
   - `critical_count` (int64)
   - `warning_count` (int64)
   - `started_at` (string)
   - `ended_at` (string, nullable)
2. **metric_windows**:
   - `run_id` (string)
   - `window_start_tick` (int64)
   - `window_end_tick` (int64)
   - `tick_compute_ms_avg` (double)
   - `tick_compute_ms_p95` (double)
   - `memory_rss_bytes_avg` (double)
   - `memory_rss_bytes_max` (double)
   - `alive_entities_avg` (double)
   - `gold_total_avg` (double)
   - `event_count` (int64)
   - `hard_law_violation_count` (int64)
3. **anomalies**:
   - `run_id` (string)
   - `rule_id` (string)
   - `severity` (string)
   - `domain` (string)
   - `tick_start` (int64)
   - `tick_end` (int64)
   - `affected_entity_count` (int64)
   - `message` (string)
4. **simulation_events**:
   - `run_id` (string)
   - `tick` (int64)
   - `event_type` (string)
   - `event_category` (string)
   - `severity` (string)
   - `entity_id` (int64, nullable)
   - `region_id` (string, nullable)
   - `quest_id` (string, nullable)
   - `message` (string)
   - `payload_json` (string, raw JSON payload representation)
