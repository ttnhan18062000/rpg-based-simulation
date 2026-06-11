---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-OBSERVATORY-INTEGRATION
artifact_type: plan
tags: [lab, observatory, integration]
---

# Plan - Milestone 79 Observatory Integration

## Objective
Seamlessly integrate the Scenario Lab Orchestrator workflow with the simulation's Observatory suite. Every seed/sweep simulation run must trigger the full `AnalysisPipeline`, generating rich local reports (`run_report.json` and `run_report.md`). After completing the run sweeps, the orchestrator compiles them into a unified, aggregated `lab_summary.json` and `lab_summary.md` that acts as the single pane of glass for all diagnostics.

## Approach
1. **Analysis and Reporting Execution**:
   - For each simulation run in `ScenarioLabOrchestrator.run_lab`, execute `AnalysisPipeline().run(run_id, allow_partial=True)`.
   - Ensure the raw events, metrics, and reports are safely generated under `data/runs/{run_id}` before copytree moves them to the isolated lab run folder.
2. **Aggregation Engine**:
   - Locate the child `run_report.json` for each executed seed run in the isolated destination directory.
   - Load and parse each report. If a report is missing or corrupt, raise a descriptive warning, and represent the run status as failed/degraded without silent swallowing.
   - Aggregate statistics across all successfully analyzed runs:
     - Average health score.
     - Total critical counts (hard law violations).
     - Total warning counts.
     - Best/worst run IDs (by health score).
     - Top anomalies frequency across all sweeps.
3. **Lab Summary Generation**:
   - Write `lab_summary.json` containing the required fields: `lab_run_id`, `world_id`, `scenario_id`, `experiment_id`, `status`, `total_runs`, `completed_runs`, `failed_runs`, `average_health_score`, `critical_count_total`, `warning_count_total`, `top_anomalies`, `worst_run_id`, `best_run_id`, `storage_usage_mb`.
   - Write a beautifully styled markdown executive report `lab_summary.md` featuring HSL tailored badges, summary scorecard table, top triggered anomalies, and links/references to individual run folders.
4. **Safety & Robustness**:
   - If all sweeps fail or no runs completed, mark overall status as `FAILED`.
   - Set up custom exceptions for missing run reports.

## Files to Modify
- `src/lab/orchestrator.py`

## Files to Create
- `tests/integration/lab/test_lab_observatory_integration.py`
