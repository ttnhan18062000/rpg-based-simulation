---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON
artifact_type: investigation
tags: [testing, observability]
---

# Investigation — TCK-20260926-LIVE-HEALTH-COUNTER-SHARED-SINGLETON

## Two independent paths into `LiveAnomalyCounter`, confirmed by reading the code

1. **The test's own path** — `POST /api/v1/test/publish_event`
   (`src/api/server.py::publish_test_event`) calls
   `LiveEventPublisher.get_instance().publish(event)` **directly** — it does not go through
   `EventRecorder` or the stream-adapter factory at all.
2. **The live engine's path** — `V2EngineManager.start()` (called from the FastAPI `lifespan` hook,
   `src/api/server.py`) spawns a background thread (`_run_loop` → `kernel.tick_once()`) from server
   boot. The kernel's own observability recording goes through `EventRecorder.record()`
   (`src/observability/event_recorder.py`), which calls `_publish_envelope_to_stream()` →
   `get_event_stream_adapter().publish(event)` (`src/observability/stream/factory.py`). Under the
   default `local-dev` profile (`ObservabilityConfig.get_stream_backend()` → `"in_process"`, no env
   override), that factory returns `InProcessEventStreamAdapter`, whose `publish()` forwards
   straight into the same `LiveEventPublisher.get_instance().publish(event)` the test's own path
   calls.

Both paths converge on the same process-wide singleton (`LiveAnomalyCounter.get_instance()`,
confirmed single-process: `uvicorn.run(app, host=..., port=...)` in `src/cli/entry.py` passes no
`workers=`).

## The isolation lever: `get_event_stream_adapter()`'s backend selection

`ObservabilityConfig.get_stream_backend()` reads `SIM_STREAM_BACKEND`/`RPG_STREAM_BACKEND` from the
environment before falling back to the deployment-profile default. Setting either env var to
`"null"` in the test's own `subprocess.Popen(..., env=env)` call selects `NullEventStreamAdapter`
(`src/observability/stream/adapters.py`), which drops every event it receives with zero downstream
effect (`self.dropped_count += 1`, nothing else).

**Critically, this only affects path 2 (the live engine's telemetry).** Path 1 (the test's own
manual injection) calls `LiveEventPublisher.get_instance().publish(event)` directly and never
touches `get_event_stream_adapter()` at all, so it is completely unaffected by this env var. This is
exactly the isolation the ticket's Open Question asks for: sever the live engine's telemetry from
the counter the test asserts on, without touching the test's own injection path or the counter's
production reset-on-run_id-change semantics (both explicitly Out of Scope).

The background engine keeps ticking either way — this doesn't stop it or change `is_running`/
`health_state`'s other server-liveness assertions (L40, L128–133 of the test), only whether its
*telemetry* reaches the anomaly counter. AC1's "demonstrated... with the background engine actively
ticking" is satisfied by construction: the engine is never paused or disabled, only its event
stream is redirected to a no-op sink.

## `tests/api/test_live_observability_status.py` — checked, not assumed clear

Read in full. Its assertions are membership/enum checks (`status in ("RUNNING", "PAUSED")`,
`health_state in (...)`) and state-transition checks (pause → `PAUSED`, resume → `RUNNING`) — no
exact-value counter assertion anywhere, and no anomaly-counter interaction at all. It does not share
this exposure; no change needed there.

## `docs/testing/regression_policy.md`'s row — what's actually wrong with it

Current text: "Require a running server; environment-dependent; failures indicate deployment
issues, not code regressions — **except** a 401/403 response, which means..." The row's *only*
carve-out names a status-code-shaped failure (auth misconfiguration). A counter-value assertion
failing after every status-code check in the same test already passed is a third failure shape the
row doesn't name at all — readers are left inferring it must be the generic "server not running"
case by elimination, which is exactly the misdiagnosis this ticket exists to stop happening a third
time.
