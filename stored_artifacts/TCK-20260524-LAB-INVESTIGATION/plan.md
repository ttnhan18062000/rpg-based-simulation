# Implementation Plan - Milestone 100 Investigation Workflow

## Goal Description
Implement the `InvestigateSimulationResultWorkflow` to dynamically ingest and analyze compacted and indexed simulation results, deriving structured bug backlogs, missing coverage areas, and actionable balance/liveness recommendations without memory or token bloat.

## User Review Required
No major breaking changes are introduced. The workflow strictly adheres to the Phase 14 specifications.

## Proposed Changes

### RPG Engine Lab Workflows

#### [MODIFY] [workflows.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/workflows.py)
- Create and implement `class InvestigateSimulationResultWorkflow`:
  - **`__init__(workspace_root)`**: Sets up session store and workspace paths.
  - **`run(session_id, request)`**:
    1. Loads the session manifest and transitions to the `INVESTIGATION` stage.
    2. Resolves the run path from either specific inputs or generic registration markers (`actual_lab_run_path.txt`).
    3. Validates path-traversal safety via `safe_path_resolution`.
    4. Validates that compaction files exist in the session's `registration/` stage directory.
    5. Dispatches based on `analysis_depth`:
       - **Light**: Loads and inspects the top 3 issues from the `issue_index.json`.
       - **Standard**: Loads `issue_index.json` (top 10), `evidence_pack_index.json`, and `signal_coverage.json`.
       - **Deep**: Loads standard data plus selective child report lookups (`run_report.json`) based on specified `focus_issues` or tick windows, avoiding heavy raw timeline processing.
    6. Generates 6 highly structured artifacts in the session's `investigation/` stage folder:
       - `investigation_report.md` (premium markdown with 13 standard sections)
       - `investigation_report.json`
       - `issue_backlog.json`
       - `missing_signals.json`
       - `insight_candidates.json`
       - `next_experiment_suggestions.json`
    7. Returns `{"status": "READY", "report_path": "..."}`.

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
- Import and export `InvestigateSimulationResultWorkflow` in `__all__`.

### Integration Tests

#### [NEW] [test_investigate_simulation_result_workflow.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/lab_agent/test_investigate_simulation_result_workflow.py)
- Write tests confirming:
  - Light investigation processes only the top 3 issues.
  - Standard investigation loads signal coverage and top 10 issues.
  - Deep investigation reads focused entities/windows.
  - All 6 output reports are created successfully.
  - Path traversal attempts are safely caught and blocked.
  - Invalid or non-completed states are cleanly rejected.

## Verification Plan

### Automated Tests
- Run `pytest tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`.
- Run `graphify update .` to keep the codebase knowledge graph synchronized.
