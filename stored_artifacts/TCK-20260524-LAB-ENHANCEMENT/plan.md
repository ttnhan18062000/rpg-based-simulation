# Implementation Plan - Milestone 101 Enhancement Proposals

## Goal Description
Implement the `ProposeSimulationEnhancementsWorkflow` to ingest the diagnostic results of M100 and construct actionable config patch proposals, draft scenarios, and change risk matrices without mutating target files directly.

## User Review Required
No breaking changes. The workflow strictly adheres to the Phase 14 specifications.

## Proposed Changes

### RPG Engine Lab Workflows

#### [MODIFY] [workflows.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/workflows.py)
- Create and implement `class ProposeSimulationEnhancementsWorkflow`:
  - **`__init__(workspace_root)`**: Sets up session store and workspace paths.
  - **`run(session_id, request)`**:
    1. Loads the session manifest and transitions to the `ENHANCEMENT` stage.
    2. Resolves target paths and validates safe sandbox limits via `safe_path_resolution`.
    3. Validates that the active session has completed the `INVESTIGATION` stage and contains `investigation_report.json`.
    4. Dispatches inputs:
       - **Generic**: Ingests `latest_investigation_report` from `investigation/` stage folder.
       - **Specific**: Uses specified `investigation_report_path`.
    5. Reads `investigation_report.json`, `issue_backlog.json`, and `missing_signals.json`.
    6. Validates change types against `allowed_change_types` and `forbidden_change_types` (raising ValueError if a forbidden change type is requested).
    7. Generates structured patch records (using YAML format for each patch file).
       - Validates that every critical rule update contains a non-empty list in the `evidence` field.
       - Rejects unsupported patch operations (only `add`, `modify`, `replace` are permitted).
       - Blocks direct modification of trusted spec files (trusted files must never be directly overwritten or mutated).
    8. Writes the 5 output artifacts in the session's `enhancement/` stage folder:
       - `enhancement/enhancement_plan.md`
       - `enhancement/proposed_patches/` (directory containing individual `.yaml` patch files)
       - `enhancement/next_experiment_drafts/` (directory containing `.yaml` scenario drafts)
       - `enhancement/insight_candidates.json`
       - `enhancement/change_risk_report.json`
    9. Returns `{"status": "READY", "report_path": "..."}`.

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
- Import and export `ProposeSimulationEnhancementsWorkflow` in `__all__`.

### Integration Tests

#### [NEW] [test_propose_simulation_enhancements_workflow.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py)
- Write tests verifying:
  - Enhancement plan and proposed patches are successfully created under the stage directory.
  - Forbidden change types are strictly respected and raise validation/blocking errors.
  - Every patch contains a detailed evidence reference list.
  - Patches are NOT automatically applied to active repository specs.
  - Invalid patch operations or evidence-free updates are cleanly rejected.

## Verification Plan

### Automated Tests
- Run `pytest tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`.
- Run `graphify update .` to keep the codebase knowledge graph synchronized.
