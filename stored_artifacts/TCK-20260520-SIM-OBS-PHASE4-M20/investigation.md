# Investigation - Scenario-Level Report and CI Gate

## Code & Data Dependency Scanning
- Sweeper produces `run_set_manifest.json` and a series of run folders inside `data/run_sets/<sweep_id>/runs/<run_id>/`.
- `RunSetArtifactRepository` indexes completed runs into `run_index.jsonl` and `sweep_summary.json`.
- `BaselineComparator.compare_sweep` reads `run_index.jsonl` and computes outlier runs and drift statistics, saving the outcomes in `sweep_baseline_comparison.json`.
- We will design `SweepReportGenerator` to build on top of these pre-computed results. If a comparison does not exist or needs to be refreshed, we can directly invoke `BaselineComparator.compare_sweep` programmatically to guarantee consistency and up-to-date data.

## Report Section Plan (All 12 Required Sections)
1. **Executive Summary**: Clear status banner, counts, and high-level evaluation statement.
2. **Sweep Metadata**: IDs, scenario info, run counts, ticks, timestamps.
3. **Run Distribution**: Distributions of completed/failed status.
4. **Baseline Summary**: Baseline ID, source sweep details, active metrics.
5. **Comparison Result**: High-level gating status.
6. **Outlier Seeds**: List of runs detected as statistical outliers.
7. **Most Common Anomalies**: Frequency mapping of rule violations.
8. **Performance Drift**: Detailed drift direction and magnitude for tick computation times.
9. **Memory Drift**: RSS memory consumption metrics and shifts.
10. **Health Score Distribution**: Shifting direction of health profiles compared to baseline.
11. **Failed Expectations**: Specific metric expectations that failed comparison checks.
12. **Recommended Investigation Points**: Actionable diagnostic suggestions based on specific failures (e.g. debugging a specific outlier seed).
