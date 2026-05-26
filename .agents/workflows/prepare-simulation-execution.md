---
name: PrepareSimulationExecution
description: Prepare everything required for the user to manually trigger the simulation sweep.
allowed_actions:
  - resolve_specs
  - run_validators
  - estimate_budgets
  - generate_execution_command
forbidden_actions:
  - execute_simulation_command
  - run_simulation_directly
input_schema:
  mode: "generic | specific"
  target: "string (optional)"
  profile: "string"
output_artifacts:
  - execution_support/execution_readiness_report.md
  - execution_support/execution_readiness_report.json
  - execution_support/execution_command.sh
  - execution_support/expected_output_paths.json
  - execution_support/budget_report.json
---

# PrepareSimulationExecution Workflow
Detailed steps for manual execution preparation...
