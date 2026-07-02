# Plan — TCK-20260627-P1H-GOAL-RUNNERUP

## Ordered Steps

### Step 1 — Add `goal_scores` field to `EntityInspectionSnapshot`

**File:** `src/observability/live/entity_inspector.py`

- Add `goal_scores: List[Dict[str, Any]] = Field(default_factory=list)` to `EntityInspectionSnapshot`.
- In `EntityInspector.inspect_entity()`, after building all other fields: import `get_active_writer` lazily (inside the method body), call `active_writer.get_latest_goal_scores(entity_id)` if writer is not None, assign result to `goal_scores`.
- Pass `goal_scores=goal_scores` to the `EntityInspectionSnapshot(...)` constructor call.

**Scope guard:** Do not change any other field or existing population logic. Lazy import to avoid circular dependency.

**AC satisfied:** AC 1.

---

### Step 2 — Extend `DecisionTraceWriter` with sorting, runner-up output, and goal-scores cache

**File:** `src/observability/cognition/decision_trace_writer.py`

2a. In `__init__()`: add `self._latest_goal_scores: Dict[int, List[Dict[str, Any]]] = {}`.

2b. In `write_trace()`:
  - Sort `scored_routes` by `score` descending: `sorted_routes = sorted(scored_routes, key=lambda r: r.score, reverse=True)`.
  - Compute top-3: `top3 = sorted_routes[:3]`.
  - Build `goal_scores_list` as `[{"goal_id": r.family.value if hasattr(r.family, "value") else str(r.family), "score": r.score, "rank": i+1} for i, r in enumerate(top3)]`.
  - Update cache: `self._latest_goal_scores[entity_id] = goal_scores_list`.
  - Extract `source_goal_score = sorted_routes[0].score if sorted_routes else None`.
  - Extract `runner_up_scores = goal_scores_list[1:]` (ranks 2 and 3 only; empty if ≤1 candidate).
  - Replace existing `routes_payload` loop to iterate over `sorted_routes[:5]` (not `scored_routes[:5]`).
  - Extend `entry` dict with top-level `"source_goal_score": source_goal_score` and `"runner_up_scores": runner_up_scores`.

2c. Add method `get_latest_goal_scores(self, entity_id: int) -> List[Dict[str, Any]]`: return `self._latest_goal_scores.get(entity_id, [])`.

**Scope guard:** Do not change `close()`, `_ensure_open()`, or the tick index logic. Do not touch `phase.py` — all sorting happens in the writer.

**AC satisfied:** AC 2, AC 3 (graceful truncation), AC 4 (routes sorted).

---

### Step 3 — Update `decision_trace_contract.md`

**File:** `docs/observability/decision_trace_contract.md`

- Add `source_goal_score` and `runner_up_scores` to the JSON Schema section.
- Note that `routes` is now sorted by descending score.

**Scope guard:** Documentation only. No code changes.

---

### Step 4 — Add new unit tests

**File:** `tests/unit/observability/test_decision_trace.py`

Add at the bottom of the file (after existing tests):
- `test_decision_trace_runner_up_scores_present`
- `test_decision_trace_source_goal_score_present`
- `test_decision_trace_runner_up_fewer_than_3`
- `test_decision_trace_runner_up_single_candidate`
- `test_decision_trace_routes_sorted_descending`
- `test_entity_inspection_snapshot_has_goal_scores_field`
- `test_decision_trace_writer_caches_goal_scores`

---

## Dependency Map

- Step 1 is independent of Steps 2-4.
- Step 2 must precede Step 4 (tests exercise writer).
- Step 3 is independent (docs only).

Execute order: 1 → 2 → 3 → 4.

## Acceptance Criteria Mapping

| AC | Steps |
|---|---|
| `EntityInspectionSnapshot` has `goal_scores` field | Step 1 |
| `decision_trace.jsonl` has `runner_up_scores` + `source_goal_score` | Step 2 |
| Graceful truncation (<3 candidates) | Step 2 |
| Unit test: 3+ candidates → ≥2 runner-up entries | Step 4 |
| Existing tests pass | Steps 2,4 (additive only) |

## Explicit Out-of-Scope Guards

- Do NOT modify `AdventureDecisionPhase.apply()` — no changes to `phase.py`.
- Do NOT modify `AdventureDecisionService.decide()` — no changes to `service.py`.
- Do NOT modify goal scoring logic (`scoring.py`).
- Do NOT change `cognition_graph_snapshots.jsonl` schema or `recorder.py`.
- Do NOT add REST endpoints.

## Deviations

_(none yet — filled in if implementation diverges)_
