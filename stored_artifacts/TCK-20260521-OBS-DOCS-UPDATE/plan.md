---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260521-OBS-DOCS-UPDATE
artifact_type: plan
tags: [obs, docs, update]
---

# Plan - Documentation Updates for Phase 1 to Phase 8 Observability

## Goal

Provide comprehensive, highly-polished, premium-quality documentation for the entire Observability & Simulation Understanding platform (Phases 1-8) of the V2 RPG Engine. This will ensure that all architecture, boundaries, configuration options, post-run analyzers, baselines, sweep generators, live pub-sub streams, and human-in-the-loop diagnostic components are completely documented and aligned with the "explainable and rule-based" design standards.

## User Review Required

None. This is a documentation-only update requested directly by the user.

## Proposed Changes

### Root Documentation
- **[MODIFY] [README.md](file:///home/vboxuser/Work/rpg-based-simulation/README.md)**: Extend the main README to cover the introduction and architecture of the post-run observability pipeline, live streams, and diagnostic system.

### Phase Docs
- **[NEW] [phase_3.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_3.md)**: Document the single-run Processing Pipeline, `RunArtifactRepository`, `RunManifest`, `MetricWindowRecorder` (`metric_windows.jsonl`), `AnalysisPipeline`, and core rules.
- **[NEW] [phase_4.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_4.md)**: Document multi-run baseline and balance analysis, sequential sweep configurations, distribution summarization, and baseline comparison policies.
- **[NEW] [phase_5.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/docs/observability/phase_5.md)**: Document live observability inspection, REST status/snapshot APIs, the focused `EntityInspector`, thread-safe `LiveEventPublisher`, and backpressure eviction hierarchies.
- **[NEW] [phase_6.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_6.md)**: Document externalization and scale readiness, pyarrow Parquet exports, local DuckDB database datasets, query abstractions, and stream adapter interfaces.
- **[NEW] [phase_7.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_7.md)**: Document production-grade integration layer, optional ClickHouse warehouse schemas, Redis stream publisher adapter with non-blocking worker thread, and live anomaly worker boundaries.
- **[NEW] [phase_8.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_8.md)**: Document post-run Advanced Simulation Understanding pipeline, Domain Analyzer Framework, Scenario Expectation Packs, Root-Cause Hypothesis Engine, Balance Diagnosis Engine, Emergent Story Detector, and Human Review Annotations.

## Verification Plan

### Automated Verification
- Verify that there are no broken local markdown links or formatting issues.
- Run `pytest` on the existing suite to ensure that no behavior has been altered and all unit/integration tests remain passing.
