---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-REST-MAP-STATIC-STATS
phase: open
date: 2026-08-21
tags: [api-design, engine]
---

# TCK-20260821-REST-MAP-STATIC-STATS

## Title
Add /api/v1/map, /api/v1/static, /api/v1/stats REST routes

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Five REST routes the frontend calls do not exist on the real backend at all: /api/v1/map, /api/v1/static, /api/v1/stats, /api/v1/speed, /api/v1/clear_events. The author wants the map/static/stats routes built (wrapping the new presenter methods), including adding total_spawned/total_deaths counters to V2EngineManager, which V1 had but V2 genuinely lacks today.

## Scope
- Add GET /api/v1/map wrapping StatePresenter.present_map
- Add GET /api/v1/static wrapping StatePresenter.present_static
- Add GET /api/v1/stats returning {tick,world_day,alive_count,total_spawned,total_deaths,running,paused}
- Add _total_spawned/_total_deaths counters to V2EngineManager, incremented once per tick via new_ids/dead_ids set-diff (comparing state.entities.keys() before/after kernel.tick_once()), following V1's alive_before/alive_after pattern
- Reset counters to 0 on V2EngineManager.reset()
- Follow existing router pattern (APIRouter+Depends+get_engine_manager, response_model, 503 when not ready) from src/api/routes/economy.py

## Out of Scope
- /api/v1/speed and /api/v1/clear_events routes -- explicitly deferred to HUD-tied scope, must not be added even though found in the same grep
- present_map/present_static implementation itself (that's a hard dependency on TCK-20260821-PRESENT-MAP-STATIC)

## Acceptance Criteria
- [ ] GET /api/v1/map returns 200 {width,height,grid} RLE-encoded, 503 when manager.latest_state is None
- [ ] GET /api/v1/static returns 200 StaticData-shaped payload sourced only via StatePresenter.present_static, never raw AuthoritativeState fields
- [ ] GET /api/v1/stats returns 200 {tick,world_day,alive_count,total_spawned,total_deaths,running,paused}, counters non-decreasing across ticks, reset to 0 after V2EngineManager.reset()
- [ ] V2EngineManager gains _total_spawned/_total_deaths incremented once per tick by len(new_ids)/len(dead_ids) (same alive_before/alive_after set-diff pattern as V1), verified by a test asserting counters increase after spawns/deaths and zero on reset()
- [ ] new assertions added to the existing tests/api/test_rest_parity.py::test_api_rest_parity rather than a new subprocess-spinning test

## Related Tickets
- TCK-20260821-PRESENT-MAP-STATIC
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/engine/contracts/frontend.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/server.py
- src/api/engine_manager.py
- src/api/presenters/state_presenter.py
- src/api/routes/economy.py
- src/api/routes/state.py
- tests/api/test_rest_parity.py

## Assumptions / Open Questions
- V2's tick loop currently has no new_ids/dead_ids diffing at all -- this is a real addition to the hot tick path, not incidental wiring

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
