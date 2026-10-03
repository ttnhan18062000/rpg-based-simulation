---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON
artifact_type: test_plan
tags: [testing, observability]
---

# Test Plan — TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON

1. `tests/api/test_live_health_api.py::test_live_health_api_suite` — existing test, unmodified in
   assertions, gains the `SIM_STREAM_BACKEND=null` env var. Run directly (spawns a real server
   subprocess): confirms the exact-value counter asserts still pass with a live, ticking engine in
   the same process.
2. `tests/api/test_live_observability_status.py` — run unmodified, confirming no regression (this
   ticket does not touch this file, per investigation.md's finding that it doesn't share the
   exposure).
3. No new unit test is added for the isolation itself: the mechanism is a config/env change verified
   by code-path reading (path 1 never calls `get_event_stream_adapter()`), not a new race to
   reproduce and re-fix. Adding a flake-hunting repeat-loop test would assert against a race that
   direct reading already rules out as reachable through this path once redirected.
4. `docs/testing/regression_policy.md`'s row change is documentation-only; verified by re-reading it
   against the three failure shapes it now names, not by a test.
