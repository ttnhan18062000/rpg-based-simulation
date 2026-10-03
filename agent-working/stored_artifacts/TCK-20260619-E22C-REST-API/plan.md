# Plan — TCK-20260619-E22C-REST-API

**Ticket:** Epic 2.2C — REST API for decision trace endpoints
**Phase:** Plan
**Date:** 2026-06-20

---

## Dependency Map

```
Step 1 (presenter)
    └── Step 2 (route) depends on Step 1
        └── Step 3 (server registration) depends on Step 2
            └── Step 4 (tests) depends on Steps 1, 2, 3
                └── Step 5 (parity ledger) — deferred to Parity phase, depends on Step 4 passing
```

Steps 1–3 are sequentially dependent. Step 4 can be written in parallel with Step 3
but must be run after all three are in place.

---

## Step 1 — Create `src/api/presenters/decisions.py`

**Files to change:** `src/api/presenters/decisions.py` (new file)

**What to implement:**

A presenter module with three static methods. All inputs are plain dicts and
primitives (no domain entity types). No imports of `AuthoritativeState`,
`EntityState`, or any domain model are permitted — not even under `TYPE_CHECKING`.

```
present_tick_response(entity_id: str, tick: int, raw_entries: List[dict]) -> dict
```
- Filters `raw_entries` to rows where `entry["entity_id"] == entity_id` (string match).
- Returns:
  ```json
  {
    "entity_id": "<entity_id>",
    "tick": <tick>,
    "decisions": [
      {
        "route": "<str>",
        "score": <float>,
        "urgency": <float>,
        "benefit": <float>,
        "personality_bias": <float>,
        "confidence_bonus": <float>,
        "risk_penalty": <float>,
        "blocker_penalty": <float>,
        "selected": <bool>
      }
    ]
  }
  ```
- Source of each decision field: the `routes` list on each matching entry dict
  (field names match the 8-field score breakdown from INFRA-211).

```
present_range_response(entity_id: str, raw_entries_by_tick: Dict[int, List[dict]]) -> List[dict]
```
- `raw_entries_by_tick`: `{tick: [raw_entry, ...]}` for each tick in the range
  that returned non-empty results.
- For each tick, calls the same entity filter and field shaping as
  `present_tick_response`.
- Returns a list of tick objects (same shape as `present_tick_response` output),
  one per tick that has at least one decision after entity filtering.
- Ticks with no data after entity filtering are omitted from the list.

```
present_summary_response(entity_id: str, distribution: Dict[str, int], tick_count: int) -> dict
```
- `distribution`: route-kind → count, pre-aggregated by the route handler.
- `tick_count`: number of ticks that had at least one matching entry for
  `entity_id`.
- Returns:
  ```json
  {
    "entity_id": "<entity_id>",
    "tick_count": <int>,
    "route_kind_distribution": {"<route>": <count>, ...}
  }
  ```

**Scope guards:**
- Do NOT import any class from `src.core.*` or `src.engine.*`.
- Do NOT add Pydantic models here — shaped plain dicts only (consistent with
  the existing `StatePresenter` pattern).
- Do NOT add any I/O or path logic — pure data transformation.

**Acceptance criteria mapped here:**
- AC: All three endpoints return shaped read models (not raw `DecisionTraceIndex`
  dicts). Verified by test assertions checking that forbidden keys (raw domain
  model fields) are absent and required shaped keys are present.
- AC: INFRA-210 guard (`tests/architecture/test_api_read_model_guard.py`) passes
  after adding this file.

---

## Step 2 — Create `src/api/routes/decisions.py`

**Files to change:** `src/api/routes/decisions.py` (new file)

**What to implement:**

```python
from __future__ import annotations
import os
from typing import List
from fastapi import APIRouter, HTTPException, Query
from src.observability.reporting.history_query import sanitize_id
from src.observability.cognition.tick_index import DecisionTraceIndex
from src.api.presenters.decisions import (
    present_tick_response,
    present_range_response,
    present_summary_response,
)

router = APIRouter(prefix="/observability", tags=["Decisions"])
```

### Endpoint 1 — Single tick

```
GET /entities/{entity_id}/decisions
Query params: tick (int, required), run_id (str, required)
```

Handler logic:
1. Sanitize `run_id` and `entity_id` via `sanitize_id()`; catch `ValueError` →
   `HTTPException(400)`.
2. `run_dir = os.path.join("data/runs", run_id)`.
3. Guard: `if not os.path.isdir(run_dir): raise HTTPException(404, ...)`.
4. Construct `index = DecisionTraceIndex(run_dir)`.
5. `raw_entries = index.lookup(tick)`.
6. Return `present_tick_response(entity_id, tick, raw_entries)`.
   (Empty list after entity filter → 200 with `"decisions": []`.)

### Endpoint 2 — Range query

```
GET /entities/{entity_id}/decisions/range
Query params: from_tick (int, ge=0), to_tick (int, ge=0), run_id (str)
              max range cap: to_tick - from_tick <= 100 (le=100 on the diff)
```

Handler logic:
1. Sanitize `run_id`, `entity_id`; catch `ValueError` → 400.
2. Validate `to_tick >= from_tick`; if not → `HTTPException(400, "to must be >= from")`.
3. Validate `(to_tick - from_tick) <= 100`; if not → `HTTPException(400, "range exceeds 100-tick cap")`.
4. `run_dir` guard (same as endpoint 1) → 404 if missing.
5. Construct `index = DecisionTraceIndex(run_dir)`.
6. Loop `for tick in range(from_tick, to_tick + 1): raw_entries_by_tick[tick] = index.lookup(tick)`.
7. Return `present_range_response(entity_id, raw_entries_by_tick)`.

FastAPI query param names: use `from_tick: int = Query(alias="from")` and
`to_tick: int = Query(alias="to")` so the URL uses `?from=3&to=7`.

### Endpoint 3 — Summary

```
GET /entities/{entity_id}/decisions/summary
Query params: run_id (str)
```

Handler logic:
1. Sanitize `run_id`, `entity_id`; catch `ValueError` → 400.
2. `run_dir` guard → 404 if missing.
3. Construct `index = DecisionTraceIndex(run_dir)`.
4. Call `index._load()` to populate `index._index`.
5. Iterate `index._index.keys()` to get all available ticks.
6. For each tick, call `index.lookup(tick)`, filter entries where
   `entry["entity_id"] == entity_id`, collect the `route` field from each
   item in `entry["routes"]` where `item["selected"] == True`.
7. Build `distribution: Dict[str, int]` (route-kind → count of selected decisions
   for this entity across all ticks). Count `tick_count` = number of ticks
   with at least one matching entry.
8. Return `present_summary_response(entity_id, distribution, tick_count)`.

**Scope guards:**
- Do NOT call `index.append_entry()`, `index.rebuild()`, or any write path.
- Do NOT import `RunArtifactRepository`.
- Do NOT return raw dicts from `DecisionTraceIndex.lookup()` — always pass
  through the presenter.
- The `from` query alias: FastAPI `Query(alias="from")` requires Python param
  named `from_tick` (reserved word guard).

**Acceptance criteria mapped here:**
- AC: GET single-tick returns `{"entity_id", "tick", "decisions": [...]}` shaped.
- AC: GET range returns list of tick objects; empty ticks omitted.
- AC: GET summary returns `{"entity_id", "tick_count", "route_kind_distribution"}`.
- AC: 400 on invalid `run_id` or `entity_id`.
- AC: 404 on missing run directory.
- AC: 400 when range > 100 ticks or `from > to`.
- AC: 200 + empty list when tick absent from index.

---

## Step 3 — Register router in `src/api/server.py`

**Files to change:** `src/api/server.py`

Add the following block immediately after the `behavior` router registration
(around line 72 in the current file):

```python
from src.api.routes import decisions
app.include_router(decisions.router, prefix="/api/v1")
```

This produces full paths:
- `/api/v1/observability/entities/{entity_id}/decisions`
- `/api/v1/observability/entities/{entity_id}/decisions/range`
- `/api/v1/observability/entities/{entity_id}/decisions/summary`

**Scope guards:**
- Touch only the router registration block; do not alter any existing route,
  middleware, lifespan, or health handler.
- The `decisions` router must be registered after `behavior` to preserve
  ordering. It must NOT be registered before `history` (which comes first at
  line 66).

**Acceptance criteria mapped here:**
- AC: All three full URL paths are resolvable.
- AC: Existing routes (`history`, `search`, `behavior`) are unaffected
  (regression: `tests/api/test_cognition_history_api.py` and
  `tests/api/test_phase27_behavior_query_api.py` still pass).

---

## Step 4 — Create `tests/api/test_decision_api.py`

**Files to change:** `tests/api/test_decision_api.py` (new file)

**Pattern:** `@pytest.mark.anyio`, direct handler import, patch at
`src.api.routes.decisions.<symbol>`.

### Test group 1 — Single tick (`test_decision_api_returns_score_breakdown`)

Setup:
- `patch("src.api.routes.decisions.os.path.isdir", return_value=True)`.
- `patch("src.api.routes.decisions.DecisionTraceIndex")` — mock instance where
  `lookup(5)` returns a list with one entry:
  ```python
  {"entity_id": "e1", "tick": 5, "routes": [
      {"route": "gather", "score": 0.82, "urgency": 0.5, "benefit": 0.6,
       "personality_bias": 0.1, "confidence_bonus": 0.05,
       "risk_penalty": 0.02, "blocker_penalty": 0.0, "selected": True}
  ]}
  ```

Assertions:
- `response["entity_id"] == "e1"`, `response["tick"] == 5`.
- `response["decisions"]` is a list with one entry.
- Decision entry has keys: `route`, `score`, `selected` (and the full 8 fields).
- No forbidden keys (e.g., `_index`, `_trace_path`) in response.

Additional cases (same test function or separate parametrized):
- 404 path: `isdir` returns False → handler raises HTTPException 404.
- 400 path: `run_id = "../evil"` → `sanitize_id` raises `ValueError` → handler
  raises HTTPException 400.
- 200-empty: `lookup` returns `[]` → response `{"decisions": []}`.

### Test group 2 — Range (`test_decision_api_range_query`)

Setup:
- `patch isdir True`, mock `DecisionTraceIndex` where `lookup(tick)` returns one
  entity-e1 entry for ticks 3,4,5 and `[]` for 6,7.

Assertions:
- Response is a list of 3 objects (only ticks 3,4,5 have data).
- Each item has `tick`, `entity_id`, `decisions`.

Additional cases:
- 400: `from_tick=7, to_tick=3` (from > to).
- 400: `from_tick=0, to_tick=101` (range > 100).
- 404: `isdir` returns False.
- 400: invalid `entity_id` characters.

### Test group 3 — Summary (`test_decision_api_summary`)

Setup:
- `patch isdir True`.
- Mock `DecisionTraceIndex` where `_load()` is a no-op, `_index = {1: 0, 2: 100, 3: 200}`.
- `lookup(tick)` for each tick returns one entity-e1 entry with one selected route.

Assertions:
- Response has `entity_id`, `tick_count` (int >= 0), `route_kind_distribution`
  (dict of str → int).
- Values are derived from shaped presenter, not raw dicts.

Additional cases:
- 404: `isdir` returns False.
- Empty index: `_index = {}` → `tick_count = 0`, `route_kind_distribution = {}`.

**Scope guards:**
- Do NOT mock the presenter itself — it is exercised through the handler.
- Mock `os.path.isdir` at `src.api.routes.decisions.os.path.isdir`,
  not at the `os` module level.
- All async test functions must have `@pytest.mark.anyio`.
- Do NOT make HTTP requests via a TestClient — call handler functions directly.

**Acceptance criteria mapped here:**
- All three endpoint ACs (shape, error codes, empty-list behavior).
- Regression: INFRA-210 guard passes (`tests/architecture/test_api_read_model_guard.py`).

---

## Step 5 — Update parity ledger (INFRA-213) — DEFERRED to Parity phase

**Files to change:** `docs/parity_ledger/infrastructure.yaml`

**What to add:**
```yaml
- id: INFRA-213
  text: >
    REST endpoints for decision trace exist: single-tick lookup
    (/entities/{id}/decisions?tick=N), range query (/decisions/range?from=A&to=B),
    and summary histogram (/decisions/summary). All responses are shaped through
    src/api/presenters/decisions.py. Missing run → 404. Invalid id → 400.
    Range > 100 ticks → 400. Empty tick → 200 with empty list.
  status: verified
  priority: P1
  v2_evidence: "src/api/routes/decisions.py; src/api/presenters/decisions.py"
  test_path: tests/api/test_decision_api.py
  divergence_note: ""
```

This step is deferred to the Parity phase (after tests pass). It is a Definition
of Done requirement.

---

## Scope Guards (Global)

- Do NOT modify `src/observability/cognition/tick_index.py`.
- Do NOT modify `src/observability/reporting/history_query.py`.
- Do NOT add `decision_trace` as a key to `RunArtifactRepository.resolve_path`.
- Do NOT alter any existing presenter, route, or test file.
- Do NOT call any write-path method (`append_entry`, `rebuild`) from the route.
- Do NOT use `anyio` in tests without `@pytest.mark.anyio`.
- Do NOT expose `_index`, `_trace_path`, or `_index_path` in API responses.

---

## Scoped Test Commands (run after Step 4)

```bash
pytest tests/api/test_decision_api.py -v
pytest tests/architecture/test_api_read_model_guard.py -v
pytest tests/unit/observability/test_decision_trace.py -v
pytest tests/api/test_cognition_history_api.py tests/api/test_phase27_behavior_query_api.py -v
```

---

## Deviations

### Naming correction: `routes`/`route_kind` (not `decisions`/`route`)

The plan's Step 1 spec used `"decisions"` as the response array key and `"route"` as the route-kind field name. The ticket Acceptance Criteria (authoritative) specifies `"routes"` and `"route_kind"` respectively. Implementation follows the ticket AC:

- Response key: `routes` (not `decisions`)
- Route-kind field: `route_kind` (not `route`)
- `entity_id` type: `int` (not `str`) — matches ticket example `"entity_id": 7`

### Presenter signature adjusted

The plan's `present_range_response` took `Dict[int, List[dict]]` (tick-keyed dict). Implementation passes a flat `List[dict]` (all entries from all ticks concatenated) and the presenter groups by tick internally. This avoids tick-keyed dict construction in the route handler and keeps the handler loop simple.

### `present_summary_response` argument order

Plan listed `(entity_id, distribution, tick_count)` but implementation uses `(entity_id, tick_count, distribution)` to match the return shape ordering logically.

All other design decisions were pre-resolved in the investigation phase.
