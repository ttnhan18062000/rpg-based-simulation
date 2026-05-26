# Investigation - Milestone 79 Observatory Integration

## Findings
- **Analysis Pipeline Trigger**: The current orchestrator calls:
  ```python
  if experiment_spec.analysis.run_post_analysis:
      try:
          from src.observability.anomaly.pipeline import AnalysisPipeline
          pipeline = AnalysisPipeline()
          pipeline.run(run_id, allow_partial=True)
      except Exception as ap_err:
          logger.error(f"Failed running AnalysisPipeline for run {run_id}: {ap_err}")
  ```
  However, this invocation occurs *before* copying the run artifacts from `temp_run_dir` to `target_run_dir`. This is actually correct because the pipeline writes `anomalies.json`, `run_report.json`, and `run_report.md` directly into the `temp_run_dir` (`data/runs/{run_id}`). When `shutil.copytree` runs right after, it carries all these files into the isolated lab run repository!
- **Data Aggregation**:
  - We can aggregate these artifacts after completing all runs by traversing the destination subdirectory `runs/`.
  - Let's check `LabRunRepository` to see how paths are resolved. Each child run is copied to `run_dir / "runs" / run_id`.
  - Inside `target_run_dir = run_dir / "runs" / run_id`, there should be `run_report.json`.
  - We will load `run_report.json` using `json.load`.
  - Expected fields inside `run_report.json`:
    - `health_score`: float
    - `critical_count` / `hard_law_violations_count`: int
    - `warning_count` / `warnings_count`: int
    - `anomalies`: List[Dict]
- **Robustness**:
  - We need to handle cases where `run_report.json` is missing or corrupted.
  - If a child run failed, `AnalysisPipeline` might not generate the report, or it might generate a partial one. If a report is missing, we must gracefully log it and increment the failed/missing count.
  - If all child runs fail (e.g. `completed_count == 0`), the status must be marked as `FAILED`.
