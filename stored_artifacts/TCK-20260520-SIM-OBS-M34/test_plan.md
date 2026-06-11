---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M34
artifact_type: test_plan
tags: [sim, obs, m34]
---

# Test Plan: Warehouse Adapter & Schema Validation

We will implement complete unit and integration tests to verify the robustness of the Warehouse Adapter boundary and schema stabilization.

---

## 1. Automated Unit Tests

### Test File: `tests/unit/observability/test_warehouse_adapter_interface.py`
- **Goal**: Confirm that `WarehouseAdapter` base abstract class cannot be instantiated directly and forces implementing subclasses to define required signatures.
- **Coverage**:
  - Direct instantiation of `WarehouseAdapter` raises `TypeError`.
  - Concrete class implementing all abstract methods instantiates cleanly.
  - Class definition defines all standard parameters: `ingest_run`, `ingest_sweep`, `query_runs`, `query_events`, `query_anomalies`, `health`, and `close`.

### Test File: `tests/unit/observability/test_warehouse_record_mapping.py`
- **Goal**: Verify that local run and sweep artifacts convert cleanly to versioned Pydantic record models.
- **Coverage**:
  - `SimulationEvent` json dictionary maps successfully to `EventRecord` and serializes `payload` dictionary to a raw JSON string.
  - `RunManifest` validates and converts into a database `RunRecord`, keeping `manifest_json` populated.
  - `AnomalyReport` converts to `AnomalyRecord`, preserving evidence payloads.
  - Verification of null/missing fields constraints (e.g. `region_id` can be None/null, raising ValueError on missing mandatory `run_id` fields).
  - Registry checks: `WarehouseSchemaRegistry.validate_artifact_version()` successfully parses `observability_artifact_v1` and raises `WarehouseSchemaVersionMismatchError` if a fake/unsupported version (e.g. `observability_artifact_v999`) is passed.

---

## 2. Automated Integration Tests

### Test File: `tests/integration/observability/test_warehouse_ingestion_dry_run.py`
- **Goal**: Verify end-to-end execution of the ingestion dry-run process using CLI routes.
- **Coverage**:
  - Run `rpg-observe warehouse ingest-run <run_id> --dry-run` and check exit code `0`.
  - Verify that the terminal logs ingestion statistics (events processed, anomalies found, timing metrics).
  - Verify that executing in dry-run mode has 100% zero side-effects on disk/database.
  - Run `rpg-observe warehouse ingest-run <run_id> --dry-run` with a simulated invalid/corrupt schema and confirm exit code `1` or expected error message output.
