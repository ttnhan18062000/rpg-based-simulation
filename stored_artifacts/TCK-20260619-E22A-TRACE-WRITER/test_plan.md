---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22A-TRACE-WRITER
artifact_type: test_plan
tags: [decision-trace, observability, tests]
---

# Test Plan: TCK-20260619-E22A-TRACE-WRITER

## Regression Surface (existing tests that must pass)
- `tests/unit/observability/test_phase17_decision_trace_contract.py` — DecisionTrace contract
- `tests/unit/observability/test_phase17_decision_trace_validator.py` — DecisionTraceValidator
- `tests/unit/observability/cognition/` — all cognition recorder tests
- `tests/unit/domains/adventure/` — AdventureRouteScorer, AdventureDecisionService tests (if present)

## New Tests Required (per AC)

### File: `tests/unit/observability/test_decision_trace.py`

#### `test_decision_trace_written_in_light_mode`
- Set `ObservabilityConfig` to LIGHT mode
- Create `DecisionTraceWriter` with a temp dir
- Create 2-3 `AdventureRouteOption` scored instances
- Call `writer.write_trace(entity_id=1, tick=5, scored_routes=[...])`
- Assert file `decision_trace.jsonl` exists in temp dir
- Assert each line is valid JSON
- Assert each line has `entity_id`, `tick`, `routes` keys
- Assert `routes` length ≤ 5

#### `test_decision_trace_schema_has_all_score_terms`
- Create a scored `AdventureRouteOption` with all fields set
- Call `writer.write_trace(entity_id=2, tick=3, scored_routes=[route])`
- Parse written JSON
- Assert route entry has all 8 fields: `urgency`, `benefit`, `personality_bias`,
  `confidence_bonus`, `risk_penalty`, `blocker_penalty`, `score`, `selected`
- Fields `urgency`, `benefit`, `personality_bias`, `confidence_bonus`, `risk_penalty`,
  `blocker_penalty` come from extended `AdventureRouteOption` fields

#### `test_decision_trace_not_written_in_off_mode`
- Set `ObservabilityConfig` to OFF mode
- Confirm writer guard: if mode is OFF, `write_trace()` is a no-op
- Assert no file created

#### `test_decision_trace_caps_at_5_routes`
- Pass 10 scored routes to `write_trace()`
- Assert written `routes` array has exactly 5 entries

#### `test_decision_trace_append_mode`
- Write two traces to the same writer
- Assert file has exactly 2 lines (append, not overwrite)

#### `test_adventure_decision_phase_wires_writer` (integration)
- Create a mock `DecisionTraceWriter`
- Call `AdventureDecisionPhase.apply(state, trace_writer=mock_writer)`
- Assert `mock_writer.write_trace` was called for eligible heroes

## Scoped Pytest Commands

```bash
# New tests (primary AC)
pytest tests/unit/observability/test_decision_trace.py -x -v

# Regression — observability unit
pytest tests/unit/observability/ -x -v -q --ignore=tests/unit/observability/warehouse

# Regression — adventure domain
pytest tests/unit/domains/adventure/ -x -v -q 2>/dev/null || true

# Full scoped run
pytest tests/unit/observability/test_decision_trace.py tests/unit/observability/test_phase17_decision_trace_contract.py tests/unit/observability/test_phase17_decision_trace_validator.py -v
```

## Anti-Drift Test Guards
- Test must assert `execute_brain()` in `cognition.py` is NOT imported by `decision_trace_writer.py`
- Test must assert `write_trace()` does not raise even when mode is OFF (graceful no-op)
- Test must assert `AdventureRouteOption` still passes existing schema validation after field extension
