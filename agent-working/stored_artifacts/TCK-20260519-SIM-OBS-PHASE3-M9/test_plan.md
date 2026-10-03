---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M9
artifact_type: test_plan
tags: [sim, obs, phase3, m9]
---

# Test Plan - Run Artifact Repository (Milestone 9)

## 1. Unit Tests

File: `tests/unit/observability/test_run_artifact_repository.py`

### Test cases:
- **`test_repository_directory_creation`**:
  * Assert that creating a run directory makes a standard directory with the resolved path.
  * Assert that `run_manifest.json` is successfully written.
- **`test_overwrite_protection`**:
  * Assert that calling `create()` on an existing `run_id` throws `FileExistsError`.
  * Assert that supplying `overwrite=True` overrides the check and successfully overwrites the existing run manifest.
- **`test_manifest_lifecycle_updates`**:
  * Create a manifest with status `CREATED`.
  * Update status to `RUNNING`, then `COMPLETED` and assert that fields merge cleanly without losing original values (like scenario_name or seed).
- **`test_schema_version_validation`**:
  * Assert that a reader accepts runs with `artifact_schema_version = "observability_artifact_v1"`.
  * Assert that a reader rejects runs with unsupported schema versions (e.g. `"observability_artifact_v99"`) throwing a `ValueError` or a customized schema compatibility exception.

---

## 2. Integration Tests

File: `tests/integration/observability/test_run_artifact_flow.py`

### Test cases:
- **`test_kernel_simulation_produces_artifacts`**:
  * Run the `Kernel` with observability enabled (`LIGHT`).
  * Verify that a run directory is created under `data/runs/<run_id>/`.
  * Verify that `run_manifest.json` exists and matches the run settings.
  * Verify that `simulation_events.jsonl` exists and is populated with events.
- **`test_observability_parity_invariants`**:
  * Run same configuration with observability `OFF` vs `LIGHT`.
  * Assert that final state hashes are 100% identical, ensuring zero side-effects.
