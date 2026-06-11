---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M9
artifact_type: plan
tags: [sim, obs, phase3, m9]
---

# Implementation Plan - Run Artifact Repository (Milestone 9)

## Goal

Create a standard, unified directory and contract layout for all simulation run artifacts under `data/runs/<run_id>/` and implement the `RunArtifactRepository` to govern files access, manifest metadata, schema validation, and lifecycle states.

---

## Proposed System Layout

Every simulation run will resolve to:
```
data/runs/<run_id>/
  run_manifest.json
  simulation_events.jsonl
  hard_law_violations.jsonl
  anomalies.json
  run_report.json
  run_report.md
```

### 1. `RunManifest` Model (`src/observability/reporting/artifact_repository.py`)
Standard Pydantic model enforcing:
- `run_id`: Unique identifier (string).
- `scenario_name`: String.
- `scenario_type`: String (e.g. `combat_sandbox`, `mixed_sandbox`).
- `seed`: Integer.
- `engine_version`: String (e.g. `2.0.0`).
- `observability_version`: String (`1.0.0`).
- `observability_mode`: String enum (`OFF`, `LIGHT`, `DEBUG`, `CERTIFICATION`).
- `started_at`: ISO-8601 string.
- `ended_at`: Optional ISO-8601 string.
- `ticks_requested`: Integer.
- `ticks_completed`: Integer.
- `status`: String literal (`CREATED`, `RUNNING`, `COMPLETED`, `FAILED`, `ANALYZED`, `REPORT_GENERATED`).
- `artifact_schema_version`: String (`observability_artifact_v1`).
- `failure_reason`: Optional string.

### 2. `RunArtifactRepository` (`src/observability/reporting/artifact_repository.py`)
Core service supporting:
- `create(run_id, manifest_data)` -> Creates folder and saves initial `run_manifest.json` with status `CREATED`.
- `resolve_path(run_id, file_key)` -> Safely resolves the absolute path for `events`, `violations`, `report_md`, `report_json`, `anomalies`.
- `read_manifest(run_id)` -> Reads, parses, and validates `run_manifest.json`. Rejects unsupported schema versions.
- `update_manifest(run_id, updates)` -> Merges updates to `run_manifest.json` with atomic locks.
- `list_runs()` -> Lists all run directories with basic manifest summaries.
- Overwrite protection: `create()` throws `FileExistsError` if the directory exists unless `overwrite=True` is supplied.

### 3. Connection with Recorders & Kernel
- Refactor `EventRecorder.flush()` to accept the repository file path instead of hardcoded paths.
- Integrate the `RunArtifactRepository` directly inside `Kernel` setup/shutdown hooks:
  * Upon kernel initialization (if observability mode is enabled), write the initial manifest and status `RUNNING`.
  * Upon kernel shutdown, update completed ticks, ended_at timestamp, status `COMPLETED`/`FAILED`, and flush all event recorders to the resolved directory paths.

---

## Verification Plan

### Automated Tests
- Unit: `tests/unit/observability/test_run_artifact_repository.py`
  * Tests run directory creation and overwrite guards.
  * Tests manifest read/write/update lifecycle transitions.
  * Tests version schema checking (`observability_artifact_v1` acceptance and other rejections).
- Integration: `tests/integration/observability/test_run_artifact_flow.py`
  * Simulates a kernel run and asserts all correct files are written with exact path resolution under `data/runs/<run_id>/`.
  * Asserts bit-identical state hashes are preserved under `OFF` and `LIGHT` modes.
