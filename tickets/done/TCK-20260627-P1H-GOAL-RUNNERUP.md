---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P1H-GOAL-RUNNERUP
phase: done
date: 2026-06-27
tags: [p1, cognition, decision-trace, runner-up, goal-score, observability]
---

# TCK-20260627-P1H-GOAL-RUNNERUP

## Title
Retain top-3 runner-up goal scores in cognition snapshot and decision trace

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The trace writer added by TCK-20260619-E22A-TRACE-WRITER captures the winning project's `source_goal_score` — but runner-up scores (why goal X won over Y) are computed transiently in `execute_brain()` and discarded at tick boundary. A developer cannot distinguish "entity stuck because all alternatives scored lower" from "entity stuck because a high-priority goal should have been interrupted." Source: D15 Gap 1 (partial resolution).

## Scope
- Retain the top-3 candidate (goal, score) pairs at tick commit in the cognition snapshot.
- Add a `goal_scores: list[GoalScoreEntry]` field to `EntityInspectionSnapshot` (or equivalent decision trace record).
- Extend the `decision_trace.jsonl` schema to include the top-3 alternatives alongside the winner.
- Wire the score collection in `execute_brain()` in `src/domains/adventure/phase.py`.
- Update `src/observability/cognition/recorder.py` to serialize the top-3.

## Out of Scope
- Storing all N candidates (only top-3 needed).
- API or REST endpoint for querying runner-up scores (future work).
- Changes to goal scoring logic itself.

## Acceptance Criteria
- [ ] `EntityInspectionSnapshot` has `goal_scores: list[dict]` (or typed `GoalScoreEntry`) with at minimum `{"goal_id": ..., "score": ..., "rank": ...}` per entry.
- [ ] `decision_trace.jsonl` records include `"runner_up_scores": [...]` alongside `"source_goal_score"`.
- [ ] Top-3 are populated even when fewer than 3 candidates exist (graceful truncation).
- [ ] Unit test: after a tick with 3+ goal candidates, `decision_trace` entry contains at least 2 runner-up scores.
- [ ] Existing decision trace tests pass.

## Related Tickets
- TCK-20260619-E22-DECISION-EXPLAIN (prior ticket that added trace writer — read its stored artifacts for schema context)

## Related Docs
- `docs/audits/D15_entity_decision_inspection.md` Gap 1 and Recommended Follow-Up
- `docs/observability/decision_trace_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E22-DECISION-EXPLAIN/` (if it exists) — decision trace implementation

## Related Code Areas
- `src/domains/adventure/phase.py` (`execute_brain()` — where goal scores are computed)
- `src/observability/cognition/recorder.py` (serialization)
- `src/core/models/` (snapshot schema)

## Assumptions / Open Questions
- "Top-3" means: winner (rank 1) + 2 highest-scoring alternatives. Sort descending by score, take first 3.
- `GoalScoreEntry` can be a simple `@dataclass(frozen=True)` or a TypedDict — prefer dataclass for type safety.

## Implementation Notes
- `DecisionTraceWriter.write_trace()` now sorts `scored_routes` by score descending before slicing. This ensures `routes[0]` is always the winner regardless of input order.
- Added `_latest_goal_scores: Dict[int, List[Dict]]` cache in writer (entity_id → top-3). Exposed via `get_latest_goal_scores(entity_id)`.
- New top-level fields in `decision_trace.jsonl` entry: `source_goal_score` (winner score) and `runner_up_scores` (list of `{"goal_id", "score", "rank"}` for ranks 2 and 3).
- `EntityInspectionSnapshot` gained `goal_scores: List[Dict[str, Any]]` field. Populated from the active writer cache inside `EntityInspector.inspect_entity()` via lazy import.
- `phase.py` was NOT modified — all sorting logic lives in the writer, not the call site.
- 7 new unit tests added to `tests/unit/observability/test_decision_trace.py`.

## Test Summary
- Unit: mock goal scorer returning 5 candidates, assert `decision_trace` entry has 2 runner-up entries (ranks 2 and 3).
- Regression: `pytest tests/ -k "decision_trace or cognition" -m "not slow"`.

## Files Changed
- `src/observability/cognition/decision_trace_writer.py` — sorting, runner_up_scores, source_goal_score, goal-score cache, get_latest_goal_scores()
- `src/observability/live/entity_inspector.py` — goal_scores field on EntityInspectionSnapshot, population from writer cache
- `docs/observability/decision_trace_contract.md` — schema updated with new fields
- `docs/parity_ledger/infrastructure.yaml` — INFRA-211 updated
- `tests/unit/observability/test_decision_trace.py` — 7 new tests added

## Completion Summary
Retained top-3 goal scores (winner + 2 runner-ups) at each tick in the decision trace. `DecisionTraceWriter.write_trace()` now sorts candidates by score descending before serialization and emits two new top-level fields in `decision_trace.jsonl`: `source_goal_score` (winner's score) and `runner_up_scores` (list of `{"goal_id", "score", "rank"}` for ranks 2–3). A per-entity goal-score cache (`_latest_goal_scores`) is maintained in the writer and exposed via `get_latest_goal_scores(entity_id)`. `EntityInspectionSnapshot` gained a `goal_scores: List[Dict]` field populated from the active writer cache inside `EntityInspector.inspect_entity()`. 7 new unit tests added covering all acceptance criteria; 28 total tests pass (0 failures). Parity ledger INFRA-211 and decision_trace_contract.md updated to reflect the schema extension.
