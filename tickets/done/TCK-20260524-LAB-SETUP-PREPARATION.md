# TCK-20260524-LAB-SETUP-PREPARATION

## Title

Implement Setup Generation (M96) and Execution Preparation (M97) Workflows

## Status

DONE

## Request Summary

Implement the core logic for `GenerateSimulationSetup` (M96) and `PrepareSimulationExecution` (M97) workflows in `src/lab/workflows.py` to support dynamic, human-gated simulation environments, along with comprehensive integration test suites.

## Scope

- Implement `GenerateSimulationSetupWorkflow` in `src/lab/workflows.py` [x]
- Implement `PrepareSimulationExecutionWorkflow` in `src/lab/workflows.py` [x]
- Create integration test suites:
  - `tests/integration/lab_agent/test_generate_simulation_setup_workflow.py` [x]
  - `tests/integration/lab_agent/test_prepare_simulation_execution_workflow.py` [x]

## Out of Scope

- Results registration and sweep post-analysis (M98 - M102).

## Acceptance Criteria

- `GenerateSimulationSetupWorkflow` successfully produces Pydantic-valid draft files and full review packs. [x]
- `PrepareSimulationExecutionWorkflow` prepares accurate `execution_command.sh` scripts for valid setups and blocks invalid ones generating blocked reports. [x]
- Non-promotion of draft specs and non-execution of engine simulation rules are fully enforced. [x]
- Comprehensive integration tests pass successfully with 100% success rate. [x]

## Related Tickets

- `TCK-20260524-LAB-REQUEST-CONTEXT` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/workflows.py`
- `tests/integration/lab_agent/test_generate_simulation_setup_workflow.py`
- `tests/integration/lab_agent/test_prepare_simulation_execution_workflow.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Designed and implemented unified heuristic mapping for generic mode setups.
- Safe absolute path anchoring prevents path traversal inside base directory checks.

## Test Summary

- Run all integration tests: 7 tests passed successfully.
- Run all unit tests: 117 tests passed successfully.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/workflows.py`
- `tests/integration/lab_agent/test_generate_simulation_setup_workflow.py`
- `tests/integration/lab_agent/test_prepare_simulation_execution_workflow.py`

## Completion Summary

- Implemented safe, isolated setup generation (M96) and verification launcher scripting (M97) workflows under `src/lab/workflows.py` with 100% test coverage. No side-effect engines are triggered.
