---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-RUN-COGNITION-HEALTH-REPORT
phase: open
date: 2026-08-22
tags: [observability, cognition]
---

# TCK-20260822-RUN-COGNITION-HEALTH-REPORT

## Title
Build a run-level aggregate cross-entity cognition health HTML report

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The idea doc proposes a run-level report "generated post-run by CognitionPatternMiner" with a class-grouping example spanning WARRIOR/MAGE/ROGUE/MERCHANT. Investigation found this reading should not be taken literally -- the architecturally consistent integration point is a new downstream report module analogous to RunReportGenerator, not new methods inside the miner class -- and that MERCHANT does not exist in CLASS_REGISTRY today (only NOVICE/WARRIOR/MAGE/ROGUE), and that class_id is not carried in CognitionFeatureExtractor's own output but must be joined from the separate, change-triggered (not per-tick) PersonalitySnapshotRecorder log. This ticket builds a new, distinct HTML report (not an extension of tools/viz_strategy.html) presenting a pattern-summary table, a churn heatmap, and a class_id grouping table scoped to CLASS_REGISTRY's real classes, hard-blocked on the sibling pipeline-wiring ticket landing first.

## Scope
- Build a new report module (analogous to RunReportGenerator) that generates a single HTML file, distinct from tools/viz_strategy.html, from a run_dir's cognition_patterns.json, cognition_features.jsonl, and entity_personality_snapshots.jsonl.
- Pattern-summary table: pattern_type x severity, with affected-entity count computed as the union of affected_entities across matching patterns.
- Churn heatmap: one cell per (tick-window, entity_id), sourced from diffs' current_project_changed flags, with zero entities silently dropped relative to cognition_features.jsonl's population.
- Class_id grouping table: join cognition_features entity_id against entity_personality_snapshots.jsonl's last-known class_id (accounting for its change-triggered cadence, not a naive per-tick join); one row per distinct class_id actually observed, scoped to real CLASS_REGISTRY values (NOVICE/WARRIOR/MAGE/ROGUE).
- Graceful degradation: when entity_personality_snapshots.jsonl is absent or ObservabilityMode was OFF, the class_id section renders a "class metadata unavailable" notice instead of crashing or silently omitting the section.

## Out of Scope
- Registering MERCHANT (or any other new class) in CLASS_REGISTRY -- the proposal's own class-grouping example names a class that doesn't exist yet; that is a separate concern, not this ticket's job.
- The post-run pipeline wiring that produces cognition_features.jsonl/cognition_patterns.json in the first place (hard dependency on the sibling pipeline-wiring ticket; this ticket consumes those artifacts, it does not produce them).
- viz_strategy.html's temporal playback, the DuckDB/decision_trace join, and the CI pattern-gate work (separate tickets in this batch).

## Acceptance Criteria
- [ ] Given a run_dir with populated cognition_patterns.json/cognition_features.jsonl/entity_personality_snapshots.jsonl, generates a single HTML file (distinct path from tools/viz_strategy.html) with a pattern-summary table (pattern_type x severity, correct affected-entity count from the union of affected_entities).
- [ ] Churn heatmap renders one cell per (tick-window, entity_id) sourced from diffs' current_project_changed flags, with zero entities silently dropped versus cognition_features.jsonl's population.
- [ ] Class_id grouping table joins cognition_features entity_id against entity_personality_snapshots.jsonl's last-known class_id, one row per distinct class_id actually observed in CLASS_REGISTRY (NOVICE/WARRIOR/MAGE/ROGUE -- MERCHANT excluded unless/until it is separately registered).
- [ ] When entity_personality_snapshots.jsonl is absent or the run's mode was OFF, the class_id section renders a clear "class metadata unavailable" notice rather than crashing or silently omitting the section.

## Related Tickets
- TCK-20260822-COGNITION-ANALYTICS-PIPELINE-WIRING

## Related Docs
- docs/plans/idea_cognition_graph_analytics_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/cognition/feature_extractor.py
- src/observability/cognition/pattern_miner.py
- src/observability/cognition/schema.py
- src/observability/cognition/recorder.py
- src/observability/personality/recorder.py
- src/observability/reporting/run_report.py
- src/observability/anomaly/pipeline.py
- src/core/classes.py
- tools/viz_strategy.html

## Assumptions / Open Questions
- Hard blocking dependency on the pipeline-wiring ticket: CognitionPatternMiner/CognitionFeatureExtractor are never called from a real production post-run hook today (only from tests), so this ticket cannot land meaningfully before that wiring exists.
- entity_personality_snapshots.jsonl's change-triggered cadence means a per-tick join is architecturally wrong; last-known-value join is the intended pattern.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
