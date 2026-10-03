---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-COGNITION-DECISION-TRACE-JOIN
phase: open
date: 2026-08-22
tags: [observability, cognition, schema, calibration]
---

# TCK-20260822-COGNITION-DECISION-TRACE-JOIN

## Title
Make cognition features queryable via DuckDB, joined against decision_trace for calibration input

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The idea doc proposes joining cognition_features against decision_trace.jsonl on (entity_id, run_id) as calibration/tuning input, using a "switch_margin" field. Investigation found decision_trace.jsonl entries carry no run_id field at all today (confirmed against both the code and docs/observability/decision_trace_contract.md), so the proposed JOIN cannot work as written without an explicit schema decision, and that "switch_margin" is not a real code symbol -- the actual mechanism is retention_margin in StrategicIntelligenceSystem.evaluate_project_switch(). This ticket adds Parquet/DuckDB access for cognition_features (contingent on the sibling pipeline-wiring ticket), resolves the decision_trace run_id gap with an explicit, documented design decision (add run_id to DecisionTraceWriter's entry dict, or inject it at conversion time from export_run()'s run_id parameter), and verifies a real (entity_id, run_id) join with an integration test -- correcting the proposal's field-name error rather than propagating it.

## Scope
- Depend on / consume the sibling pipeline-wiring ticket's cognition_features Parquet/DuckDB access (do not re-implement it here).
- Resolve the decision_trace.jsonl run_id gap: choose and implement one of (a) add run_id to DecisionTraceWriter's entry dict at write time, or (b) inject run_id at Parquet conversion time from export_run()'s own run_id parameter; document the choice and why.
- Add decision_trace.jsonl -> decision_trace.parquet conversion, reachable via the existing exporter/AnalyticsDatasetBuilder path, carrying the resolved run_id column.
- Add a DuckDB query joining cognition_features and decision_trace on (entity_id, run_id), verified against at least one real run fixture via an integration test.
- Update docs/observability/decision_trace_contract.md and the relevant parity ledger entry in the same session to reflect the entry-shape change.

## Out of Scope
- The post-run pipeline wiring that produces cognition_features.jsonl/cognition_patterns.json and their Parquet/DuckDB access in the first place (hard dependency on the sibling pipeline-wiring ticket).
- Any retroactive reprocessing of E12/E11D's already-closed historical measurement runs -- those ran before broadened cognition capture existed and cannot retroactively benefit; this ticket is forward-looking for future calibration passes only.
- The storage-cost budget decision (consumes it, does not set it), viz_strategy.html playback, the HTML report, and the CI pattern-gate work (separate tickets in this batch).

## Acceptance Criteria
- [ ] cognition_features.jsonl exported into cognition_features.parquet is reachable via AnalyticsDatasetBuilder/ArtifactExporter and queryable by DuckDBQueryService -- contingent on the pipeline-wiring ticket landing first.
- [ ] decision_trace.jsonl exported into decision_trace.parquet carries a run_id column, added either to DecisionTraceWriter's entry dict or injected at conversion time -- the decision is explicitly documented in this ticket, not left implicit.
- [ ] A DuckDB query joining cognition_features and decision_trace on (entity_id, run_id) returns correlated rows (graph_churn_rate alongside route_kind/personality_bias/blocker_penalty) for at least one real run fixture, verified by an integration test.
- [ ] docs/observability/decision_trace_contract.md and the relevant parity ledger entry are updated in the same session to reflect any schema change.

## Related Tickets
- TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
- TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING

## Related Docs
- docs/plans/idea_cognition_graph_analytics_pipeline.md
- docs/observability/decision_trace_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/observability/decision_trace_contract.md
- src/observability/cognition/decision_trace_writer.py
- src/observability/cognition/feature_extractor.py
- src/observability/analytics/exporter.py
- src/observability/analytics/dataset.py
- src/observability/analytics/query.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Hard blocking dependency on the pipeline-wiring ticket; unbuildable standalone.
- The storage-cost budget from the storage-budget ticket applies to this ticket's Parquet output as well.
- Zero live connection to already-closed E12/E11D tickets beyond documentation -- purely forward-looking for future calibration passes, not a retroactive fix to those runs.
- Cite retention_margin (StrategicIntelligenceSystem.evaluate_project_switch()), not the proposal's "switch_margin," which is not a real code symbol.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
