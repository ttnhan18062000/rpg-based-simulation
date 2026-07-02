---
ticket_id: TCK-20260619-E22-DECISION-EXPLAIN
phase: test_plan
date: 2026-06-20
---

# Test Plan: Decision Explanation Model

## Unit Tests (new file: tests/unit/observability/test_decision_trace.py)

Written in E22A:

### test_decision_trace_written_in_light_mode
- Run 10-tick simulation in LIGHT observability mode
- Assert `decision_trace.jsonl` exists in run dir
- Assert ≥ 1 entry per entity that had routes scored

### test_decision_trace_schema_has_all_score_terms
- Load one entry from `decision_trace.jsonl`
- Assert JSON has keys: `entity_id`, `tick`, `routes`
- Assert each route in `routes` has: `route_kind`, `score`, `urgency`, `benefit`, `personality_bias`, `confidence_bonus`, `risk_penalty`, `blocker_penalty`, `selected`

### test_tick_index_o1_lookup (written in E22B)
- Write a mock `decision_trace.jsonl` with entries for tick 1, 2, 3
- Build tick index
- Assert byte-seek for tick 2 returns the correct entry without scanning file from start
- Assert `O(1)` behavior: assert no full-file scan (use mock or count seeks)

## API Tests (new file: tests/api/test_decision_api.py)

Written in E22C:

### test_decision_api_returns_score_breakdown
- POST a short run; GET `/api/v1/observability/entities/{id}/decisions?tick={N}`
- Assert response has ranked routes with `urgency`, `benefit`, etc. fields

### test_decision_api_range_query
- GET `/api/v1/observability/entities/{id}/decisions/range?from=1&to=3`
- Assert entries for ticks 1, 2, 3 returned

### test_decision_api_summary
- GET `/api/v1/observability/entities/{id}/decisions/summary`
- Assert response has route_kind distribution histogram

## Validation Commands
```bash
# Unit suite (fast)
pytest tests/unit/observability/test_decision_trace.py -x -v

# API tests
pytest tests/api/test_decision_api.py -x -v

# Existing observability tests must not regress
pytest tests/unit/observability/ -x -v -q
```
