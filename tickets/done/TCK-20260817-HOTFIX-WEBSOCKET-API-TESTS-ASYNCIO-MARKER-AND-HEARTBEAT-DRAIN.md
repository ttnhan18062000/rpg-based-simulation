---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-WEBSOCKET-API-TESTS-ASYNCIO-MARKER-AND-HEARTBEAT-DRAIN
phase: done
date: 2026-08-17
tags: [observability, bug, testing]
---

# TCK-20260817-HOTFIX-WEBSOCKET-API-TESTS-ASYNCIO-MARKER-AND-HEARTBEAT-DRAIN

## Title
Fix 2 real WebSocket API test bugs found during full "API / tools / logging" CI-job
re-verification, not caught by the original per-failure investigation batch

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
While re-running the real CI job's exact invocation (`pytest tests/api tests/cli tests/tools
tests/logging tests/engine tests/observability -m "not slow"`) to verify the rest of this
session's fixes, 2 additional real failures surfaced that the original `gh api` log fetch (limited
to a `tail -150` window) had cut off and none of the 8 dispatched investigation agents were briefed
on:

1. `tests/api/test_ws_protocol.py::test_ws_json_handshake` and `::test_ws_msgpack_handshake` —
   `Failed: async def functions are not natively supported. You need to install a suitable
   plugin...`. Root cause: both tests use `@pytest.mark.asyncio`, but this repo's actual async
   test convention (confirmed via every other passing async test, e.g.
   `tests/observability/test_metrics_export.py::test_metrics_endpoint_direct`) is
   `@pytest.mark.anyio` — `pytest-asyncio` is not installed/configured at all, only `anyio`'s
   pytest plugin is. A stale decorator, not a missing dependency.
2. `tests/api/test_observability_websocket.py::test_observability_websocket_suite` —
   `AssertionError: Did not receive keep-alive heartbeat message`. Root cause: the test reads a
   fixed count of 5 messages waiting for a heartbeat (sent every 5s by the real server), but the
   default server continuously ticks a real simulation broadcasting real domain events (combat/
   economy/etc.) much faster than the heartbeat interval — confirmed via direct reproduction
   (received 3 real events in ~0.3s). A small fixed read count can exhaust itself entirely on real
   events still ahead of the heartbeat in the FIFO queue, independent of event volume.

## Scope
- `tests/api/test_ws_protocol.py`: `@pytest.mark.asyncio` → `@pytest.mark.anyio` (both tests).
- `tests/api/test_observability_websocket.py`: replace the fixed-count (5) heartbeat-wait loop
  with an overall wall-clock deadline (20s) drain loop, guaranteeing several heartbeat intervals
  elapse regardless of real event volume.

## Out of Scope
- The server's heartbeat architecture itself (5s interval, `src/api/ws/stream.py`) — confirmed
  correctly implemented; only the test's read strategy was wrong.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] `test_ws_json_handshake`/`test_ws_msgpack_handshake` pass.
- [x] `test_observability_websocket_suite` passes.
- [x] Full real CI job invocation shows no failures attributable to either bug.

## Related Tickets
None — found independently during full-scope re-verification of this session's other fixes.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/api/test_ws_protocol.py`
- `tests/api/test_observability_websocket.py`

## Implementation Notes
Changed both `@pytest.mark.asyncio` decorators to `@pytest.mark.anyio`, matching the repo's real,
only-configured async test convention. Replaced the heartbeat test's `for _ in range(5): ...`
fixed-count read with a `while asyncio.get_event_loop().time() < deadline: ...` wall-clock-bounded
drain (20s), so the loop keeps consuming real events until either a heartbeat is found or the
deadline (several heartbeat intervals) genuinely elapses.

## Test Summary
- `pytest tests/api/test_ws_protocol.py -q`: 2 passed.
- `pytest tests/api/test_observability_websocket.py -q`: 1 passed.
- Full real CI job invocation (`tests/api tests/cli tests/tools tests/logging tests/engine
  tests/observability -m "not slow"`): both bugs confirmed no longer present.

## Files Changed
- `tests/api/test_ws_protocol.py`
- `tests/api/test_observability_websocket.py`

## Completion Summary
Fixed 2 real bugs that fell outside the original 8-agent investigation batch's scope (a raw CI log
`tail` window cut them off before they were seen). One was a stale async-test decorator convention
mismatch; the other was a fixed-count message-read strategy that couldn't keep up with real
simulation event volume. Both confirmed via direct reproduction before fixing, not assumed.
