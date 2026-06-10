# Investigation — TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE

## LabRunManifest schema (src/lab/schema.py:222)

Required fields:
- `lab_run_id: str` — alphanum pattern `^[a-zA-Z0-9_-]+$`
- `world_id, scenario_id, experiment_id: str`
- `status: str` — must be in VALID_LABRUN_STATUSES (COMPLETED, FAILED, PARTIAL, etc.)
- `started_at: str` — ISO 8601
- `ended_at: Optional[str]`
- `run_count, completed_run_count, failed_run_count: int`
- `artifact_root: str` — canonical path to run folder (absolute)
- `schema_versions: dict[str, str]`
- `budgets: dict[str, Any]`
- `storage_usage_mb: float`

## RegisterSimulationResultWorkflow reads (workflows.py:906-936)

1. Opens `lab_run_manifest.json` and parses via `LabRunManifest(**manifest_data)`
2. Checks `run_manifest.run_count` against actual child dirs under `runs/` that have `run_report.json`
3. Classification: COMPLETE if actual_count >= expected_count; PARTIAL if fewer; CORRUPTED if manifest invalid

## Child run structure

Workflow scans `resolved_run_path / "runs" / <child_dir> / "run_report.json"`.
Content of `run_report.json` is loaded in CompactSimulationData workflow but NOT required by
RegisterSimulationResultWorkflow — it only needs the file to exist for the count check.

## tests/fixtures/ directory

Does not exist — need to create with `__init__.py`.

## artifact_root handling

`artifact_root` must be an absolute path in the manifest but the fixture is stored in the repo.
The test must:
1. Copy `tests/fixtures/lab_runs/minimal_completed_run/` to `tmp_path / "data" / "lab_runs" / "minimal-completed-run"`
2. Patch `artifact_root` in the copied manifest to the actual tmp_path location

## Files to create

- `tests/fixtures/__init__.py`
- `tests/fixtures/lab_runs/minimal_completed_run/lab_run_manifest.json`
- `tests/fixtures/lab_runs/minimal_completed_run/runs/run-seed-42/run_report.json`
- `tests/integration/lab_agent/test_golden_run_fixture.py` (new test file)
