---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-COMPACT-SIMULATION
artifact_type: investigation
tags: [lab, compact, simulation]
---

# Investigation Report - M99 CompactSimulationData Workflow

## 1. Context Analysis & System Design

To prevent heavy token bloat in downstream LLM calls (e.g. `InvestigateSimulationResultWorkflow`), the system requires compact summaries of simulation run diagnostics rather than importing massive raw event files (`simulation_events.jsonl` which can easily exceed tens of megabytes).

### Schema Design of Compaction Artifacts

1. **`compact_summary.json`**:
   - **`lab_run_id`**: Identifies the simulation run.
   - **`summary_stats`**: Aggregated stats: run count, completed count, failed count, total anomalies count, average health score.
   - **`world_id` / `scenario_id` / `experiment_id`**: Linked configurations.
   - **`top_issues`**: Top issue types and their counts.
   - **`top_entity_hotspots`**: Top entity IDs involved in anomalies.

2. **`issue_index.json`**:
   - Map or array of issues with:
     - `rule_name` (string)
     - `severity` (string)
     - `count` (int)
     - `tick_range` (list: `[min_tick, max_tick]`)
     - `affected_entities` (list of int)
     - `affected_runs` (list of str)
     - `short_evidence_summaries` (list of str - capped by `top_n`)

3. **`evidence_pack_index.json`**:
   - Array of objects corresponding to child runs:
     - `run_id` (str)
     - `status` (str - e.g. "COMPLETE", "FAILED")
     - `health_score` (float)
     - `anomaly_counts` (dict of `rule_name` -> int)
     - `total_anomalies` (int)
     - `has_critical_violations` (bool)
     - `report_file_path` (str - e.g. `"runs/run_0/run_report.json"`)

4. **`metric_digest.json`**:
   - Aggregated quantitative signals:
     - `avg_health_score` (float)
     - `min_health_score` (float)
     - `max_health_score` (float)
     - `total_criticals` (int)
     - `total_warnings` (int)
     - `total_errors` (int)
     - `tick_max` (int)

5. **`entity_hotspots.json`**:
   - Grouping anomalies by entity ID:
     - `entity_id` (int)
     - `anomaly_count` (int)
     - `issue_types` (list of str)
     - `affected_runs` (list of str)

6. **`signal_coverage.json`**:
   - Map of gameplay domains to coverage status:
     - `domain`: `kernel`, `movement`, `strategy`, `combat`, `resource`
     - `total_anomalies` (int)
     - `covered` (bool)
     - `focus_status` (str: `"HIGH_FOCUS"`, `"FOCUS"`, `"NONE"`)
     - `rules_triggered` (list of str)

---

## 2. Guardrails & Path Escapes

- Strict traversal checks via `safe_path_resolution()` will be performed on incoming `lab_run_path`.
- Path traversal escapes (such as `../../etc`) will result in blocking registration stages and throwing explicit ValueError / returning `BLOCKED`.
- Verify `simulation_events.jsonl` or other heavy lines are strictly excluded from the output JSON files to guarantee light token footprints.
