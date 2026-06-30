---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-WIRE-SERVER
phase: open
date: 2026-06-30
tags: [simulation-quality, simq, api, server, wiring]
---

# TCK-20260630-SIMQ-WIRE-SERVER

## Title
Call set_quality_hub() in server lifespan so REST quality endpoints return live data

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
D20 audit (G2): `set_quality_hub()` is defined in `src/api/dependencies.py:22–24` but
never called from any execution path. As a result `get_quality_hub()` always returns
`None`, and every REST quality endpoint silently returns a disabled-hub response for the
entire lifetime of the server process. The shutdown handler in `server.py` already reads
`get_quality_hub()` to write the final report — it just has no hub to read because
nothing called `set_quality_hub()` at startup.

## Scope
- Call `set_quality_hub(hub)` in the `lifespan` context manager in `src/api/server.py`
  after the `V2EngineManager` is started and the hub is available
- The hub should be the same hub instance that the engine manager uses for its run
- On shutdown, `get_quality_hub()` already writes the final report — no change needed there

## Out of Scope
- Kernel-side quality_fn wiring (→ TCK-20260630-SIMQ-WIRE-KERNEL)
- Calibration (→ TCK-20260630-SIMQ-RECALIBRATE)
- WebSocket push / streaming quality updates
- Changes to the REST route implementations themselves

## Acceptance Criteria
1. `GET /api/v1/quality/pillars` returns live pillar data (not the disabled-hub response)
   during an active server run after this ticket is applied
2. `GET /api/v1/quality/report` returns a populated `QualityReport` at run end
3. No crash if SimQ is disabled (`SIMQ_ENABLED=false`) — `set_quality_hub(None)` or
   equivalent guard handles the disabled path gracefully
4. Existing API tests pass (`pytest tests/api/ -x`)

## Related Tickets
- TCK-20260628-SIMQ-EPIC — parent epic
- TCK-20260628-SIMQ-E5-API — original API implementation
- TCK-20260630-SIMQ-WIRE-KERNEL — kernel-side wiring (parallel, independent)

## Related Docs
- `docs/audits/D20_simq_integration.md` — audit finding G2
- `docs/simulation_quality/quality_scoring_contract.md` — §10 API surface

## Related Code Areas
- `src/api/server.py` — lifespan context manager (startup/shutdown)
- `src/api/dependencies.py:22–27` — `set_quality_hub()` / `get_quality_hub()`
- `src/api/engine_manager.py` — `V2EngineManager` which owns the hub reference

## Assumptions / Open Questions
- The hub is constructed by `V2EngineManager` or passed to it at construction time.
  Confirm hub ownership before calling `set_quality_hub()`.
- If the server is started without SimQ enabled, `set_quality_hub(None)` should be a
  no-op (or `set_quality_hub` should accept `None` without error).

## Implementation Notes
Minimal change: in `server.py` lifespan, after `manager.start()`, call:
```python
from src.api.dependencies import set_quality_hub
set_quality_hub(manager.quality_hub)   # or however hub is exposed from manager
```
The exact attribute name on the manager needs verification before implementation.

## Test Summary
- Integration: start server, run 20 ticks, GET /api/v1/quality/pillars → non-empty response
- Regression: existing API tests pass

## Files Changed
(to be filled in after implementation)

## Completion Summary
(to be filled in after implementation)
