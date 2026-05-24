---
name: RegisterSimulationResult
description: Register completed simulation run outputs into a new lab run folder with diagnostic indexes.
allowed_actions:
  - read_simulation_outputs
  - validate_schema
  - move_to_lab_runs
  - rebuild_lab_index
  - generate_diagnostic_scorecard
forbidden_actions:
  - alter_original_logs
  - delete_raw_outputs
input_schema:
  mode: "generic | specific"
  session_id: "string"
output_artifacts:
  - registration/lab_run_manifest.json
  - registration/lab_summary.json
  - registration/diagnostic_scorecard.md
---

# RegisterSimulationResult Workflow
Detailed steps for result registration...
