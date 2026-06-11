---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260610-WORKFLOW-SEMANTIC-TESTS
phase: done
date: 2026-06-10
tags: [workflow, semantic, tests]
---

# TCK-20260610-WORKFLOW-SEMANTIC-TESTS

## Title
Add semantic assertions to agentic workflow tests (PrepareExecution, Register, Investigate, Propose)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Most agentic workflow tests verify artifact creation and stage transitions, not semantic correctness. A workflow can write `execution_readiness_report.md` and pass even if the actual command would fail. Four workflows need semantic assertions added: PrepareSimulationExecution, RegisterSimulationResult, InvestigateSimulationResult, ProposeSimulationEnhancements.

## Scope
Add at least one semantic test per workflow:

**PrepareSimulationExecution:**
- Generated command references an existing scenario/experiment ID
- Command has expected output path set
- Command does not execute (forbidden action check)
- Budget report matches configured run count and tick count

**RegisterSimulationResult:**
- `completed_run_count` in manifest matches number of child run result files
- `failed_run_count` matches failed children
- Artifact index includes all required file types

**InvestigateSimulationResult:**
- Known anomaly fixture produces the expected anomaly type
- Known healthy fixture produces no false critical issue

**ProposeSimulationEnhancements:**
- Critical issue produces at least one proposal
- Low-confidence issue does not auto-propose a patch
- Proposed patch is not applied (only proposed)

## Out of Scope
- Changing workflow implementations
- Adding nightly semantic tests (these are unit/integration level)

## Acceptance Criteria
- [x] PrepareSimulationExecution: command references valid scenario; command does not execute
- [x] PrepareSimulationExecution: budget matches configuration
- [x] RegisterSimulationResult: completed + failed counts match actual children
- [x] RegisterSimulationResult: artifact index validated structurally
- [x] InvestigateSimulationResult: anomaly fixture → expected anomaly type (pre-existing test_investigation_light_depth)
- [x] InvestigateSimulationResult: healthy fixture → zero false critical issues
- [x] ProposeSimulationEnhancements: critical issue → proposal exists
- [x] ProposeSimulationEnhancements: low-confidence issue → no auto-patch
- [x] ProposeSimulationEnhancements: proposed patch not applied (pre-existing test_enhancement_no_direct_mutation)
- [x] Each workflow has at least one negative case (unsafe action forbidden)

## Related Tickets
- TCK-20260524-LAB-KNOWLEDGE (workflow implementation)
- TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE (golden fixture reusable here)
- TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT (related approval semantic tests)

## Related Docs
- `docs/guidelines/design_patterns.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`
- `tests/unit/lab_agent/` — per-workflow unit test files
- `src/lab/workflows/` — workflow implementations

## Assumptions / Open Questions
- Check whether separate per-workflow unit test files already exist under `tests/unit/lab_agent/` before writing new ones.
- The golden fixture from TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE is useful for Register and Investigate tests — implement that ticket first.

## Implementation Notes
Per-workflow integration test files already existed (`tests/integration/lab_agent/test_prepare_*`, etc.). Added semantic tests at the bottom of each. No new files needed — no unit test files were created.

`test_investigation_light_depth` already covered "known anomaly → expected type" (checks `critical_issues[0]["rule_name"] == "HardLawViolationRule"`), so only the healthy fixture test was missing for Investigate.

`test_enhancement_no_direct_mutation` already covered "proposed patch not applied".

The `mock_workspace_warning_only` fixture writes investigation artifacts directly (bypassing the full pipeline) because ProposeSimulationEnhancements reads `issue_backlog.json` independently of how it was produced.

## Test Summary
New tests added (7 total):
- Prepare: `test_command_references_generated_experiment_path`, `test_budget_estimate_run_count_reflects_seeds`
- Register: `test_result_integrity_counts_reflect_manifest`, `test_artifact_index_contains_manifest_entry`
- Investigate: `test_investigation_healthy_run_zero_critical_issues`
- Propose: `test_critical_issue_generates_known_issues_proposal`, `test_warning_only_issue_no_known_issues_patch`

50/50 lab_agent integration tests pass.

## Files Changed
- `tests/integration/lab_agent/test_prepare_simulation_execution_workflow.py`
- `tests/integration/lab_agent/test_register_simulation_result_workflow.py`
- `tests/integration/lab_agent/test_investigate_simulation_result_workflow.py`
- `tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`

## Completion Summary
Added 7 semantic tests across four workflow test files. Tests verify correctness of generated artifacts (command path, budget counts, integrity report counts, artifact index, investigation classification, proposal logic). 50/50 lab_agent integration tests pass.
