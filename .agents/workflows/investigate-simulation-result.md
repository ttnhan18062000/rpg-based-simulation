---
name: InvestigateSimulationResult
description: Analyze simulation logs, extract metrics, detect balance anomalies, and generate a comprehensive diagnostic report.
allowed_actions:
  - read_run_reports
  - read_scorecards
  - detect_anomalies
  - compare_with_historical_runs
  - write_investigation_report
forbidden_actions:
  - modify_specs
  - auto_apply_patches
input_schema:
  mode: "generic | specific"
  session_id: "string"
output_artifacts:
  - investigation/investigation_report.md
  - investigation/investigation_report.json
---

# InvestigateSimulationResult Workflow
Detailed steps for investigation...
