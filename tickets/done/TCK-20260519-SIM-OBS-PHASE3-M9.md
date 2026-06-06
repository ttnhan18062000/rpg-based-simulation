# TCK-20260519-SIM-OBS-PHASE3-M9

## Title

Milestone 9: Run Artifact Contract and Repository

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the unified directory and artifact layout contract for every simulation run under `data/runs/<run_id>/`, defining the standard `RunManifest` configuration and implementing the `RunArtifactRepository` class to manage read/write access to all post-run diagnostics, JSONL event databases, metrics, and report summaries.

## Scope

- **RunManifest Model**: Implement the standard Pydantic model for run manifests (incorporating run_id, scenario_name, scenario_type, seed, engine_version, status, schema version, and start/end metadata).
- **RunArtifactRepository Class**: Build `RunArtifactRepository` inside `src/observability/reporting/artifact_repository.py` to create run folders, resolve path contracts, open/parse existing runs, prevent accidental overwrites, and handle manifest status transitions (`CREATED` -> `RUNNING` -> `COMPLETED`/`FAILED`).
- **Observability Writer Integration**: Refactor the existing observability systems (`EventRecorder`, `HardLawMonitor`, and `RunReportGenerator`) to route their files via `RunArtifactRepository` paths.
- **Verification Suite**: Add unit tests for repository directories, manifest read/write operations, and schema version validation checks; write integration tests executing a sample run with correct contract files generated.

## Out of Scope

- Implementing the `MetricWindowRecorder` (Milestone 10) or central pipeline orchestrator (Milestone 11).
- CLI command endpoints or FastAPI read paths.
- ClickHouse or external storage adapters.

## Acceptance Criteria

- **Stable Standard Layout**: Running a simulation produces standard folder layout `data/runs/<run_id>/` with `run_manifest.json`, `simulation_events.jsonl`, `hard_law_violations.jsonl`, and final report paths.
- **Manifest Invariant Enforcement**: Manifest contains the exact `artifact_schema_version = "observability_artifact_v1"`, and reader rejects runs with unsupported schema versions with a clear error.
- **Accidental Overwrite Protection**: Repository refuses to overwrite existing directories unless `overwrite=True` is explicitly provided.
- **Parity Preservation**: Integration tests prove that enabling/disabling run folder generation preserves deterministic canonical state hashes perfectly.
- **100% Test Success**: Automated tests pass cleanly.

## Related Tickets

- `TCK-20260519-SIM-OBS-PHASE2` (Phase 2 Semantic Events and Post-Run Observatory)

## Related Docs

- `obs_sim_phase3.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/artifact_repository.py` [NEW]
- `src/observability/event_recorder.py`
- `src/observability/reporting/run_report.py`
- `src/engine/kernel.py`

## Assumptions / Open Questions

- We assume the default base path for runs will be `data/runs/` within the workspace.

## Implementation Notes

- Implemented full directory and path resolution contract in `RunArtifactRepository` with overwrite guards.
- Connected EventRecorder and HardLawMonitor to resolve paths from artifact repository directory.
- Refactored EventRecorder constructor alignment to resolve a bug in existing EventRecorder run_dir resolution.

## Test Summary

- `tests/unit/observability/test_run_artifact_repository.py` (5/5 Passed)
- `tests/integration/observability/test_run_artifact_flow.py` (2/2 Passed)
- Full observability suite (19/19 Passed)

## Files Changed

- `src/observability/reporting/artifact_repository.py`
- `src/engine/kernel.py`
- `obs_sim_phase3.md`

## Completion Summary

- Milestone 9 is 100% completed, hardened, and verified via extensive automated test coverage.
