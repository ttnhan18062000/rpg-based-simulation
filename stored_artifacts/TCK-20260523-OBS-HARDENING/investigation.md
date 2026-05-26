# Technical Investigation - Simulation Observability Stack Hardening

This document outlines the root-causes and technical details for all identified issues in the observability pipeline across Phases 1–9.

## 1. ObservabilityMode Mapping
- **Source**: `src/observability/mining/controller.py`
- **Issue**: The `obs_mode_mapping` dictionary was mapping strings to `ObservabilityMode.PRODUCTION` and `ObservabilityMode.FULL`. However, the actual enum `ObservabilityMode` in `src/observability/config.py` only defines `OFF`, `LIGHT`, `DEBUG`, `CERTIFICATION`, and `LONG_RUN`. This would cause attribute crashes under certain configuration configurations.
- **Resolution**:
  - `production` -> `ObservabilityMode.LONG_RUN`
  - `full` -> `ObservabilityMode.DEBUG`
  - `light` -> `ObservabilityMode.LIGHT`
  - `none` -> `ObservabilityMode.OFF`
  - `cert` -> `ObservabilityMode.CERTIFICATION`

## 2. Docker Compose References
- **Source**: `docker-compose.yml`
- **Issue**: Services `ai_worker` and `watchdog` were configured with legacy command targets (`src.workers.ai_worker_daemon` and `src.utils.watchdog`) which no longer exist in the V2 layout.
- **Resolution**:
  - `ai_worker` command updated to use: `python -m src.observability.anomaly.worker` (with a newly added `__main__` entrypoint block).
  - `watchdog` command updated to use: `python -m src.observability.watchdog` (new V2 watchdog implementation).

## 3. Schema Inconsistencies & Hard-Law Persistence
- **Source**: `src/observability/hard_law_monitor.py`, `src/observability/warehouse/adapters.py`, `src/observability/reporting/artifact_repository.py`
- **Issue**:
  - Hard law violations are expected at `hard_law_violations.jsonl` by `RunArtifactRepository` but some mining matrix components read from `hard_law_violations.json`.
  - The `HardLawMonitor` did not write violations to the run artifact `.jsonl` file.
- **Resolution**:
  - Enforce `hard_law_violations.jsonl` naming everywhere.
  - Implement dynamic appending of hard-law violations inside `HardLawMonitor` to ensure post-run analytics can read them accurately.

## 4. Determinism Auditor
- **Source**: `src/observability/mining/auditors.py`
- **Issue**: If seeds or final hashes are missing/empty, the auditor would return `DETERMINISTIC` by default due to a "no mismatch found" logic fall-through.
- **Resolution**: Add explicit check. If hash list is empty or hashes are missing, return `INSUFFICIENT_DATA`.

## 5. Expectation Packs
- **Source**: `src/observability/understanding/expectation_packs/`
- **Issue**: Missing scenario expectation packs (`resource_economy.json`, `combat_heavy.json`, `peaceful_village.json`, `mixed_sandbox.json`) caused scenario understanding tests to fail or silently fall back to `mixed_sandbox`.
- **Resolution**: Populate each scenario json file with valid threshold constraints matching their profile context.

## 6. Resource Metric for ResourceProductionZero Rule
- **Source**: `src/observability/anomaly/rules.py`
- **Issue**: The `ResourceProductionZero` rule utilized average gold as a proxy for resource production. Gold is an economic exchange medium, not direct production.
- **Resolution**: Pivot the rule to evaluate direct production/harvesting metrics.

## 7. pyarrow Optional Fallback
- **Source**: `src/observability/warehouse/exporter.py`
- **Issue**: If `pyarrow` is absent, Parquet exports crashed the program instead of cleanly warning the user or falling back.
- **Resolution**: Implement try-except import guard; fall back to a standard JSON/CSV representation or skip gracefully.
