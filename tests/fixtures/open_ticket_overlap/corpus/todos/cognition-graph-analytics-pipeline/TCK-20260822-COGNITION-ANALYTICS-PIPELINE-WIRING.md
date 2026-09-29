---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING
phase: open
date: 2026-08-22
tags: [observability, cognition, schema]
---

# TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING

## Title
Wire cognition feature/pattern artifacts into the post-run analytics pipeline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The idea doc proposes wiring CognitionFeatureExtractor/CognitionPatternMiner output into a "Persistence phase post-run hook" alongside Parquet conversion, DuckDB querying, and a cognition_health_score field added "alongside" RunManifest's existing health_score. Investigation found the Persistence-phase framing is wrong (Kernel._phase_persistence only computes hashes/replay events) and that RunManifest has no existing health_score field to sit alongside -- the real run-level health_score lives on AnalysisResult/run_report.json instead. This ticket wires the (stateless, read-only) extractor and miner into a real post-run hook -- Kernel.shutdown() or the external AnalysisPipeline, whichever is chosen and documented -- adds Parquet conversion for the two new tables following the existing _convert_X_to_parquet pattern, exposes them via DuckDBQueryService using the miner's own DEFAULT_THRESHOLDS (not a second hardcoded copy), and adds cognition_health_score as a genuinely new typed RunManifest field.

## Scope
- Choose and document the post-run hook location (Kernel.shutdown() vs external AnalysisPipeline) and explicitly state which run paths get coverage (standalone Kernel runs vs sweep/lab-orchestrated runs only).
- Call CognitionFeatureExtractor and CognitionPatternMiner from that hook to produce cognition_features.jsonl and cognition_patterns.json for a completed run automatically.
- Add Parquet conversion for both artifacts to ParquetArtifactExporter, following the existing _convert_X_to_parquet(src_path, dest_path) -> count + mapping-entry pattern.
- Add a predefined DuckDB query (e.g. overloaded-entities) to DuckDBQueryService, sourcing thresholds from CognitionPatternMiner.DEFAULT_THRESHOLDS rather than a duplicated hardcoded copy.
- Add cognition_health_score as a new typed field on RunManifest (not assumed onto a nonexistent existing health_score key), deterministic and clamped to [0.0, 1.0].
- Apply the storage-cost budget/ceiling decided in the sibling storage-budget ticket to whatever raw-capture scope this hook triggers.

## Out of Scope
- Deciding the storage-cost budget itself (covered by the storage-budget ticket; this ticket consumes that decision, it does not make it).
- viz_strategy.html temporal playback, the run-level HTML report, the DuckDB/decision_trace join, and the CI pattern-gate work (separate tickets in this batch).
- Any change to tools/calibrate_simq.py's corpus scope.

## Acceptance Criteria
- [ ] Invoking the wired post-run hook on a completed run with a non-empty cognition_graph_snapshots.jsonl produces cognition_features.jsonl and cognition_patterns.json without any separate manual call.
- [ ] ParquetArtifactExporter.export_run(artifact_types=['cognition_features']) produces cognition_features.parquet with row count equal to the source jsonl's line count and a schema matching the idea doc's 12-column spec; the same holds for cognition_patterns with its 8-column schema.
- [ ] DuckDBQueryService.execute_predefined_query('overloaded-entities') returns rows using the shared threshold from CognitionPatternMiner.DEFAULT_THRESHOLDS (not a second hardcoded copy); pattern-summary counts sum to len(cognition_patterns.json).
- [ ] cognition_health_score is deterministic, clamped to [0.0, 1.0], and written to an explicitly new typed RunManifest field (not assumed onto a nonexistent existing health_score key).

## Related Tickets
- TCK-20260822-COGNITION-STORAGE-BUDGET
- TCK-20260822-RUN-COGNITION-HEALTH-REPORT
- TCK-20260822-COGNITION-DECISION-TRACE-JOIN
- TCK-20260822-COGNITION-PATTERN-CI-GATE

## Related Docs
- docs/plans/idea_cognition_graph_analytics_pipeline.md
- docs/engine/kernel.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/analytics/dataset.py
- src/observability/analytics/exporter.py
- src/observability/analytics/query.py
- src/observability/cognition/feature_extractor.py
- src/observability/cognition/pattern_miner.py
- src/observability/cognition/recorder.py
- src/observability/reporting/artifact_repository.py
- src/engine/kernel.py
- src/observability/anomaly/pipeline.py
- src/observability/sweeper.py
- src/lab/orchestrator.py

## Assumptions / Open Questions
- Must explicitly pick Kernel.shutdown() vs external AnalysisPipeline as the hook location; a standalone single Kernel run outside sweep/lab orchestration never calls AnalysisPipeline today, so the choice determines which run paths get coverage.
- AnalyticsDatasetBuilder.build_dataset() is currently sweep-scoped only; new tables must follow the same sweep-level read loop unless this ticket explicitly extends that scope.
- Depends on the storage-cost budget ticket landing first (or at minimum its scope decision being available) since this ticket's raw-capture trigger inherits that cost.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
