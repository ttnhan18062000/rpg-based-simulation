# Investigation Notes - Milestone 13: Evidence, Triage, and Report V2

We investigated the current structure of `src/observability/reporting/run_report.py` and `src/observability/anomaly/pipeline.py`.

## Core Findings

1. **Current Reporting Flow**:
   - `RunReportGenerator.generate()` parses the raw `anomalies.json` from the run directory, counts severities to calculate the health score, and writes `run_report.json` and `run_report.md`.
   - It also reconstructs flagged entity timelines from `simulation_events.jsonl` if `EntityTimelineStore` is not provided.

2. **Integration Plan**:
   - Create `src/observability/anomaly/triage.py` to host `EvidenceBuilder`, `TriageEngine`, and static `InvestigationHint` dictionaries.
   - Expand `AnalysisPipeline` to run `TriageEngine` on the final deduplicated anomaly list.
   - Update `RunReportGenerator.generate()` to accept `rule_results` and clustered anomalies, producing the new Report V2 tables and sections (statuses, skipped rules, clusters, evidence, hints).
