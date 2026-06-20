---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31D-REST-API
phase: open
date: 2026-06-20
tags: [scenario-runtime, rest-api, observability, phase-3]
---

# TCK-20260619-E31D-REST-API

## Title
Epic 3.1D · Scenario Runtime REST API

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ScenarioRuntimeService` and checkpoint are headless. This ticket exposes them via 3 REST endpoints: status, checkpoint, and restore — making the runtime inspectable and controllable via API.

**Requires:** TCK-20260619-E31C-CHECKPOINT

## Scope

Three endpoints in new `src/api/routes/scenarios.py`:

```
GET  /api/v1/scenarios/{id}/status
     → {tick, objective_state, alive_entity_count, key_metrics: {...}}

POST /api/v1/scenarios/{id}/checkpoint
     body: {name: "checkpoint_name"}
     → {path: "checkpoints/...", tick: N}

POST /api/v1/scenarios/{id}/restore/{checkpoint_name}
     → {tick: N, objective_state: "RUNNING"}
```

Follow existing route patterns in `src/api/routes/` (read `behavior.py` for conventions).
Use presenter layer (`src/api/presenters/`) to shape responses — do not return raw domain objects.
Register in `src/api/server.py`.

Also: create `docs/engine/scenario_runtime_contract.md` (service lifecycle, objective state machine, checkpoint format, REST API contract). Run `make knowledge-index-update` after.

## Acceptance Criteria
- `GET /api/v1/scenarios/{id}/status` returns `{tick, objective_state, alive_entity_count}`
- `test_status_endpoint_returns_live_state` passes
- `docs/engine/scenario_runtime_contract.md` exists
- `docs/parity_ledger/infrastructure.yaml` checkpoint entry updated to `verified`

## Related Tickets
- TCK-20260619-E31-SCENARIO-RUNTIME (parent epic)
- TCK-20260619-E31C-CHECKPOINT (required)
- TCK-20260619-E32-CAMPAIGN-RUNTIME (unlocked after this)

## Related Code Areas
- `src/api/routes/scenarios.py` (new)
- `src/api/server.py` (register router)
- `src/api/presenters/scenarios.py` (new presenter)
- `tests/api/test_scenario_runtime_api.py` (new)

## Test Summary
```bash
pytest tests/api/test_scenario_runtime_api.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
