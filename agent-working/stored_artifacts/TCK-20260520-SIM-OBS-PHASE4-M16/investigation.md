---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M16
artifact_type: investigation
tags: [sim, obs, phase4, m16]
---

# Investigation - Milestone 16: Multi-Run Artifact Index

## Findings

1. **Individual Run Report Parse Pattern**:
   - Each completed run folder (under `data/run_sets/<sweep_id>/runs/<run_id>/`) contains standard Phase 3 artifacts:
     - `run_manifest.json` (describes `run_id`, `seed`, `ticks_requested`, `ticks_completed`, `status`, `scenario_name`, `scenario_type`)
     - `run_report.json` if run was fully analyzed (contains `"health_score"`, `"critical_count"`, `"warning_count"`, `"hard_law_violation_count"`)
     - `anomalies.json` contains a JSON list of recorded anomalies, which we can load and parse to count rule ID frequencies.

2. **Error Resiliency**:
   - If a run fails, `run_report.json` or `anomalies.json` might not exist.
   - We must cleanly fallback to default counts (e.g. `health_score = 0.0` or `None` if failed, and count traces based on the recorded run manifest status).
   - This ensures missing reports do not crash the indexer!

3. **JSONL Index Format**:
   - `run_index.jsonl` contains line-separated JSON records.
   - We will write this cleanly line-by-line or as a single dump during the indexing phase of `ScenarioSweeper`.
