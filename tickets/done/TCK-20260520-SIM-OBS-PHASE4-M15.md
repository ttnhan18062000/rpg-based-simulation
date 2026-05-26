# TCK-20260520-SIM-OBS-PHASE4-M15

## Title

Milestone 15 — Scenario Run Matrix and Sweeper

## Status

DONE

## Request Summary

Build a working scenario sweeper that runs the same scenario across multiple seeds and/or configurations sequentially, collecting standard Phase 3 run artifacts and producing a structured Run Set Manifest.

## Scope

- Define `ScenarioSweepConfig` and `ScenarioRunSpec` configuration models.
- Implement `ScenarioSweeper` executing multiple sequential runs.
- Generate standard `RunSetManifest` documenting execution timestamps, seed mapping, and completion statuses.
- Support robust failure handling (log and continue vs. stop-on-first-critical).
- Extend CLI `rpg-observe sweep <sweep_config.json>` command.
- Write full unit and integration test suite coverage.

## Out of Scope

- Multi-run index repository logic (staged for Milestone 16).
- Parallel run execution.
- Auto-fixing or dynamic stat tuning.

## Acceptance Criteria

- Valid sweep config loads and parses correctly.
- Invalid configurations (e.g. empty seeds list, non-positive ticks) are rejected with clear errors.
- Runs execute sequentially, generating isolated output files matching seed settings.
- Sweep manifests are cleanly saved under `data/run_sets/<sweep_id>/run_set_manifest.json`.
- A single seed failure records the error without corrupting or losing prior successful seeds' data.

## Related Tickets

- TCK-20260519-SIM-OBS-PHASE3-M13 (Done)

## Related Docs

- `obs_sim_phase4.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/sweeper.py` (NEW)
- `src/cli/entry.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Use the existing `RunArtifactRepository` to allocate new `run_id` spaces under standard locations.
- The default output directory for run sets is `data/run_sets/`.

## Test Summary

- `tests/unit/observability/test_sweep_config.py`
- `tests/unit/observability/test_scenario_sweeper.py`
- `tests/integration/observability/test_sweep_execution_flow.py`

## Files Changed

- `src/observability/sweeper.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_sweep_config.py`
- `tests/unit/observability/test_scenario_sweeper.py`
- `tests/integration/observability/test_sweep_execution_flow.py`

## Completion Summary

- Implemented `ScenarioSweepConfig`, `ScenarioRunSpec`, and `RunSetManifest` configuration models.
- Implemented `ScenarioSweeper` executing sequential simulations.
- Registered CLI subcommand `rpg-observe sweep`.
- Added complete suite of unit and integration tests covering all requirements. All tests pass successfully.

