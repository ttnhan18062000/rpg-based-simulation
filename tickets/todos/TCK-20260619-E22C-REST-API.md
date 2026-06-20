---
status: open
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22C-REST-API
phase: open
date: 2026-06-20
tags: [decision-explanation, observability, rest-api, phase-2]
---

# TCK-20260619-E22C-REST-API

## Title
Epic 2.2C · Decision Explanation REST Endpoints

## Status
OPEN

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
- For range queries, iterate ticks A..B and call `lookup()` per tick.
- For summary, scan the full file once (acceptable — summary is a heavy query).
- Guard against missing `decision_trace.jsonl` with a 404 response: `{"error": "no decision trace for this run"}`.
- After docs written: run `make knowledge-index-update`.

## Test Summary
```bash
pytest tests/api/test_decision_api.py -x -v
pytest tests/unit/observability/ -x -v -q  # regression
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
