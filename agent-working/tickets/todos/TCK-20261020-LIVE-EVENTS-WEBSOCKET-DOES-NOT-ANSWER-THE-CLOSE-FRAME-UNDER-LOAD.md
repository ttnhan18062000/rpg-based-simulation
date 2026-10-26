---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-LIVE-EVENTS-WEBSOCKET-DOES-NOT-ANSWER-THE-CLOSE-FRAME-UNDER-LOAD
phase: open
date: 2026-10-20
tags: [observability]
---

# TCK-20261020-LIVE-EVENTS-WEBSOCKET-DOES-NOT-ANSWER-THE-CLOSE-FRAME-UNDER-LOAD

## Title
Under host load, the live-events websocket server sometimes never answers a client's close frame, so each idle client waits out its 10 s close_timeout

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Lane C found this on 2026-10-20 while fixing the observability websocket test flake (PR #679, TCK-20261020-WEBSOCKET-OBSERVABILITY-TEST-WAITS-FOR-THE-WALK-EVENT-BY-DEADLINE-NOT-MESSAGE-COUNT). In tests/api/test_observability_websocket.py, the final `await client.close()` loop over the 10 idle step-6 clients took 50.0 s in a slow run, against about 0.1 s in a fast one. 5 of the 10 clients each waited exactly 10.0 s, which is the websockets client close_timeout. The server never answered their close frame. It happened in about 1 of 4 runs with other servers loading the host and 0 of 8 unloaded. The test still passes, only slower. The server side is `stream_live_events_ws`, where one task both sends and receives per socket. It was not read in that ticket.

## Scope
- Read `stream_live_events_ws` and the per-socket send/receive task. Find why a close frame goes unanswered under load: for example, a send blocked on a full queue or a slow drain while the receive side never sees the close, or a missing close handling path.
- Fix it on the server side so the close handshake completes promptly under load.
- Add a test that closes N idle subscribers under load and asserts the close completes well inside close_timeout.

## Out of Scope
- Hiding it in the test with a short close_timeout or by aborting the clients (Lane C's rejected mitigation).
- The hard-coded test port 8019.

## Acceptance Criteria
- Under the loaded condition (other servers running), 0 of 20 runs show a close wait of 10 s or more.
- The test suite's wall time stays near 9 s under load.
- No change to event delivery order or content.

## Related Tickets
- TCK-20261020-WEBSOCKET-OBSERVABILITY-TEST-WAITS-FOR-THE-WALK-EVENT-BY-DEADLINE-NOT-MESSAGE-COUNT (PR #679)
- TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE

## Related Docs
- docs/combat/observability_rulebook.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/api (stream_live_events_ws)
- tests/api/test_observability_websocket.py

## Assumptions / Open Questions
- Is the starlette 1.x websocket close behaviour involved (#646)? Check it; it is not assumed.

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary
