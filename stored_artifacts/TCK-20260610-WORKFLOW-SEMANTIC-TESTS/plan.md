---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260610-WORKFLOW-SEMANTIC-TESTS
artifact_type: plan
tags: [workflow, semantic, tests]
---

# Plan: TCK-20260610-WORKFLOW-SEMANTIC-TESTS

## Strategy
Append semantic tests to the tail of each existing integration test file. No new files needed.

## New tests (7 total)

### PrepareSimulationExecution
- `test_command_references_generated_experiment_path`: read draft experiment.yaml path, assert it appears in command script
- `test_budget_estimate_run_count_reflects_seeds`: parse seeds from YAML, assert `storage_estimate.run_count == len(seeds)`

### RegisterSimulationResult
- `test_result_integrity_counts_reflect_manifest`: manifest with run_count=3/completed=2/failed=1 → report counts match
- `test_artifact_index_contains_manifest_entry`: artifact_index has entry with `lab_run_manifest.json` in relative_path

### InvestigateSimulationResult
- `test_investigation_healthy_run_zero_critical_issues`: new fixture with zero anomalies → `critical_issues == []`

### ProposeSimulationEnhancements
- `test_critical_issue_generates_known_issues_proposal`: CRITICAL HardLawViolationRule → KnownIssues patch with rule name reference
- `test_warning_only_issue_no_known_issues_patch`: WARNING-only issue_backlog → zero KnownIssues patches
