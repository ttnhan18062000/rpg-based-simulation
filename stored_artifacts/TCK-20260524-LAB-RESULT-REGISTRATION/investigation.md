# Investigation: RegisterSimulationResult Workflow (Milestone 98)

## 1. Analysis of `LabResultStore` and Completed Runs
Completed runs are expected to contain:
- `lab_run_manifest.json` (required): Loaded using `LabResultStore.load_lab_run_manifest()`.
- `lab_summary.json` (optional): Loaded using `LabResultStore.load_lab_summary()`.
- `runs/` (directory): Contains subdirectories for each individual seed run (e.g. `runs/run_0/run_report.json`).

## 2. Integrity and Completeness Classification
- **MISSING**: Directory does not exist on disk.
- **CORRUPTED**: Manifest does not exist or is malformed/fails Pydantic parse validation.
- **FAILED**: Manifest loaded but status is marked `"FAILED"`.
- **PARTIAL**: Manifest status is not failed, but the number of successful child directories in `runs/` is less than `manifest.run_count`.
- **COMPLETE**: Manifest status is successful and child run count matches `run_count`.

## 3. Registration Artifact Path Locations
Output artifacts will be saved relative to `data/lab_sessions/{session_id}/registration/`:
- `result_integrity_report.md`
- `result_integrity_report.json`
- `artifact_index.json`
- `actual_lab_run_path.txt`
