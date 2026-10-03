---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
artifact_type: test_plan
tags: [observability, engine]
---

# Test Plan — TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

## Regression Surface

Unit:
- `tests/unit/observability/test_alert_router.py` — must keep passing unmodified, including
  `test_factory_watchdog_trip` (line 80-87). This ticket adds a **new** call site for
  `AlertEvent.create_watchdog_trip` from `src/observability/watchdog.py`; it must not change the
  factory's existing signature or the two existing `kernel.py` call sites (lines 441, 600).
- `tests/unit/core/test_watchdog.py` — unrelated `CertificationHarness`/`ArenaStopCondition.WATCHDOG`
  mechanism (arena hang-detection). Must keep passing untouched; confirms this ticket did not
  accidentally touch that subsystem.

Integration / API (subprocess-launched real server, existing pattern to follow):
- `tests/api/test_rest_parity.py::test_api_rest_parity` — asserts `GET /health` returns HTTP 200
  with `data["status"] == "ok"` and `data["version"] == "v2"` for a freshly-started (~3s uptime)
  engine. Must keep passing — the new implementation must report healthy for a normally-starting,
  ticking engine, not just for the old always-`ok` stub.
- `tests/api/test_live_health_api.py::test_live_health_api_suite` — exercises the *separate*
  `/api/v1/observability/live/health` endpoint (`LiveAnomalyCounter`-backed) and the observability
  UI. Unrelated route, must not regress; confirms this ticket's `/health` change is scoped to the
  one route and doesn't collide with the already-existing `/api/v1/observability/live/health`.
- `tests/api/test_scenario_runtime_api.py` — broader API surface test; run to confirm no import-time
  or startup regression from touching `server.py`.

## New Tests Required

Per Acceptance Criteria:

1. **`/health` degrades when the engine thread is killed.**
   - Category: integration (subprocess-launched real server, matching
     `test_rest_parity.py`'s/`test_live_health_api.py`'s existing pattern).
   - Verifies: with the server running normally, `GET /health` returns `status: ok` (HTTP 200);
     after forcibly stopping/crashing the `V2EngineManager`'s background thread (e.g. via the
     existing `/api/v1/control/*` surface if sufficient, or a test-only injection point exposed by
     the new `_thread.is_alive()`-based check), `GET /health` returns a materially different status
     (`degraded`/`unhealthy`) — not still `ok` — and ideally a non-200 status code so external
     orchestration (load balancers, container health probes) can act on it without parsing the body.
   - Where: `tests/api/test_health_liveness.py` (new file) — keep the AC-mandated "thread
     killed/hung" scenario isolated from `test_rest_parity.py`'s general-shape assertions so a
     future contributor doesn't have to modify the parity test to add liveness scenarios.

2. **`/health` degrades on last-tick staleness (hang, not crash).**
   - Category: integration or unit (unit if `V2EngineManager`'s new staleness accessor can be
     exercised directly without a real subprocess server — preferred, faster, more deterministic).
   - Verifies: a thread that is still `.is_alive()` but hasn't produced a new tick within the
     staleness threshold decided in Plan is reported as degraded/unhealthy, not `ok` — this is the
     AC's "hung" half, distinct from "killed."
   - Where: `tests/unit/api/test_engine_manager.py` (new file, no such file exists today per
     `tests/unit/api/` listing: `test_economy_route.py`, `test_read_model_cache.py`,
     `test_read_model_service.py`) if a unit-level accessor is added; otherwise
     `tests/api/test_health_liveness.py` alongside test 1.

3. **`/health` does not report unhealthy while intentionally paused.**
   - Category: unit or integration.
   - Verifies: the pause-vs-crash disambiguation risk flagged in `investigation.md` — calling
     `POST /api/v1/control/pause` must not, by itself, flip `/health` to degraded/unhealthy, since
     the thread stays alive and paused-with-recent-last-tick is a normal operator state, not a
     failure. This is the regression guard for the specific trap identified during investigation
     (naively wiring to the existing `is_running` property would fail this test).
   - Where: `tests/api/test_health_liveness.py`.

4. **`SimulationWatchdog`'s critical escalation reaches `AlertsManager`'s router.**
   - Category: unit, with `AlertsManager`/`AlertRouter` mocked or using a test sink (matching
     `test_alert_router.py`'s existing patterns for constructing an `AlertRouter` with injected
     sinks).
   - Verifies: once `self.consecutive_failures >= self.max_failures` trips in
     `SimulationWatchdog.run_cycle()` (the existing `watchdog.py:106-108` condition), a
     `create_watchdog_trip`-shaped `AlertEvent` is actually routed (not just logged) — i.e. a sink's
     `send()` gets called, proving the wiring exists end-to-end at the code level, independent of
     whether a real webhook URL is configured in the environment.
   - Where: `tests/unit/observability/test_watchdog.py` (new file — no unit test file exists for
     `SimulationWatchdog` today; only integration-shaped, requests-based E2E coverage would catch
     this indirectly and shouldn't be the only coverage for an alert-wiring regression).

5. **Doc/reality parity check (lightweight, not a full architecture guard).**
   - Category: doc-content assertion, or manual verification noted in `Completion Summary` — pick
     one deliberately in Plan rather than skipping silently, since D24's audit specifically flagged
     doc-path-drift as caught late in this exact area.
   - Verifies: `docs/architecture/simulation_watchdog.md` no longer states `Status: Proposed` and no
     longer cites `src/utils/watchdog.py`.
   - Where: if automated, extend or reuse whatever mechanism Epic C's planned doc-path-existence
     checker eventually provides (`docs/plans/architecture_resilience_remediation_roadmap.md` Epic
     C) — do not build a bespoke one-off checker for this single doc as part of this ticket; a
     manual read-and-confirm step recorded in the ticket's Completion Summary is acceptable given
     Epic C is where the general-purpose tooling for this belongs.

## Scoped Pytest Commands

```bash
# New/changed API-level health behavior + existing REST/health parity
pytest tests/api/test_health_liveness.py tests/api/test_rest_parity.py tests/api/test_live_health_api.py tests/api/test_scenario_runtime_api.py -v

# Engine manager unit coverage (thread-liveness / staleness accessors, if added at unit level)
pytest tests/unit/api/ -v

# Watchdog alert-wiring unit coverage + existing alert-router regression surface
pytest tests/unit/observability/test_watchdog.py tests/unit/observability/test_alert_router.py -v

# Unrelated-subsystem-named-watchdog regression guard (arena/certification harness)
pytest tests/unit/core/test_watchdog.py -v
```

Do not run `pytest tests/` — scope stays within `tests/api/`, `tests/unit/api/`, and
`tests/unit/observability/` per this ticket's actual touched surface.

## Anti-Drift Test Guards

- Test 3 (pause-vs-crash) is the guard against the most likely silent-regression path identified in
  investigation: implementing `/health` against the existing `is_running` property instead of a new
  `_thread.is_alive()` accessor would pass tests 1 and 2 but silently fail test 3 (report
  unhealthy during a normal pause) — this test exists specifically to catch that shortcut.
- Test 4 asserts the wiring reaches the router/sink layer, not just that `logger.critical` still
  fires — a change that only adds a differently-worded log line without actually calling
  `AlertsManager.get_router().route(...)` would satisfy a naive "still logs critical" check but
  fail this test, which is the point.
- Keep `create_watchdog_trip`'s two existing `kernel.py` call sites (lines 441, 600) and their test
  coverage in `test_alert_router.py`/`kernel.py`'s own integration tests untouched — any diff that
  modifies those call sites' `run_id`/`tick`/`message`/`details` shapes as a side effect of adding
  the new `watchdog.py` call site is out of scope and should be reverted, not merged.
- `tests/unit/core/test_watchdog.py` passing unmodified is itself an anti-drift guard: if an
  implementer mistakenly "fixes" that file thinking it's related to `SimulationWatchdog`, this
  regression-surface entry existing in the test plan makes that scope-creep visible in review.
