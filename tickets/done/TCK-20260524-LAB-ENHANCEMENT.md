# TCK-20260524-LAB-ENHANCEMENT

## Title

Implement ProposeSimulationEnhancements Workflow (Milestone 101)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the `ProposeSimulationEnhancementsWorkflow` class in `src/lab/workflows.py` to ingest an investigation report and construct actionable enhancement proposals, next experiment drafts, change risk reports, and structured patches without automatically applying them.

## Scope

- Create `ProposeSimulationEnhancementsWorkflow` class in `src/lab/workflows.py`
  - Ingest the investigation reports and backlogs.
  - Generate a structured patch YAML format supporting operations like `add`, `modify`, `replace`.
  - Validate that patch types do not violate `forbidden_change_types` (e.g. EngineCode).
  - Enforce critical rules:
    - Patches cannot modify trusted specs directly.
    - Patches must not use unsupported operations.
    - Critical rule updates must contain an evidence reference.
  - Generate the 5 output artifacts in the `enhancement/` session subdirectory:
    1. `enhancement_plan.md`
    2. `proposed_patches/` (directory containing structured yaml patch files)
    3. `next_experiment_drafts/` (directory containing draft configs)
    4. `insight_candidates.json`
    5. `change_risk_report.json`
- Apply safe path resolution and sandbox guards to block traversal breakouts.
- Export `ProposeSimulationEnhancementsWorkflow` in `src/lab/__init__.py`.
- Write integration tests inside `tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`.

## Out of Scope

- Implementing the final `UpdateSimulationKnowledgeWorkflow` (M102).
- Automatically executing bash operations to apply the patches.

## Acceptance Criteria

- Workflow returns `READY` and generates the 5 required output artifacts under `enhancement/` session subdirectory.
- Forbidden change types (e.g. `EngineCode`) are strictly respected and raise validation/blocking errors.
- Structured patches contain a detailed `evidence` field.
- Temporary or invalid patch operations are correctly rejected.
- Paths are validated with `safe_path_resolution()` to prevent sandbox escapes.

## Related Tickets

- `TCK-20260524-LAB-INVESTIGATION` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260524-LAB-INVESTIGATION/`

## Related Code Areas

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added dynamic validation checking that all patch operations match allowed sets (`add`, `modify`, `replace`).
- Enforced strict sandboxed output staging where patch files are proposed but never applied directly to active workspace configs.

## Test Summary

- Run `pytest tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`. All 5 tests passed successfully in 0.32 seconds.
  - Verifies that the 5 output enhancement files are successfully created under the stage directory.
  - Verifies that forbidden change types (KnownIssues, EngineCode) trigger ValueError.
  - Verifies that target specification files are not mutated directly.
  - Verifies that unsupported operations (e.g., delete) are blocked.
  - Verifies that critical rule patches with missing evidence references raise ValueError.

## Files Changed

- `src/lab/workflows.py`
- `src/lab/__init__.py`
- `tests/integration/lab_agent/test_propose_simulation_enhancements_workflow.py`

## Completion Summary

- Milestone 101 (M101) is fully complete. All artifacts are verified and compiled.
