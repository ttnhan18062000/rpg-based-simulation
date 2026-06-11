---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M11
phase: done
date: 2026-05-19
tags: [sim, obs, phase3, m11]
---

# TCK-20260519-SIM-OBS-PHASE3-M11

## Title

Milestone 11: Analysis Pipeline Orchestrator

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Create the central orchestrator (`AnalysisPipeline`) that executes post-run analysis. The pipeline should load standard run context and artifacts (manifest, events, metrics, violations), run extensible analyzers via an analyzer registry in stable order, support partial run mode, collect anomalies, trigger report generation, update manifest status, and write results back to the run directory.

## Scope

- **AnalysisContext & AnalysisResult Models**: Define standard models for loading simulation contexts and capturing detailed execution outcomes.
- **AnalysisInputLoader**: Implement robust artifact parser for loading `run_manifest.json`, `simulation_events.jsonl`, `metric_windows.jsonl`, and `hard_law_violations.jsonl`.
- **AnalyzerRegistry**: Create registry interface for managing stable ordered executions of default and custom analyzers.
- **Initial Analyzers**:
  - `HardLawAnalyzer`: validates events for simulation invariants.
  - `BasicMovementAnalyzer`: checks navigation and combat stall loops.
  - `BasicEconomyAnalyzer`: checks node crowding issues.
  - `BasicQuestAnalyzer`: tracks quest stall metrics.
  - `BasicRuntimeAnalyzer`: scans metric windows for RSS growth and high latency pressure.
- **AnalysisPipeline**: Coordinate loading, analysis evaluation, reporting triggers, manifest status cuts, and JSONL output writes.
- **Partial-Run support**: Implement `--allow-partial` checks, blocking incomplete status by default and flagging outcomes accordingly.
- **Testing**: Complete unit and integration test suites validating execution flows and partial run checks.

## Out of Scope

- Real-time live analysis dashboard logic.
- Long-run anomaly clustering algorithms (Milestone 12).

## Acceptance Criteria

- **Pristine Run Analysis**: Pipeline successfully processes a completed run directory, compiling anomalies and executing reports.
- **Registry Order & Safety**: Registry runs analyzers in a stable order and handles individual analyzer exceptions gracefully.
- **Partial Run Validation**: Pipeline rejects running on incomplete simulations unless `allow_partial=True` is supplied.
- **Manifest Cut**: Manifest status is updated to `"ANALYZED"` on successful run completion.
- **100% Test Coverage Pass**: Dedicated unit and integration tests verify all loader, registry, and pipeline branches.

## Related Tickets

- `TCK-20260519-SIM-OBS-PHASE3-M10`

## Related Docs

- `obs_sim_phase3.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260519-SIM-OBS-PHASE3-M11/`

## Related Code Areas

- `src/observability/anomaly/pipeline.py`
- `tests/unit/observability/test_analysis_pipeline.py`
- `tests/integration/observability/test_analysis_pipeline_flow.py`

## Assumptions / Open Questions

- Missing optional files (e.g. `simulation_events.jsonl` or `hard_law_violations.jsonl`) should be tolerated gracefully without crashing.

## Implementation Notes

- Designed `AnalysisInputLoader` to robustly load files using `RunArtifactRepository`.
- Built `AnalyzerRegistry` with 5 pre-registered analyzers, executing in stable order and executing `HardLawViolationRule`, `NavigationStuckRule`, `CombatNeverEndsRule`, `ResourceNodeCrowdingRule`, and `QuestStalledRule`.
- Created `BasicRuntimeAnalyzer` checking metrics against CPU time average limits (>50ms), memory Max RSS limits (>2GB), and queue saturation (>80%).
- Integrated standard markdown generation and prepended `PARTIAL RUN ANALYSIS` warnings to the top of `run_report.md` when running in `allow_partial=True` on an incomplete/failed manifest.

## Test Summary

- Added 5 unit tests for loader validation, registry order preservation, error containment, and runtime metric warning rules.
- Added 2 integration tests verifying complete pipeline execution flows on both completed and partial runs.
- All 34/34 observability tests pass in 0.80 seconds.

## Files Changed

- `src/observability/anomaly/__init__.py` [NEW]
- `src/observability/anomaly/pipeline.py` [NEW]
- `tests/unit/observability/test_analysis_pipeline.py` [NEW]
- `tests/integration/observability/test_analysis_pipeline_flow.py` [NEW]

## Completion Summary

All loader, registry, default rules, pipeline orchestration, reporting triggers, and partial run safety cutoffs have been implemented under clean, robust patterns and are 100% covered by pytest unit and integration tests.
