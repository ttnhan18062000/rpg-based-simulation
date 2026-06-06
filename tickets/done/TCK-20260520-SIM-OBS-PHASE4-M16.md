# TCK-20260520-SIM-OBS-PHASE4-M16

## Title

Milestone 16 — Multi-Run Artifact Index

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Create an index and repository abstraction that manages sweeps, indexes individual run records, builds aggregate summaries, and exposes CLI commands to list and inspect sweeps.

## Scope

- Define the `RunIndexRecord` and `SweepSummary` models using Pydantic.
- Implement `RunSetArtifactRepository` to manage read/write of sweep artifacts: `run_set_manifest.json`, `run_index.jsonl`, and `sweep_summary.json`.
- Implement `MultiRunArtifactReader` or similar index builders to parse individual run manifests, `anomalies.json`, and `run_report.json`, generating `run_index.jsonl`.
- Implement `RunSetSummaryBuilder` to aggregate metric indexes, worst/best runs, and count anomaly rule IDs.
- Integrate the indexing and summary generation directly inside the `ScenarioSweeper.run_sweep()` flow upon completing a sweep.
- Add CLI commands: `rpg-observe list-sweeps` and `rpg-observe inspect-sweep <sweep_id>`.
- Add unit and integration tests covering the repository, index builder, summaries, and CLI interfaces.

## Out of Scope

- Baseline generation (Milestone 17).
- Dynamic comparisons across distinct scenario types.

## Acceptance Criteria

- `RunSetArtifactRepository` cleanly creates, reads, and lists sweeps under `data/run_sets/`.
- `run_index.jsonl` contains exactly one line per run, containing correct seed, health scores, and anomaly counts.
- Missing `run_report.json` or `anomalies.json` does not cause crashes (returns safe defaults or flags).
- `sweep_summary.json` computes average health, worst/best run IDs, and surfaces top anomaly rule IDs.
- `list-sweeps` lists all available sweeps, status, and run counts.
- `inspect-sweep` shows status, worst run, and anomaly distributions clearly.

## Related Tickets

- TCK-20260520-SIM-OBS-PHASE4-M15 (Completed)

## Related Docs

- `obs_sim_phase4.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/sweeper.py`
- `src/observability/reporting/run_set_repository.py` (NEW)
- `src/cli/entry.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- `RunSetArtifactRepository` will use `data/run_sets` as its default base directory.

## Test Summary

- `tests/unit/observability/test_run_set_repository.py`
- `tests/unit/observability/test_run_index_builder.py`
- `tests/integration/observability/test_multi_run_index_flow.py`

## Files Changed

- `src/observability/reporting/run_set_repository.py`
- `src/observability/sweeper.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_run_set_repository.py`
- `tests/unit/observability/test_run_index_builder.py`
- `tests/integration/observability/test_multi_run_index_flow.py`

## Completion Summary

- Implemented `RunIndexRecord`, `SweepSummary`, and `RunSetArtifactRepository` models and filesystem serializations.
- Integrated automated run index and sweep summary generation into sequential sweep execution flows.
- Registered CLI subcommands `list-sweeps` and `inspect-sweep` with beautifully detailed reports.
- Handled fallbacks resiliently when individual reports or anomaly logs are missing.
- Added comprehensive unit and integration test coverage. All tests pass successfully.

