# Test Plan — TCK-20260627-P1H-GOAL-RUNNERUP

## Regression Surface (existing tests that must pass)

| Test file | Why it must pass |
|---|---|
| `tests/unit/observability/test_decision_trace.py` | All existing writer/index tests — schema is additive |
| `tests/unit/observability/test_phase17_decision_trace_contract.py` | Contract invariants |
| `tests/unit/observability/test_phase17_decision_trace_validator.py` | Validator guards |
| `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py` | End-to-end trace write |

Scoped regression command:
```
pytest tests/unit/observability/ tests/integration/scenarios/test_phase17_decision_trace_scenarios.py -m "not slow" -v
```

## New Tests Required (per AC)

All new tests go in `tests/unit/observability/test_decision_trace.py`.

### AC 1 — runner_up_scores in decision_trace.jsonl

`test_decision_trace_runner_up_scores_present`
- Give writer 5 candidates with distinct scores.
- Call `write_trace()`.
- Read JSONL; assert entry has `runner_up_scores` key.
- Assert `len(runner_up_scores) == 2` (ranks 2 and 3).
- Assert each entry has `goal_id`, `score`, `rank` keys.
- Assert rank values are 2 and 3.

### AC 2 — source_goal_score in decision_trace.jsonl

`test_decision_trace_source_goal_score_present`
- Write single route with score 0.77.
- Assert entry has `source_goal_score == 0.77`.

### AC 3 — graceful truncation when fewer than 3 candidates

`test_decision_trace_runner_up_fewer_than_3`
- Write with 2 candidates (scores 0.8, 0.4).
- Assert `runner_up_scores` has exactly 1 entry (rank 2).

`test_decision_trace_runner_up_single_candidate`
- Write with 1 candidate.
- Assert `runner_up_scores` is empty list `[]`.

### AC 4 — routes sorted by score descending

`test_decision_trace_routes_sorted_descending`
- Give writer candidates in unsorted order (scores 0.3, 0.9, 0.6).
- Assert `routes[0]["score"] == 0.9` (highest first).
- Assert `routes[0]["selected"] is True`.

### AC 5 — EntityInspectionSnapshot has goal_scores field

`test_entity_inspection_snapshot_has_goal_scores_field`
- Construct `EntityInspectionSnapshot(entity_id=1, exists=False)`.
- Assert `hasattr(snapshot, "goal_scores")`.
- Assert `snapshot.goal_scores == []`.

### AC 6 — writer cache populates goal_scores

`test_decision_trace_writer_caches_goal_scores`
- Write 5 candidates.
- Call `writer.get_latest_goal_scores(entity_id)`.
- Assert returns list of 3 entries (top-3).
- Assert first entry has `rank == 1`.

## Scoped Pytest Commands

Full new + regression scope:
```bash
pytest tests/unit/observability/test_decision_trace.py tests/unit/observability/test_phase17_decision_trace_contract.py tests/unit/observability/test_phase17_decision_trace_validator.py tests/integration/scenarios/test_phase17_decision_trace_scenarios.py -m "not slow" -v
```

Quick sanity check (new tests only):
```bash
pytest tests/unit/observability/test_decision_trace.py -m "not slow" -v
```

## Anti-Drift Test Guards

- Existing `test_decision_trace_caps_at_5_routes` must still pass (routes still capped at 5).
- Existing `test_decision_trace_selected_flag` must still pass (first route is winner).
- Existing `test_decision_trace_schema_has_all_score_terms` must still pass (8 score fields intact).
