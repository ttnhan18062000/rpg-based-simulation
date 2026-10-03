---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M11
artifact_type: plan
tags: [sim, obs, phase3, m11]
---

# Implementation Plan - Milestone 11: Analysis Pipeline Orchestrator

## Proposed Architecture

1. **`AnalysisContext` and `AnalysisResult`**:
   - `AnalysisContext` will act as a unified, immutable input container for all loaded run artifacts.
   - `AnalysisResult` will act as a structured output containing execution status, anomaly counts, output paths, and any loader/analyzer errors.

2. **`AnalysisInputLoader`**:
   - Uses `RunArtifactRepository` to parse and load:
     - `run_manifest.json` (Raises `FileNotFoundError` if missing).
     - `simulation_events.jsonl` (Gracefully handles empty or missing files).
     - `metric_windows.jsonl` (Gracefully handles empty or missing files).
     - `hard_law_violations.jsonl` (Gracefully handles empty or missing files).
   - Validates that the manifest status is `"COMPLETED"` unless `allow_partial=True` is provided. If not `"COMPLETED"` and `allow_partial` is False, raises a `ValueError`.

3. **`AnalyzerRegistry` and `BaseAnalyzer`**:
   - `BaseAnalyzer` is an interface with `analyze(self, context: AnalysisContext) -> List[Anomaly]`.
   - `AnalyzerRegistry` maintains a list of analyzers in stable registration order.
   - Catches individual analyzer execution exceptions, adding them to the result's errors block instead of failing the pipeline.

4. **Default Analyzers**:
   - `HardLawAnalyzer`: Executes `HardLawViolationRule` against events.
   - `BasicMovementAnalyzer`: Executes `NavigationStuckRule` and `CombatNeverEndsRule` against events.
   - `BasicEconomyAnalyzer`: Executes `ResourceNodeCrowdingRule` against events.
   - `BasicQuestAnalyzer`: Executes `QuestStalledRule` against events.
   - `BasicRuntimeAnalyzer`: Scans `metric_windows` for high CPU usage (`tick_compute_ms_avg > 50.0`), memory leaks (`memory_rss_bytes_max > 2 * 1024 * 1024 * 1024`), or queue bottlenecks (`queue_utilization_avg > 0.8`), raising warning anomalies.

5. **`AnalysisPipeline`**:
   - Triggers `AnalysisInputLoader` to parse the run directory.
   - Executes registered analyzers.
   - Combines anomalies and writes `anomalies.json` and `anomaly_summary.md` back to the run directory.
   - Triggers `RunReportGenerator.generate(...)` to output `run_report.json` and `run_report.md`.
   - Updates run manifest status to `"ANALYZED"`.
   - Returns a structured `AnalysisResult`.
