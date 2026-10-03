---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON
artifact_type: plan
tags: [testing, observability]
---

# Plan — TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON

## 1. Isolation mechanism (Open Question — decided)

Set `env["SIM_STREAM_BACKEND"] = "null"` in
`tests/api/test_live_health_api.py::test_live_health_api_suite`'s subprocess env. This is the
narrowest of the three candidates the ticket named:
- **Chosen**: redirect the live engine's own telemetry to a no-op sink. Zero blast radius on what
  the test is testing (the health/anomaly-counter API contract) — the engine still runs, still
  ticks, still reports `RUNNING`; only its *event stream* is now inert.
- **Rejected: dedicated counter instance for the test.** Would require either a new
  dependency-injection seam in `get_live_health()` (production code change, larger blast radius) or
  monkeypatching the singleton from outside the subprocess (impossible — the server runs in a
  separate process, not importable from the test).
- **Rejected: not starting the background engine for this test.** Changes what the test verifies —
  `get_live_health()`'s `manager` branch (`status_str` derived from `is_running`/`is_paused`) would
  never exercise the "engine running" path, silently narrowing existing coverage.

## 2. Test change

- Add `env["SIM_STREAM_BACKEND"] = "null"` alongside the existing `SIM_OBS_MODE`/
  `RPG_API_KEY_HASHES` env assignments.
- Add a one-line comment at that assignment explaining why (points at this ticket ID and the
  run_id-reset hazard, satisfying AC4 "documented at the point of use" for the test side).
- No assertion changes — AC2 requires the exact-value asserts stay exact.

## 3. Production-code documentation (AC4, the other "point of use")

Add a short comment to `LiveAnomalyCounter.push()` in `src/observability/live/anomaly_counter.py`
documenting the reset-on-run_id-change behavior and that it is shared with any live engine's own
telemetry — so a future reader of the counter (not just the test) meets the hazard where it lives,
not only in a test comment. No behavior change here — Out of Scope explicitly forbids touching the
reset semantics themselves.

## 4. `docs/testing/regression_policy.md` correction

Rewrite the "Live observability tests" row's reason clause to name three failure shapes instead of
one carve-out against an implicit default:
1. Server genuinely not up / connection refused — the row's original case.
2. 401/403 — the existing `RPG_API_KEY_HASHES` test-config carve-out, unchanged.
3. **New**: a counter/state-value assertion failing after every preceding status-code assertion in
   the same test already passed — not automatically case 1; investigate the actual assertion before
   filing it under this row.

## 5. Verification

- Run `tests/api/test_live_health_api.py` and `tests/api/test_live_observability_status.py` locally
  (both require a real server subprocess — expect the ~4s startup sleep per run).
- Confirm AC1 by demonstrating the isolation holds with the engine actively ticking: this is
  structural (the env var change), not something a single passing run can independently prove
  beyond what the code path itself guarantees — record the reasoning, not a flake-hunting loop,
  matching the ticket's own "demonstrated rather than asserted" wording via the mechanism's
  construction (path 1 never touches the adapter at all) rather than via repeated runs hoping to
  catch a race that direct code reading already rules out.
