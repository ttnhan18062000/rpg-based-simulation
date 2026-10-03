# Test Plan — TCK-20260619-E22C-REST-API

**Ticket:** Epic 2.2C — REST API for decision trace endpoints
**Phase:** Investigate
**Date:** 2026-06-20

---

## Regression Surface

These existing tests must continue to pass after implementation. All touch adjacent code or architecture guards that decisions.py could accidentally violate.

| Test | File | Why it matters |
|---|---|---|
| `test_no_api_route_directly_imports_authoritative_state` | `tests/architecture/test_api_read_model_guard.py` | INFRA-210 guard — fires if decisions.py imports domain entities |
| `test_decision_trace_written_in_light_mode` | `tests/unit/observability/test_decision_trace.py` | INFRA-211 — verifies writer shape matches what API will surface |
| `test_tick_index_o1_lookup` | `tests/unit/observability/test_decision_trace.py` | INFRA-212 — verifies `DecisionTraceIndex.lookup()` returns correct list |
| All `tests/api/test_cognition_history_api.py` tests | `tests/api/test_cognition_history_api.py` | History route must not be disturbed by server.py registration change |
| All `tests/api/test_phase27_behavior_query_api.py` tests | `tests/api/test_phase27_behavior_query_api.py` | Behavior route must not be disturbed |

---

## New Tests Required

**File:** `tests/api/test_decision_api.py`

All async test functions use `@pytest.mark.anyio`. Dependencies are patched at `src.api.routes.decisions.<symbol>`. Handler functions are imported directly and called with keyword arguments.

---

### Test 1 — `test_decision_api_returns_score_breakdown`

**AC:** Endpoint 1 returns shaped score breakdown for a valid entity/tick.

```
GET /api/v1/observability/entities/{entity_id}/decisions?tick=5&run_id=run_abc
```

Setup:
- Patch `src.api.routes.decisions.DecisionTraceIndex` to return a mock where `lookup(5)` returns:
  ```python
  [
      {"entity_id": "e1", "tick": 5, "routes": [
          {"route": "gather", "score": 0.82, "urgency": 0.5, "benefit": 0.6,
           "personality_bias": 0.1, "confidence_bonus": 0.05,
           "risk_penalty": 0.02, "blocker_penalty": 0.0, "selected": True}
      ]}
  ]
  ```
- `entity_id = "e1"`, `run_id = "run_abc"`, `tick = 5`

Assertions:
- Response is a dict (not a raw list)
- `response["entity_id"] == "e1"`
- `response["tick"] == 5`
- `response["decisions"]` is a list with at least one entry
- Each entry has keys: `route`, `score`, `selected` (shaped by presenter — not raw dict passthrough)
- No `AuthoritativeState` or `EntityState` key present in response

Also test 404 when `os.path.isdir(run_dir)` returns False.
Also test 400 when `run_id` contains path traversal characters (`../evil`).
Also test 200-empty when tick is absent from index (`lookup` returns `[]`).

---

### Test 2 — `test_decision_api_range_query`

**AC:** Endpoint 2 returns aggregated decisions for a tick range.

```
GET /api/v1/observability/entities/{entity_id}/decisions/range?from=3&to=7&run_id=run_abc
```

Setup:
- Patch `DecisionTraceIndex` mock: `lookup(tick)` returns one entry for each of ticks 3,4,5; returns `[]` for 6,7.
- `entity_id = "e1"`, `from_tick = 3`, `to_tick = 7`, `run_id = "run_abc"`

Assertions:
- Response contains entries only for ticks 3–5 (ticks with data)
- Response is shaped (not raw dicts)
- Ticks with no data are omitted or represented as empty — consistent with presenter contract

Also test 400 when `from_tick > to_tick`.
Also test 400 when range exceeds max-range cap (e.g. `from=0, to=200` if cap is 100).
Also test 404 for missing run_dir.
Also test 400 for invalid `entity_id` characters.

---

### Test 3 — `test_decision_api_summary`

**AC:** Endpoint 3 returns a histogram/summary over all ticks.

```
GET /api/v1/observability/entities/{entity_id}/decisions/summary?run_id=run_abc
```

Setup:
- Patch `DecisionTraceIndex` mock: `_index` (or exposed via `list_ticks()` if available) contains ticks {1,2,3}. `lookup(tick)` returns one entity-e1 entry per tick with varying routes.

Assertions:
- Response contains `total_decisions` (int, >= 0)
- Response contains `ticks_with_data` (int)
- Response contains `top_routes` (list of `{"route": str, "count": int}`)
- All values derived from shaped presenter — no raw dict keys from `DecisionTraceIndex`

Also test 404 for missing run_dir.
Also test summary returns zeros/empty when no trace data exists (empty index).

---

## Scoped Pytest Commands

Run before claiming completion. Do NOT run `pytest tests/` (full suite).

```bash
# New API tests
pytest tests/api/test_decision_api.py -v

# Regression: architecture guard
pytest tests/architecture/test_api_read_model_guard.py -v

# Regression: observability unit tests (INFRA-211, INFRA-212)
pytest tests/unit/observability/test_decision_trace.py -v

# Regression: adjacent API routes
pytest tests/api/test_cognition_history_api.py tests/api/test_phase27_behavior_query_api.py -v

# Combined scoped run (all of the above, exclude slow)
pytest tests/api/test_decision_api.py \
       tests/architecture/test_api_read_model_guard.py \
       tests/unit/observability/test_decision_trace.py \
       tests/api/test_cognition_history_api.py \
       tests/api/test_phase27_behavior_query_api.py \
       -v -m "not slow"
```

---

## Anti-Drift Test Guards

1. **INFRA-210 guard** (`test_no_api_route_directly_imports_authoritative_state`) — must pass. If it fails after adding `src/api/routes/decisions.py`, the route has a forbidden import. Fix: move any domain type imports under `TYPE_CHECKING`.

2. **Presenter isolation** — `test_decision_api_returns_score_breakdown` must mock at the `DecisionTraceIndex` boundary, not at the presenter. The presenter is exercised through the handler to verify it shapes correctly.

3. **anyio marker required** — all `async def test_*` functions must have `@pytest.mark.anyio`. Missing marker causes silent skip, not failure — verify via `pytest --collect-only`.

4. **No `os.path.exists` bypass in tests** — tests must mock `os.path.isdir` (or `os.path.exists`) at `src.api.routes.decisions.os.path.isdir` to control 404 path without writing to disk.

5. **Parity entry INFRA-213** — once `test_decision_api.py` passes, add INFRA-213 to `docs/parity_ledger/infrastructure.yaml` with `test_path: tests/api/test_decision_api.py` and `status: verified`. This is a Definition of Done requirement for the ticket.
