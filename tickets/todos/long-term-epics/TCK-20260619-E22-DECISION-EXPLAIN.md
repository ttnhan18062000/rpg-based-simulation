---
status: open
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22-DECISION-EXPLAIN
phase: open
date: 2026-06-19
tags: [decision-explanation, observability, rest-api, route-trace, cognition, epic, phase-2]
---

# TCK-20260619-E22-DECISION-EXPLAIN

## Title
Epic 2.2 · Decision Explanation Model

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Goal scoring is computed in `execute_brain()` every tick and discarded at tick boundary. `cognition_graph_snapshots.jsonl` exist only in DEBUG/CERTIFICATION mode with no REST API and no tick index. Every behavioral quality experiment requires manual JSONL parsing. Promoting existing computed data to a queryable API closes the P0 gap without new simulation logic.

Score: 7/10 · Effort: M · Source: `docs/audits/D15_entity_decision_inspection.md`

## Scope
- Promote route trace data to a durable per-tick snapshot: store top-5 scored routes per entity per tick (route_kind, score breakdown by term: urgency/benefit/personality_bias/confidence_bonus/risk_penalty/blocker_penalty, selected=True/False)
- Write snapshots to `decision_trace.jsonl` in LIGHT observability mode (not DEBUG-only)
- Add tick-index sidecar (`decision_trace_index.json`) mapping tick → byte offset for O(1) lookup
- REST endpoints:
  - `GET /api/v1/observability/entities/{id}/decisions?tick={N}` — tick-N snapshot
  - `GET /api/v1/observability/entities/{id}/decisions/range?from={A}&to={B}` — time range
  - `GET /api/v1/observability/entities/{id}/decisions/summary` — project-kind distribution histogram
- Child tickets: (a) snapshot storage schema + writer, (b) tick-index sidecar, (c) REST endpoints

## Out of Scope
- Interactive replay UI
- Multi-entity comparison view
- Goal score influence visualization

## Acceptance Criteria
- `curl /api/v1/observability/entities/7/decisions?tick=342` returns a ranked list of scored routes with per-term breakdown, without reading JSONL manually
- `decision_trace.jsonl` exists in LIGHT mode runs (not just DEBUG)
- Tick-index lookup for a specific tick completes in O(1) (byte seek, not scan)

## Related Tickets
- TCK-20260619-E12-BALANCE-BASELINE (unlocked: every balance measurement can use this API)

## Related Docs
- `docs/audits/D15_entity_decision_inspection.md` (promote from gap-analysis to implemented after completion)
- `docs/plans/long_term_development_roadmap.md` § Epic 2.2
- `docs/engine/kernel.md` (cognition phase is where `execute_brain()` runs; decision trace writer is inserted here — update to note LIGHT mode trace output)
- `docs/simulation/domains/campaigns_contract.md` (observability boundary reference)
- `docs/parity_ledger/infrastructure.yaml` (observability tooling entries — add decision trace as `verified`)
- New doc: `docs/observability/decision_trace_contract.md` (decision trace schema, index format, REST endpoints, LIGHT mode behavior)
- `docs/plans/idea_cognition_graph_analytics_pipeline.md` (idea: wire `decision_trace.jsonl` into `ArtifactExporter` + `AnalyticsDatasetBuilder` Parquet tables so DuckDB can join traces against cognition features — define artifact type key `"decision_trace"` in this epic's writer so the analytics pipeline can reference it by name)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-D15/`

## Related Code Areas
- `src/domains/adventure/brain.py` (execute_brain() — where route trace is computed)
- `src/observability/` (existing cognition_graph_snapshots.jsonl writer — reference for pattern)
- `src/` REST API layer (locate existing API structure before adding new routes)

## Assumptions / Open Questions
- Where is the REST API layer? Find existing route pattern (check `src/api/` or `src/` for FastAPI/Flask entrypoint) before adding routes
- Are REST APIs served by the same process as the simulation kernel, or a separate reader process?

## Implementation Notes
This epic promotes existing computed data — do not change `execute_brain()` logic, only add a writer at the point where the trace is currently discarded. Use the existing cognition_graph_snapshots.jsonl writer as a pattern for the new decision_trace.jsonl.

After implementation: create `docs/observability/decision_trace_contract.md` documenting the schema, index format, and REST API contract. Update `docs/parity_ledger/infrastructure.yaml` — add a new entry for decision trace observability with `status: verified` and `test_path`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/observability/test_decision_trace.py`:
  - `test_decision_trace_written_in_light_mode()` — run 10-tick sim in LIGHT mode; assert `decision_trace.jsonl` exists with ≥1 entry per entity-tick
  - `test_decision_trace_schema_has_all_score_terms()` — assert each entry contains urgency/benefit/personality_bias/confidence_bonus/risk_penalty/blocker_penalty fields
  - `test_tick_index_o1_lookup()` — write decision_trace.jsonl, build index, assert byte-seek for tick N returns correct entry without scanning full file
- New file `tests/api/test_decision_api.py`:
  - `test_decision_api_returns_score_breakdown()` — POST a run, GET `/api/v1/observability/entities/{id}/decisions?tick={N}`; assert ranked routes with per-term scores
  - `test_decision_api_range_query()` — GET range from A to B; assert N×(B-A) entries returned

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
