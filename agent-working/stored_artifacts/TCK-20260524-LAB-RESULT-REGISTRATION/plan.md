---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-RESULT-REGISTRATION
artifact_type: plan
tags: [lab, result, registration]
---

# Implementation Plan: RegisterSimulationResult Workflow (Milestone 98)

## Proposed Changes

### Lab Workflows

#### [MODIFY] [workflows.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/workflows.py)
We will implement the `RegisterSimulationResultWorkflow` class. 

##### Initialization
- Takes an optional `workspace_root` argument, defaulting to the absolute path of the project root directory.
- Initializes the `LabSessionStore` and `LabResultStore`.

##### Execution Flow (`run` method)
1. **Stage Transition**: Load active session manifest by `session_id`, set `manifest.current_stage = "REGISTRATION"`, and save session.
2. **Resolve Path**:
   - In `"generic"` mode, load `data/lab_sessions/{session_id}/execution_support/expected_output_paths.json` and read the `"output_directory"`.
   - In `"specific"` mode, read `request.specific_inputs.get("lab_run_path")`.
   - Run `safe_path_resolution(self.workspace_root, lab_run_path)` to get `resolved_run_path`.
3. **Status Classification**:
   - Check if directory exists. If not, classification is `MISSING`.
   - Check if `lab_run_manifest.json` exists and is parseable. If not, classification is `CORRUPTED`.
   - If manifest status is `"FAILED"`, classification is `FAILED`.
   - Iterate over expected child runs or check manifest's `run_count` vs. actual directory contents. If incomplete, classification is `PARTIAL`.
   - If complete and success, classification is `COMPLETE`.
4. **Link Run to Session**:
   - Append `resolved_run_path.name` to `manifest.linked_lab_runs` in the session manifest and save.
   - Write the resolved absolute run path string to `registration/actual_lab_run_path.txt`.
5. **Generate Indexes**:
   - Build `registration/artifact_index.json` containing lists of all files within `lab_run_path` mapped to their size and relative paths.
6. **Generate Reports**:
   - Write `registration/result_integrity_report.json` containing the status classification and counts.
   - Write `registration/result_integrity_report.md` presenting a premium, clean summary of the run success, child runs checklist, and next steps for metamorphic post-analysis.

### Verification Plan

#### Automated Tests
We will add `tests/integration/lab_agent/test_register_simulation_result_workflow.py` containing integration cases:
- Complete successful run
- Partial run (missing child directories)
- Missing manifest (MISSING/CORRUPTED)
- Traversal path rejection
