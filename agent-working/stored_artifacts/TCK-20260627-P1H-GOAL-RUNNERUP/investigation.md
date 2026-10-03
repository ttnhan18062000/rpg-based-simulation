# Investigation — TCK-20260627-P1H-GOAL-RUNNERUP

## Current Behavior (file:line refs)

### Data flow for scored candidates

1. `AdventureDecisionService.decide()` — `src/domains/adventure/service.py:71-79`
   - Iterates `candidates`, calls `AdventureRouteScorer.score()` for each, appends to `scored_candidates` (generation order, **not sorted**).
   - `valid_candidates` is sorted by `(score, confidence, expected_benefit)` descending — but this sorted list is **not** put into the trace.
   - `trace["scored_candidates"] = scored_candidates` — unsorted full list.

2. `AdventureDecisionPhase.apply()` — `src/domains/adventure/phase.py:85-87`
   - Reads `scored_candidates = result.trace.get("scored_candidates", [])`.
   - Passes them directly to `_writer.write_trace(hero.id, tick, scored_candidates)` — **unsorted**.

3. `DecisionTraceWriter.write_trace()` — `src/observability/cognition/decision_trace_writer.py:85-96`
   - Iterates `scored_routes[:5]` **without sorting**.
   - Marks `idx == 0` as `selected=True` — assumes first route is the winner, but candidates arrive in generation order so this is only coincidentally correct.
   - No `runner_up_scores` field. No `source_goal_score` in the decision trace.
   - Entry schema: `{entity_id, tick, routes[]}` — no explicit rank or runner-up.

4. `EntityInspectionSnapshot` — `src/observability/live/entity_inspector.py:8-27`
   - No `goal_scores` field currently.
   - Inspector reads from `manager.latest_state` and kernel timeline — no access to decision trace scores.

### Snapshot recorder
- `cognition_graph_snapshots.jsonl` does have `source_goal_score` (winner project score from entity state) — `src/observability/cognition/recorder.py:236-237`.
- This is the *project's stored score*, not live scoring comparison data.

## Mechanics/Engine Constraints

- No Mechanics Bible chapters constrain this (pure observability feature, no simulation law changes).
- Engine contracts: changes are post-commit, read-only observations only — no authoritative state mutations.
- Architecture rule: decision trace writer is observability infrastructure, not durable state.

## Parity Ledger Overlap

- **INFRA-211** (`infrastructure.yaml:2387-2394`): Decision trace writer. Currently text says captures "all 8 score-term fields". After this ticket, the schema also includes `source_goal_score` and `runner_up_scores`. Entry needs updating.
- No other ledger entries directly affected.

## Prior Work

- **TCK-20260619-E22A-TRACE-WRITER**: Added `DecisionTraceWriter` and wired it in `AdventureDecisionPhase.apply()`. `scored_candidates` path was established. Test file: `tests/unit/observability/test_decision_trace.py`.
- **TCK-20260619-E22B-TICK-INDEX**: Added `DecisionTraceIndex` tick-based O(1) lookup. No schema change needed here.
- **TCK-20260619-E22C-REST-API**: REST endpoints on top of the tick index. Schema extension here will flow through to the REST responses automatically.

## Risks and Open Questions

1. **Sorting in writer vs. service**: `scored_candidates` arrives unsorted. Sorting must happen in `write_trace()` (not in `phase.py`) to keep the writer self-consistent and not affect `phase.py` behavior.
2. **`goal_id` = `route_kind`**: The ticket calls it `goal_id`; the actual concept is `RouteFamily.value` string. Naming is consistent with the ticket's intent.
3. **Cache invalidation**: The per-entity goal-scores cache in the writer persists the last tick's scores. Inspection calls between ticks will see the prior tick's data — acceptable given the observability-only use case.
4. **Backward compatibility**: Existing tests assert `routes` list schema. Adding `source_goal_score` and `runner_up_scores` top-level fields is additive — backward compatible.

## Anti-Drift Hazards

- `DecisionTraceWriter._latest_goal_scores` dict grows with one entry per entity per run — bounded by entity count, no leak risk.
- Sorting inside `write_trace()` must use only `score` (float) as key to stay deterministic.
- `EntityInspector` must import `get_active_writer` lazily (inside the method) to avoid circular import risk.
