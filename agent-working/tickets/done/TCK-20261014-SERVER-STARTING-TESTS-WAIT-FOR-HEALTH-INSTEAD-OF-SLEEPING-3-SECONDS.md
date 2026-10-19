---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-SERVER-STARTING-TESTS-WAIT-FOR-HEALTH-INSTEAD-OF-SLEEPING-3-SECONDS
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-SERVER-STARTING-TESTS-WAIT-FOR-HEALTH-INSTEAD-OF-SLEEPING-3-SECONDS

## Title
Tests that start the API server wait for /health instead of sleeping a fixed 3 seconds.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
tests/api/test_ws_protocol.py and tests/observability/test_metrics_export.py start python -m src serve and slept 3 seconds. The server takes about 5.5 s to come up while it compiles an authored world, so they failed with ConnectionRefused on clean main as well as on the D69 branch.

## Scope
One shared helper (tests/helpers/live_server.py) that polls /health (default 30 s) and fails with the server's output if it exits or never comes up; the two test files use it. No other behaviour change.

## Out of Scope
Other tests that start a server (test_rest_parity, test_live_entity_inspection, test_live_observability_status, test_live_health_api, test_observability_websocket, test_websocket_stream_events); they were not failing and can adopt the helper later.

## Acceptance Criteria
Both files pass three runs in a row.

## Related Tickets
TCK-20261014-THE-LIVE-SERVER-RUNS-THE-AUTHORED-WORLD-NOT-A-DEMO-SPAWN-D69.

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
tests/helpers/live_server.py; tests/api/test_ws_protocol.py; tests/observability/test_metrics_export.py.

## Assumptions / Open Questions
None.

## Implementation Notes
start_server(port, extra_args, env, timeout) returns (process, log); stop_server terminates and closes. The server output goes to a temp file shown on failure.

## Test Summary
Both files: 10 passed on each of three consecutive runs (about 23 s each).

## Files Changed
tests/helpers/live_server.py; the two test files.

## Completion Summary
Done.
