# TCK-20260524-WORKFLOW-REGISTRY

## Title

Implement Workflow Registry and Skill Contracts (M93)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a dynamic Markdown frontmatter parsing engine `WorkflowRegistry` and validated `WorkflowSkill` contracts that load specifications directly from `.agents/workflows/` and `.agents/skills/`.

## Scope

- Create Pydantic model `WorkflowSkill` to represent dynamic workflow and skill contracts.
- Implement `WorkflowRegistry` class to:
  - Dynamically scan `.agents/workflows/` and `.agents/skills/` folders.
  - Parse YAML frontmatter metadata from Markdown spec files.
  - Expose validated contract checks (allowed actions, forbidden actions, output artifacts).
- Create `.agents/workflows/` markdown files for Phase 14 workflows to ensure the system starts with complete runtime specs.
- Implement unit tests in `tests/unit/lab_agent/test_workflow_registry.py`.

## Out of Scope

- Core workflow execution logic (M96 - M102) details.
- Context Pack builder (M95).
- CLI implementation.

## Acceptance Criteria

- `WorkflowRegistry` correctly parses dynamic YAML frontmatter from `.agents/workflows/` files.
- `WorkflowSkill` correctly exposes all contract attributes (name, purpose/description, input_schema, allowed_actions, forbidden_actions, output_artifacts, approval_required, context_budget, failure_behavior).
- Checks for unknown workflows or prohibited commands fail appropriately.
- 100% passing tests for the dynamic workflow registry.

## Related Tickets

- `TCK-20260524-LAB-SESSION-MODEL` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/registry.py`
- `tests/unit/lab_agent/test_workflow_registry.py`

## Assumptions / Open Questions

- We assume YAML frontmatter is enclosed between `---` boundaries at the start of Markdown files.

## Implementation Notes

- Use python's `pyyaml` library (already integrated in the project via `import yaml`) to parse parsed frontmatter substrings.

## Test Summary

- Automated unit tests implemented in `tests/unit/lab_agent/test_workflow_registry.py`
- 4 unit test cases passing perfectly covering dummy scans, model defaults, validation rules, and action prohibition validation on actual workflows.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/registry.py`
- `tests/unit/lab_agent/test_workflow_registry.py`
- `.agents/workflows/generate-simulation-setup.md`
- `.agents/workflows/prepare-simulation-execution.md`
- `.agents/workflows/register-simulation-result.md`
- `.agents/workflows/compact-simulation-result.md`
- `.agents/workflows/investigate-simulation-result.md`
- `.agents/workflows/propose-simulation-enhancements.md`
- `.agents/workflows/update-knowledge-store.md`

## Completion Summary

- Implemented standard Phase 14 `WorkflowSkill` dynamic contract model using robust Pydantic schemas.
- Implemented file-based `WorkflowRegistry` ensuring robust scanner extraction of frontmatter YAML configuration data.
- Automatically populated all Phase 14 standard workflow markdown specifications within the native `.agents/workflows/` folder.
- Verified action constraints (e.g. `PrepareSimulationExecution` forbids `execute_simulation_command` and `GenerateSimulationSetup` forbids `promote_trusted_specs`) via automated unit test executions.

