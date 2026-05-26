# Plan - Lab Result Store (Milestone 80)

We will implement `LabResultStore` in a dedicated file `src/lab/store.py` to retrieve, index, and load laboratory artifacts securely.

## Proposed Component Layout

`LabResultStore` will reside in `src/lab/store.py`. It will wrap filesystem access to `data/lab_runs/` (or a customized base directory) and operate on top of `LabRunManifest` from `src/lab/schema.py`.

### Safe Path Traversal Resolution
All file access will be gated by a strict `_resolve_path(self, lab_run_id: str, subpath: str | Path | None = None) -> Path` helper that resolves absolute paths and enforces that the target is strictly inside the configured `lab_runs_dir` base directory, raising `PermissionError` on violations.

### Public Methods
1. `list_lab_runs() -> list[str]`: Scans the base directory for folders containing `lab_run_manifest.json` and lists their IDs sorted.
2. `load_lab_run_manifest(lab_run_id: str) -> LabRunManifest`: Reads and parses `lab_run_manifest.json` under the safe run folder.
3. `load_lab_summary(lab_run_id: str) -> dict`: Reads `lab_summary.json` from the run's root (or `analysis/` if applicable, but our orchestrator outputs `lab_summary.json` to the root `run_dir` for direct access).
4. `load_run_report(lab_run_id: str, run_id: str) -> dict`: Reads `run_report.json` for a specific child run under `runs/{run_id}/run_report.json`.
5. `load_validation_reports(lab_run_id: str) -> dict`: Compiles a dict loading both scenario and experiment validation reports.
6. `load_compile_report(lab_run_id: str) -> dict`: Reads the `world_compile_report.json` under `world/world_compile_report.json`.
7. `rebuild_index()`: Scans all directories, parses manifests, and compiles the central `lab_index.json`.
8. `get_index() -> dict`: Reads the central `lab_index.json`, rebuilding it if missing.

## Verification Plan

### Automated Unit Tests
A new suite `tests/unit/lab/test_lab_result_store.py` will verify:
- Safe path resolution and path traversal rejection.
- Correct listing of lab runs.
- Loading of manifests, summaries, compile reports, and validation reports.
- Graceful handling of missing summaries or files.
- Index rebuilding with precise requested keys.
