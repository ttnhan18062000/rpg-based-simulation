# Plan — TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE

## Step 1 — Create fixture directory tree

`tests/fixtures/__init__.py` (empty)
`tests/fixtures/lab_runs/minimal_completed_run/lab_run_manifest.json`:
  - All LabRunManifest fields, status=COMPLETED, run_count=1, completed_run_count=1
  - artifact_root="__REPLACED_AT_TEST_TIME__" (sentinel; test patches it)

`tests/fixtures/lab_runs/minimal_completed_run/runs/run-seed-42/run_report.json`:
  - run_id, health_score, critical_count, warning_count, anomalies list

## Step 2 — Create `tests/integration/lab_agent/test_golden_run_fixture.py`

Markers: `pytest.mark.integration`, `pytest.mark.e2e_golden`

### Fixture `golden_run_workspace`
1. Create session dir + lab_runs dir in tmp_path
2. Copy fixture tree to `tmp_path / "data" / "lab_runs" / "minimal-completed-run"`
3. Patch `artifact_root` in manifest to the copied path
4. Create lab session "session_golden_01"
5. Return tmp_path

### `test_golden_fixture_registers_successfully`
- Register via `RegisterSimulationResultWorkflow` with `lab_run_path = "data/lab_runs/minimal-completed-run"`
- Assert `res["status"] == "READY"`
- Assert `res["classification"] == "COMPLETE"`
- Assert `res["lab_run_id"] == "minimal-completed-run"`
- Assert `artifact_index.json` exists in registration dir
- Assert manifest schema matches `LabRunManifest` (parse with `LabRunManifest(**data)`)

### `test_golden_fixture_manifest_matches_schema`
- Load the original fixture file (no patching needed for schema check)
- Replace artifact_root sentinel with a real path
- Parse with `LabRunManifest(**data)` — assert no ValidationError

### `test_missing_fixture_blocks_registration`
- Point workflow at a non-existent path
- Assert `res["status"] == "BLOCKED"`
- Assert `"MISSING"` in `res["reason"]` or `res["classification"]`

### `test_corrupt_fixture_blocks_registration`
- Copy fixture, corrupt `lab_run_manifest.json` (write invalid JSON)
- Assert `res["status"] == "BLOCKED"`

## Files Changed
- `tests/fixtures/__init__.py` (new)
- `tests/fixtures/lab_runs/minimal_completed_run/lab_run_manifest.json` (new)
- `tests/fixtures/lab_runs/minimal_completed_run/runs/run-seed-42/run_report.json` (new)
- `tests/integration/lab_agent/test_golden_run_fixture.py` (new)
