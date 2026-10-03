---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M11
artifact_type: investigation
tags: [sim, obs, phase3, m11]
---

# Investigation - Milestone 11: Analysis Pipeline Orchestrator

## Current Capabilities
- `PostRunAnomalyAnalyzer` is already implemented and executes rules (`HardLawViolationRule`, `NavigationStuckRule`, `QuestStalledRule`, `CombatNeverEndsRule`, `ResourceNodeCrowdingRule`) against a loaded list of `SimulationEvent`.
- `RunReportGenerator` generates markdown and JSON summaries based on the run folder and anomalies files.
- `RunArtifactRepository` already manages loading and updating the manifest.

## Gap Analysis
- There is currently no unified loader that loads all 4 run files (`run_manifest.json`, `simulation_events.jsonl`, `metric_windows.jsonl`, `hard_law_violations.jsonl`) cleanly, validates schema versions, and checks partial-run status.
- There is no registry for custom, domain-specific analyzers.
- No analyzer exists that operates on `metric_windows.jsonl` to detect runtime/pressure anomalies (e.g., memory RSS leaks, compute latency spikes, queue bottlenecks).
- There is no single central `AnalysisPipeline.run(run_id)` command that ties all these steps together.
