---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-WEBSOCKET-OBSERVABILITY-TEST-WAITS-FOR-THE-WALK-EVENT-BY-DEADLINE-NOT-MESSAGE-COUNT
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-WEBSOCKET-OBSERVABILITY-TEST-WAITS-FOR-THE-WALK-EVENT-BY-DEADLINE-NOT-MESSAGE-COUNT

## Title
test_observability_websocket_suite step 5 waits for the synthetic walk event by wall-clock deadline, not by a count of 10 messages

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/api/test_observability_websocket.py::test_observability_websocket_suite[asyncio]` fails intermittently in CI ("Failed to receive movement event from stream"): MAIN run 39355039492 at abef4d682, twice on #676, once on #658.

## Scope
Step 5 subscribes with `category=movement`, POSTs one synthetic `walk` event, then read at most 10 messages (2 s each). The server runs a live simulation whose real movement events pass the same filter and sit ahead of the walk event in the subscriber's FIFO queue. Measured locally: 5 real movement events precede the walk event with one server, 7-8 with four servers on the host; at 10 or more the loop ends without seeing it. How many queue ahead depends on the POST latency and the tick rate, so a loaded runner overruns the count. The loop now runs to a 20 s wall-clock deadline (2 s per receive).

Not the cause: the starlette 1.9 / fastapi 0.143.5 / redis 8 move. The server side forwards in FIFO order with no timing change; the failing assertion is the message-count bound the earlier hotfix (TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE) left in place.

## Out of Scope
No change to src/api or src/observability; the server behaviour (real events delivered ahead of a posted one) is correct.

## Acceptance Criteria
- [x] Step 5 bounded by wall-clock deadline.
- [x] 20 consecutive local runs pass with 3 other server instances running alongside.

## Related Tickets
TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE, TCK-20260817-HOTFIX-WEBSOCKET-API-TESTS-ASYNCIO-MARKER-AND-HEARTBEAT-DRAIN

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
tests/api/test_observability_websocket.py

## Assumptions / Open Questions
Wall time of the test swings from 10 s to 60 s under load (observed again: two 60 s runs of 20); not explained by this ticket. The sleep(4) server start and the 20 s heartbeat deadline are the other time budgets in the test.

## Implementation Notes
Second cause, found while timing the suite: the test still started its server with `time.sleep(4.0)`, so on a loaded host the first connection was refused (6 of 10 timed runs failed with ConnectionRefused on 8019 or an early error). It now uses `tests.helpers.live_server.start_server`/`stop_server` (health-polling; TCK-20261014-SERVER-STARTING-TESTS-WAIT-FOR-HEALTH-INSTEAD-OF-SLEEPING-3-SECONDS) and asserts port 8019 is free first.

Finding: the port 8019 is hard-coded, so two runs of this test cannot share a host. A second `serve` on a busy port is not noticed by the health wait (the other server answers /health), so the test now fails loudly instead. A subscription_ack replaced by an `error` reply in another lane's run coincided with this session's servers holding 8019 (port clash symptom, not a regression).

Open, not addressed here: wall time swings from 10 s to 60 s (one 59 s pass in the last 10 loaded runs). The timed copy put the extra ~50 s after the start of step 6 (max-subscribers); it is investigated separately.
Reproduction probe counted messages before the walk event on an unloaded and a loaded host.

## Test Summary
Deadline loop: 20 of 20 passed under concurrent server load. With the health wait: 20 sequential runs with 8019 free before and after each, all passed (8.8-9.3 s); 10 more with other servers loading the host, all passed (one took 59 s: the open swing).

## Files Changed
tests/api/test_observability_websocket.py

## Completion Summary
Step 5 no longer gives up after 10 messages.
