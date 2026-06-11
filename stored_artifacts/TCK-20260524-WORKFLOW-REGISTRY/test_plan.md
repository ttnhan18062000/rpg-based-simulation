---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260524-WORKFLOW-REGISTRY
artifact_type: test_plan
tags: [workflow, registry]
---

# Test Plan: Workflow Registry and Skill Contracts (M93)

We will implement isolated unit tests in `tests/unit/lab_agent/test_workflow_registry.py` using `pytest`.

## Test Cases

- **`test_scan_and_register_success`**: Correctly parses valid YAML frontmatter blocks from markdown files.
- **`test_workflow_fields_validation`**: Validates that all `WorkflowSkill` fields are mapped correctly and defaults are applied.
- **`test_unknown_workflow_rejected`**: Getting an unregistered workflow or skill throws a `ValueError`.
- **`test_allowed_forbidden_actions`**: Verifies that allowed actions and forbidden actions are correctly validated and populated in the registry.
- **`test_prepare_execution_forbids_command`**: Checks that the loaded `PrepareSimulationExecution` workflow strictly prohibits `execute_simulation_command` (or similar execution primitives).
- **`test_generate_setup_forbids_promotion`**: Checks that `GenerateSimulationSetup` strictly prohibits trusted promotion or direct rulebook modifications.
