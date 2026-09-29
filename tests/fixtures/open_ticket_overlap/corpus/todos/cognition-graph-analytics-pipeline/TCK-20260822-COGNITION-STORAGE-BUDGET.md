---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-COGNITION-STORAGE-BUDGET
phase: open
date: 2026-08-22
tags: [observability, cognition]
---

# TCK-20260822-COGNITION-STORAGE-BUDGET

## Title
Define storage-cost budget for cognition graph capture and Parquet tables

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The idea doc (docs/plans/idea_cognition_graph_analytics_pipeline.md) proposes building cognition_features.parquet/cognition_patterns.parquet analytics tables and cites 5.9MB/143MB storage figures as if they described those tables' cost. Investigation found those figures actually describe raw per-tick cognition_graph_snapshots.jsonl/diffs.jsonl capture (TCK-20260805's measurement), not the small aggregated Parquet outputs that would be built from them -- and no retention policy exists today to delete the raw JSONL after feature extraction. Before any pipeline-wiring work proceeds, this ticket must produce a written budget that separates the two costs, sets a concrete corpus-scope ceiling for raw capture, decides retention vs. deletion of raw snapshots/diffs post-conversion, and states the Parquet compression codec for the new tables -- correcting the proposal's conflation rather than carrying it forward.

## Scope
- Produce a written storage-cost budget document (or ticket-embedded policy section) covering cognition capture and analytics-table storage.
- Measure or credibly estimate: (a) cognition_features.jsonl/cognition_patterns.json per-run size at aggregated scale, (b) raw cognition_graph_snapshots.jsonl/diffs.jsonl size at the same run scale, explicitly distinguishing the two.
- Define a concrete corpus-scope ceiling for raw capture (e.g., opt-in scenario/tier list, or a total raw-capture byte ceiling per make simq-full-audit-full run) -- not open-ended.
- Decide and document explicitly whether raw snapshots/diffs are retained or deleted after Parquet/feature extraction, and the durable-cost delta of that choice.
- Specify the Parquet compression codec/setting for cognition_features.parquet and cognition_patterns.parquet with rationale.

## Out of Scope
- Building the Parquet tables, exporter wiring, or post-run hook itself (covered by the pipeline-wiring ticket in this batch).
- Any change to tools/calibrate_simq.py or its corpus-scope decision (TCK-20260805 already declined that; this ticket must not silently re-decide it as a side effect -- it must make the call explicitly and document it here).
- The viz_strategy.html temporal playback, run-level HTML report, DuckDB/decision_trace join, and CI pattern-gate work (each a separate ticket in this batch).

## Acceptance Criteria
- [ ] Written budget states separately (a) estimated size of cognition_features.parquet/cognition_patterns.parquet per run (small, aggregated) vs (b) size of raw snapshots/diffs required to produce them (large, per TCK-20260805's 5.9MB/150-tick and 143MB/2000-tick figures), explicit about which cost is bounded by this policy.
- [ ] Budget defines a concrete corpus-scope limit for raw capture (e.g., opt-in for N scenarios/tiers, or a total raw-capture ceiling per make simq-full-audit-full run), not left open-ended.
- [ ] Budget explicitly states whether raw snapshots/diffs are retained after Parquet/feature extraction or deleted post-conversion, with the resulting durable-cost figure for each choice.
- [ ] Budget states the Parquet compression codec/setting for cognition_features.parquet and cognition_patterns.parquet, with rationale.

## Related Tickets
- TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP
- TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING

## Related Docs
- docs/plans/idea_cognition_graph_analytics_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/idea_cognition_graph_analytics_pipeline.md
- src/observability/cognition/feature_extractor.py
- src/observability/cognition/pattern_miner.py
- src/observability/cognition/recorder.py
- src/observability/analytics/exporter.py
- tools/calibrate_simq.py

## Assumptions / Open Questions
- No prior measurement exists of cognition_features.jsonl/cognition_patterns.json real file sizes at corpus scale; this ticket must measure against a real run rather than assume from the idea doc's numbers.
- If the budget decision is 'scoped opt-in' capture, that would reintroduce TCK-20260805's own already-declined open question -- this ticket must make that call explicitly rather than silently duplicating the undecided state.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
