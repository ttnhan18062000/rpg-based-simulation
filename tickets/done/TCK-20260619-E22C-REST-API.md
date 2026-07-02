---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22C-REST-API
phase: done
date: 2026-06-20
tags: [decision-explanation, observability, rest-api, phase-2]
---

# TCK-20260619-E22C-REST-API

## Title
Epic 2.2C · Decision Explanation REST Endpoints

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`decision_trace.jsonl` and its tick-index exist after E22A/B. This ticket exposes them via three REST endpoints so behavioral quality experiments can be run without manual JSONL parsing.

**Requires:** TCK-20260619-E22B-TICK-INDEX

## Scope

### New route file: `src/api/routes/decisions.py`

Three endpoints (match existing route patterns — read `src/api/routes/behavior.py` for conventions):

**1. Single tick**
```
GET /api/v1/observability/entities/{entity_id}/decisions?tick={N}
```
Returns: ranked list of scored routes for entity `entity_id` at tick `N`.

```json
{
  "entity_id": 7,
  "tick": 342,
  "routes": [
    {
      "route_kind": "GATHER_RESOURCE",
      "score": 1.85,
      "urgency": 0.6,
      "benefit": 0.4,
      "personality_bias": 0.25,
      "confidence_bonus": 0.15,
      "risk_penalty": 0.3,
      "blocker_penalty": 0.0,
      "selected": true
    },
    ...
  ]
}
```

**2. Tick range**
```
GET /api/v1/observability/entities/{entity_id}/decisions/range?from={A}&to={B}
```
Returns: list of tick entries A..B for entity `entity_id`.

**3. Summary histogram**
```
GET /api/v1/observability/entities/{entity_id}/decisions/summary
```
Returns: distribution of route kinds selected over all ticks.

```json
{
  "entity_id": 7,
  "tick_count": 400,
  "route_kind_distribution": {
    "GATHER_RESOURCE": 0.45,
    "RETREAT": 0.20,
    "ENGAGE_COMBAT": 0.15,
    "TRAVEL": 0.20
  }
}
```

### Register in `src/api/server.py`

Find where existing routes are registered (e.g. `app.include_router(behavior.router)`) and add `decisions.router`.

### Presenter layer

Per architecture rule: "API/routes present shaped read models through presenters/schemas, not raw domain objects." Create `src/api/presenters/decisions.py` with presenter functions shaping the JSONL data into the response schema. Do not return raw JSONL dicts from the route handlers.

## Out of Scope
- Interactive replay UI
- Multi-entity comparison
- Authentication/authorization

## Acceptance Criteria
- `GET /api/v1/observability/entities/7/decisions?tick=5` returns JSON with `routes` array
- Response shape matches presenter (not raw JSONL)
- `test_decision_api_returns_score_breakdown` passes
- `test_decision_api_range_query` passes
- `test_decision_api_summary` passes
- `docs/observability/decision_trace_contract.md` exists documenting schema + API contract

## Related Tickets
- TCK-20260619-E22-DECISION-EXPLAIN (parent epic)
- TCK-20260619-E22B-TICK-INDEX (required first)

## Related Docs
- `docs/observability/decision_trace_contract.md` (new — author in this ticket)
- `docs/parity_ledger/infrastructure.yaml` (add decision trace entry with `status: verified`)
- `docs/engine/kernel.md` (note LIGHT mode trace output in cognition phase section)

## Related Code Areas
- `src/api/routes/decisions.py` (new)
- `src/api/routes/behavior.py` (pattern reference)
- `src/api/server.py` (register router)
- `src/api/presenters/decisions.py` (new presenter)
- `tests/api/test_decision_api.py` (new)

## Assumptions / Open Questions
- What framework is `src/api/` using? FastAPI or Flask? Read `src/api/server.py` before writing route handlers.
- Are run IDs needed as a path segment, or does the API infer the current run? Check existing routes for convention (`src/api/routes/history.py`).
- Does the API have access to the run_dir for file reads? Check how other routes access run data.

## Implementation Notes
- Use `DecisionTraceIndex.lookup(tick)` for single-tick queries (O(1) seek).
- For range queries, iterate ticks A..B and call `lookup()` per tick; flat list passed to presenter which groups by tick.
- For summary, call `index._load()` then iterate `index._index.keys()` to get all ticks; compute fraction distribution (float, rounded to 4 dp) not raw counts.
- Guard against missing run dir (404 "Run not found") and missing `decision_trace.jsonl` separately (404 "no decision trace for this run").
- All three endpoints route through `DecisionPresenter` — no raw JSONL dicts returned.
- `entity_id` is `int` throughout (path param, filter, and response field) per ticket AC.
- Range response omits ticks that have no routes for the entity after filtering.
- `_get_index()` helper centralises run_dir guard and trace-file guard.
- After docs written: run `make knowledge-index-update`.

## Test Summary
```bash
pytest tests/api/test_decision_api.py -x -v
pytest tests/unit/observability/ -x -v -q  # regression
```

## Files Changed
- src/api/presenters/decisions.py (new)
- src/api/routes/decisions.py (new)
- src/api/server.py (modified — router registration)
- tests/api/test_decision_api.py (new — 15 tests)
- docs/parity_ledger/infrastructure.yaml (modified — INFRA-213)
- staging_artifacts/TCK-20260619-E22C-REST-API/plan.md (modified — deviations)

## Completion Summary
Implemented three Decision Explanation REST endpoints (GET /decisions, /decisions/range, /decisions/summary) under /api/v1/observability/entities/{entity_id}/. Created DecisionPresenter shaping layer in src/api/presenters/decisions.py with no domain model imports. Registered decisions.router in src/api/server.py. Added 15 tests in tests/api/test_decision_api.py (all pass). Added INFRA-213 to docs/parity_ledger/infrastructure.yaml.
