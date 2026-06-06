# TCK-20260519-SIM-OBS-PHASE3-M13

## Title

Milestone 13: Evidence, Triage, and Report V2

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the post-simulation triage engine, evidence builder, and investigation hint generator. Upgrade the Markdown report generator to support all Report V2 sections, including anomaly clustering, evidence samples, and skipped rules to make the diagnostic outputs highly actionable and robust.

## Scope

- **Evidence Builder**:
  - Implement `EvidenceBuilder` to query and attach relevant event segments, metric window sequences, and hard law breach records to individual anomalies.
  - Ensure evidence is compact, JSON-serializable, and structured with clear origin/tick bounds.
- **Triage & Clustering**:
  - Design `TriageEngine` to group/cluster anomalies by matching `rule_id`, severity, regional/resource context, and overlapping tick ranges.
  - Count total affected entities and resource IDs per cluster while preserving raw anomaly records.
- **Troubleshooting Hints**:
  - Implement dynamic lookup for `InvestigationHint` mapping based on standard rules (e.g. stuck navigation, zero production, governor degradation).
- **Report V2 Renderer**:
  - Upgrade `RunReportGenerator` in `src/observability/reporting/run_report.py` to produce Report V2 formats.
  - Add standard tables for: executive run summaries, rule execution statuses (including skipped/missing signal counts), structured anomaly clusters, sample evidence blocks, and targeted recommended investigation items.

## Out of Scope

- Real-time online streaming triage engine logic.
- Natural language generation models for dynamic hints.

## Acceptance Criteria

- **Evidence attachment**: Anomalies are enriched with clean, bounded JSON evidence objects.
- **Deterministic Clustering**: Repeated anomalies in the same space-time span are grouped deterministically without duplicate records.
- **Report Completeness**: The final `run_report.md` contains all Report V2 sections (statuses, clusters, skipped details, hints).
- **JSON/MD parity**: Parity between structured `run_report.json` and rendering in `run_report.md`.
- **Test suite**: Comprehensive test coverage across new components via unit and integration tests.

## Related Tickets

- `TCK-20260519-SIM-OBS-PHASE3-M12`

## Related Docs

- `obs_sim_phase3.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/anomaly/triage.py` [NEW]
- `src/observability/reporting/run_report.py` [MODIFY]
- `src/observability/anomaly/pipeline.py` [MODIFY]
- `tests/unit/observability/test_triage_engine.py` [NEW]
- `tests/unit/observability/test_evidence_builder.py` [NEW]
- `tests/integration/observability/test_report_v2.py` [NEW]

## Assumptions / Open Questions

- Static hint lists are sufficient for Phase 3 and can be expanded via code dictionaries.

## Implementation Notes

- Designed `EvidenceBuilder` with deterministic time-window queries to isolate local events (within `[tick_start - 5, tick_end + 5]`) and metric window entries without overloading memory.
- Built a multi-key spacetime group clusterer in `TriageEngine` that safely groups anomalies when they intersect overlapping temporal windows (tolerance up to 10 ticks) and share matching spatial properties (`region_id`, `resource_id`, `quest_id`).
- Implemented `InvestigationHint` maps for stuck paths, production drops, crowding limits, endless combat, and hard law violations.
- Integrated the new triage capabilities directly into the core `AnalysisPipeline.run()` execution block, keeping full compatibility with pre-existing reports.

## Test Summary

- Added 5 new unit tests in `tests/unit/observability/test_evidence_builder.py` covering event matching, window metrics gathering, and edge case bounds.
- Added 2 new unit tests in `tests/unit/observability/test_triage_engine.py` for spatial-temporal matching and entity/resource aggregation.
- Added a full end-to-end integration test in `tests/integration/observability/test_report_v2.py` simulating standard rule execution, clustering, and markdown structure validation.
- All 52 unit and integration tests passed cleanly and deterministic correctness has been fully certified.

## Files Changed

- `src/observability/anomaly/triage.py`
- `src/observability/reporting/run_report.py`
- `src/observability/anomaly/pipeline.py`
- `tests/unit/observability/test_evidence_builder.py`
- `tests/unit/observability/test_triage_engine.py`
- `tests/integration/observability/test_report_v2.py`

## Completion Summary

- Implemented the full post-simulation triage engine, evidence builder, and investigation hint generator.
- Upgraded the Markdown/JSON run report generator to support all upgraded Report V2 sections, including anomaly clustering, evidence samples, skipped rules execution status, and recommended troubleshooting actions.
- Successfully verified all features, maintaining 100% backward compatibility with all pre-existing simulation observability flows.
