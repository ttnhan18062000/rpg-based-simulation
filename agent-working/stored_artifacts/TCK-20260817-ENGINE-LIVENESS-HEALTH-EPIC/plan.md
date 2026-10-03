---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
artifact_type: plan
tags: [observability, engine]
---

# Implementation Plan — TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

## Summary

Replace `/health`'s hardcoded `{"status": "ok"}` stub with a real liveness computation sourced
from two new `V2EngineManager` accessors — `_thread.is_alive()` (crash signal) and last-tick
recency over the already-populated `_tick_times` deque (hang signal) — combined in a new
`get_health_status()` method that evaluates staleness independently of `is_paused` so a normal
operator pause never reports unhealthy. The route returns HTTP 503 only when the thread is
actually dead; `ok`/`degraded` both stay HTTP 200. Separately, `SimulationWatchdog`'s existing
log-only critical escalation gets a third call site into the already-built
`AlertsManager`/`AlertRouter`/`WebhookAlertSink` stack (reused as-is, no new sink code), using a
`run_id` read from `/health`'s own new `engine.run_id` field (backed by `Kernel.run_id`, which
already exists) rather than an invented placeholder. `docker-compose.yml`'s `watchdog` service
gains operator-configurable (default-disabled) webhook env vars. Docs
(`simulation_watchdog.md`, `api_protocol_contract.md`) and a new `INFRA-358` parity ledger entry
are updated to match the real, honest end state — including the honest caveat that out of the
box, with no `SIM_ALERTS_WEBHOOK_URL` set, the escalation is still effectively log-only; only the
*capability* to reach a real external channel is what this ticket adds.

## Steps

### Step 1 — Add raw engine-liveness accessors to `V2EngineManager`
**Files:** `src/api/engine_manager.py`

**Change:** Add two new read-only properties to `V2EngineManager` (place near the existing
property block at lines 303-334):
- `is_thread_alive` — `return self._thread is not None and self._thread.is_alive()`. Today
  `self._thread` (assigned at `engine_manager.py:243` in `start()`) has no public accessor at all
  — confirmed by reading the full property list at lines 303-334 (`tick`, `is_running`,
  `is_paused`, `is_stopped`, `is_stopping`, `kernel`, `started_at`, `errors_total`); none call
  `.is_alive()`.
- `last_tick_age_seconds` — reads under the existing `self._state_lock` (the same lock
  `_run_loop` already holds when appending to `_tick_times`, `engine_manager.py:287-288`):
  `time.time() - self._tick_times[-1]` if `self._tick_times` is non-empty, else
  `time.time() - self._started_at` if `self._started_at` is set (covers the startup window before
  the first tick completes), else `None`. `self._tick_times = deque(maxlen=100)` is confirmed
  populated only at `engine_manager.py:288` inside `_run_loop`.

**Other writers to `_tick_times`/`_started_at` (must not collide):** `_tick_times` has exactly one
writer in the whole codebase — `_run_loop` (`engine_manager.py:288`), always under
`_state_lock`. `_started_at` has exactly one writer — `start()` (`engine_manager.py:239`), set
once before the thread is spawned, never mutated afterward. This step only reads both under the
same lock discipline already in place; it adds no new writer and cannot race with the existing
one because reads happen under the same `_state_lock`.

**Do NOT touch:** `is_running` (`engine_manager.py:308-310`), `is_paused`
(`engine_manager.py:312-314`), `get_tps()` (`engine_manager.py:64-71`), or `_run_loop` itself
(`engine_manager.py:273-301`). These stay exactly as they are — the new accessors are additive.

**Verify:** `tests/unit/api/test_engine_manager.py::test_is_thread_alive_reflects_real_thread_state`,
`::test_last_tick_age_seconds_uses_tick_times_then_started_at_fallback` (new tests, Step 4).

---

### Step 2 — Add `get_health_status()` to `V2EngineManager`
**Files:** `src/api/engine_manager.py`

**Change:** Add a new method `get_health_status(self) -> Dict[str, Any]` on `V2EngineManager`,
alongside `get_metrics_snapshot()` (`engine_manager.py:73-76`) — same "manager owns its own
health/metrics computation" pattern, not a free function elsewhere. Logic:

```python
def get_health_status(self) -> Dict[str, Any]:
    now = time.time()
    thread_alive = self.is_thread_alive
    with self._state_lock:
        if self._tick_times:
            last_tick_age = now - self._tick_times[-1]
        elif self._started_at is not None:
            last_tick_age = now - self._started_at
        else:
            last_tick_age = None
        errors_total = self._errors_total
    paused = self.is_paused
    run_id = self._kernel.run_id if self._kernel is not None else None
    staleness_threshold = max(3.0, self._tick_rate * 60)

    if not thread_alive:
        status = "unhealthy"
    elif not paused and last_tick_age is not None and last_tick_age > staleness_threshold:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "version": "v2",
        "timestamp": now,
        "engine": {
            "thread_alive": thread_alive,
            "paused": paused,
            "last_tick_age_seconds": last_tick_age,
            "staleness_threshold_seconds": staleness_threshold,
            "errors_total": errors_total,
            "run_id": run_id,
        },
    }
```

**Design decisions made here (resolving investigation's open questions):**
- **Staleness threshold = `max(3.0, self._tick_rate * 60)`.** `self._tick_rate = 0.05` (20 TPS
  default) is a hardcoded instance constant set once in `__init__`
  (`engine_manager.py:34`, `# 20 TPS default`) — confirmed not derived from `RuntimeProfile`
  (`src/config/profiles.py` has no `tick_rate` field; grep confirmed) and never reassigned
  anywhere else in the file, so it is safe to key the threshold off it. At the real default,
  `0.05 * 60 = 3.0`, so the floor and the formula agree exactly: **3.0 seconds**, i.e. ~60 missed
  ticks of headroom — generous enough to absorb GC pauses/thread-scheduling jitter without a false
  "degraded," but far tighter than `SimulationWatchdog`'s external ~30s trip time
  (`max_failures=3` × `POLL_INTERVAL=10s`, `watchdog.py:14,22`), so `/health` gives a fast,
  fine-grained in-process signal that complements (not duplicates) the external watchdog's coarser
  poll-based backstop. The `self._tick_rate * 60` form (not a bare literal `3.0`) keeps the
  threshold self-adjusting if `_tick_rate` is ever made configurable later.
- **`run_id` sourced from the real `Kernel.run_id` property**, not an invented placeholder.
  Confirmed `Kernel` (`src/engine/kernel.py:1214-1215`) exposes `run_id` as a public property
  backed by `self._run_id`, which is always populated — either passed in or auto-generated as
  `f"run_{int(time.time())}_{suffix}"` (`kernel.py:120-123`) — never `None` once a `Kernel`
  exists. `V2EngineManager` already exposes `.kernel` (`engine_manager.py:324-326`). This directly
  answers investigation's open question: yes, `V2EngineManager` exposes a real run_id via its
  kernel, so `/health`'s new `engine.run_id` field carries it end-to-end (used by Step 5's
  watchdog wiring instead of an invented sentinel).

**Other writers to `_errors_total`/`_kernel`/`is_paused`'s underlying `Event`s:** `_errors_total`
has one writer, `_run_loop`'s except block (`engine_manager.py:293-294`). `self._kernel` is
assigned once in `_build()` (`engine_manager.py:145`, called from `__init__` and `reset()`); no
concurrent writer exists while a request thread reads `self._kernel.run_id`. `_paused`/`_running`
are `threading.Event`s already read without extra locking by the existing `is_paused`/`is_running`
properties (`engine_manager.py:308-314`) — this step follows that same established, safe pattern,
adds no new lock.

**Do NOT touch:** `get_metrics_snapshot()` or `_latest_metrics_snapshot` (a separate,
already-correct read path for `/metrics`, not `/health`) — do not merge or share state between
the two.

**Verify:** `tests/unit/api/test_engine_manager.py::test_get_health_status_*` (killed / hung /
paused scenarios — Step 4).

**Dependency:** Requires Step 1's accessors.

---

### Step 3 — Wire `/health` route to `get_health_status()`
**Files:** `src/api/server.py`

**Change:**
1. Add `JSONResponse` to the existing `fastapi.responses` import at line 10
   (`from fastapi.responses import HTMLResponse, RedirectResponse` →
   `from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse`).
2. Replace the stub at `server.py:126-128`:
   ```python
   @app.get("/health", response_model=Dict[str, Any])
   async def health_check(manager: V2EngineManager = Depends(get_engine_manager)):
       payload = manager.get_health_status()
       status_code = 503 if payload["status"] == "unhealthy" else 200
       return JSONResponse(content=payload, status_code=status_code)
   ```
   This adds `Depends(get_engine_manager)` — confirmed `/health` is currently the *only* route
   handler without it (investigation, re-confirmed by reading `server.py:116-128`: `/metrics`
   already uses the identical `Depends(get_engine_manager)` pattern one function above). This is
   safe: `create_v2_app`'s `lifespan` (`server.py:26-29`) always calls
   `set_engine_manager(manager)` and `manager.start()` before `yield`, so by the time any request
   is served, `get_engine_manager()` (`src/api/dependencies.py:17-20`) never raises.
3. HTTP status mapping: `ok`/`degraded` → 200 (unchanged from today for the healthy case —
   required by `tests/api/test_rest_parity.py:19`); `unhealthy` → 503, satisfying the ticket AC's
   "ideally a non-200 status code" for the killed-thread case.

**Other writers to `/health`'s route registration:** none — `server.py` defines this route exactly
once; no other module re-registers or monkey-patches it.

**Do NOT touch:** `/metrics` (`server.py:116-124`), `/api/v1/observability/live/status`
(`server.py:130-138`) or `/api/v1/observability/live/health` (a different, already-existing route
backed by `LiveAnomalyCounter`, not `V2EngineManager` — per `test_plan.md`'s regression surface,
must keep passing unmodified and unrelated).

**Verify:** `tests/api/test_health_liveness.py::test_health_route_wiring_returns_ok_for_healthy_engine`
(new, Step 4); `tests/api/test_rest_parity.py::test_api_rest_parity` (existing, must keep passing
unmodified).

**Dependency:** Requires Step 2.

---

### Step 4 — New tests for engine-liveness health computation and route wiring
**Files:** `tests/unit/api/test_engine_manager.py` (new file — confirmed no such file exists today;
`tests/unit/api/` currently holds only `test_economy_route.py`, `test_read_model_cache.py`,
`test_read_model_service.py`), `tests/api/test_health_liveness.py` (new file)

**Change:**

In `tests/unit/api/test_engine_manager.py`, construct `V2EngineManager` directly (existing
precedent: `tests/observability/test_metrics_export.py:27` and `tests/api/test_paged_logic.py:16`
both do `V2EngineManager(profile, ...)` directly and read private attributes like
`manager._latest_metrics_snapshot` — reaching into `_thread`/`_tick_times` directly in tests
follows this codebase's established pattern, not a new one). Cover, at the manager level
(deterministic, no HTTP/subprocess needed — matching `test_plan.md`'s own stated preference
"unit... preferred, faster, more deterministic" for this exact scenario):

1. `test_is_thread_alive_reflects_real_thread_state` — before `start()`, `is_thread_alive` is
   `False`; after `start()`, `True`; after `stop()`, `False` again.
2. `test_get_health_status_killed_thread_reports_unhealthy` — two variants:
   - Synthetic/deterministic: after `start()`, replace `manager._thread` with a stub object whose
     `is_alive()` returns `False`, assert `get_health_status()["status"] == "unhealthy"`.
   - Realistic: after `start()`, monkeypatch `manager._kernel.tick_once` to raise, poll (short
     timeout loop, not a fixed `sleep`) until `manager._thread.is_alive()` is `False` (proves the
     real `_run_loop` except-path at `engine_manager.py:291-295` actually kills the thread, not
     just that the property logic is correct), then assert `get_health_status()["status"] ==
     "unhealthy"`.
3. `test_get_health_status_stale_tick_reports_degraded` — after `start()`, wait briefly for at
   least one real tick, then directly append a stale timestamp
   (`manager._tick_times.append(time.time() - 10.0)` under `manager._state_lock`) so
   `last_tick_age_seconds` exceeds the 3.0s threshold while the thread is still alive and not
   paused; assert `status == "degraded"`.
4. `test_get_health_status_paused_stays_ok` — the AC's core regression guard: after `start()`,
   call `manager.pause()`, then force `last_tick_age_seconds` past the threshold the same way as
   test 3; assert `status == "ok"` (not `"degraded"`) because pause is intentional. This is the
   test that would fail if a future change naively swapped `get_health_status()`'s logic to key
   off `is_running` instead of `is_thread_alive` + pause-aware staleness.

In `tests/api/test_health_liveness.py`, one integration-level test using
`fastapi.testclient.TestClient` over `create_v2_app(profile)` (in-process ASGI, not a subprocess —
lighter-weight than `test_rest_parity.py`'s subprocess pattern, sufficient to prove the route
itself calls `get_health_status()` and maps the status code correctly):
`test_health_route_wiring_returns_ok_for_healthy_engine` — `GET /health` on a freshly-started app
returns HTTP 200 and `status == "ok"`.

**Other writers to these new test files:** none — new files, no collision risk.

**Do NOT touch:** `tests/api/test_rest_parity.py` (must keep passing unmodified per
`test_plan.md`'s Regression Surface), `tests/api/test_live_health_api.py`, `tests/unit/core/test_watchdog.py`.

**Verify:** `pytest tests/unit/api/test_engine_manager.py tests/api/test_health_liveness.py tests/api/test_rest_parity.py -v`

**Dependency:** Requires Steps 1-3.

---

### Step 5 — Wire `SimulationWatchdog`'s critical escalation to `AlertsManager`
**Files:** `src/observability/watchdog.py`

**Change:**
1. In `SimulationWatchdog.__init__` (`watchdog.py:19-23`), add `self.run_id =
   "external-watchdog-unknown"` — the pre-first-successful-poll sentinel, overwritten by (2) the
   moment a real run_id is observed.
2. Modify `check_health()` (`watchdog.py:25-34`): on a 200 response, parse the JSON body (already
   fetched via `requests.get`, currently discarded — confirmed `check_health` today only checks
   `resp.status_code`, never reads `resp.json()` or `resp.text`) and, if
   `body.get("engine", {}).get("run_id")` is present, set `self.run_id` to it. Wrap the parse in
   its own `try/except` so a malformed/older-shape response body degrades to "keep the last known
   run_id," not a hard failure of the health check itself:
   ```python
   if resp.status_code == 200:
       try:
           body = resp.json()
           candidate = body.get("engine", {}).get("run_id")
           if candidate:
               self.run_id = candidate
       except Exception:
           pass
       return True
   ```
   This is the concrete resolution of investigation's open question: the external watchdog process
   has no `run_id` concept of its own, so it reads the real one from `/health`'s new `engine.run_id`
   field (Step 2), which is populated from the same `Kernel.run_id` the in-kernel watchdog already
   uses at `kernel.py:442,601`.
3. In `run_cycle()`'s existing trip block (`watchdog.py:106-108`), add a call to
   `AlertsManager.get_router().route(...)` immediately after the existing `logger.critical(...)`
   call — do not remove or alter the existing log line:
   ```python
   if self.consecutive_failures >= self.max_failures:
       logger.critical("SYSTEM_CRITICAL: Persistent failure! Reason: %s",
                      status_report, extra={'component': 'watchdog', 'diagnostics': status_report})
       try:
           from src.observability.alerts.manager import AlertsManager
           from src.observability.alerts.models import AlertEvent
           router = AlertsManager.get_router()
           tick_value = int(self.last_tick) if self.last_tick and self.last_tick > 0 else 0
           event = AlertEvent.create_watchdog_trip(
               run_id=self.run_id,
               tick=tick_value,
               message=f"External SimulationWatchdog detected persistent failure: {status_report}",
               details=status_report,
           )
           router.route(event)
       except Exception:
           logger.exception("Failed to dispatch WatchdogTrip alert")
   ```
   The `try/except` wrapper mirrors the existing pattern at the two `kernel.py` call sites
   (`kernel.py:437-451`, `596-609`, both wrap their `AlertsManager` call in `try/except`) so a
   dispatch failure never breaks the watchdog's own polling loop.

**Other writers to the resources this step touches:**
- `AlertEvent.create_watchdog_trip` (`src/observability/alerts/models.py:62-73`): already called
  from two sites in `kernel.py` (lines 441-451 tick-budget path, 600-609 mid-tick throttle path) —
  **do not modify those call sites or the factory's signature.** This step adds a *third*,
  independent call site. `kernel.py` runs inside the `backend` container's process;
  `watchdog.py` runs inside the separate `watchdog` container's process (confirmed
  `docker-compose.yml:120-134`) — the two never share Python process state, so there is no
  cross-process race on the factory call itself.
- `AlertsManager._router` (`manager.py:13`, class-level singleton): lazily built by `get_router()`
  under `cls._lock` (`manager.py:14,19`) — already thread/call-safe for concurrent callers within
  one process. This step is a new caller within the `watchdog` container's own process only; it
  never shares the singleton with the `backend` container's `kernel.py` callers (separate
  processes, separate class-level state). No new locking is needed; this step reuses the existing
  thread-safe singleton exactly as `kernel.py` already does.
- `AlertDeduplicator`'s 60s suppression window (`manager.py:26`, default) keys on
  `dedup_key=f"watchdog:{run_id}"` (`models.py:72`). Confirmed: with `POLL_INTERVAL=10s` and
  `max_failures=3` (`watchdog.py:14,22`), `consecutive_failures >= max_failures` stays `True`
  every ~10s cycle until recovery — so with a stable `run_id`, only the first trip in any 60s
  window reaches a sink; subsequent trips in the same window are deduplicator-suppressed. This is
  intentional storm-prevention (documented here, not an accidental side effect) and requires no
  code change — it is the existing `AlertDeduplicator` behavior, reused as-is.
- **Honest limit, stated explicitly:** `WebhookAlertSink.send()` (`sinks.py:53-55`) returns
  `False` immediately — no HTTP call attempted — when `enabled=False` or `webhook_url` is empty.
  `AlertsManager.get_router()` always registers a `WebhookAlertSink` (`manager.py:56-63`)
  regardless of env vars, but it defaults to `enabled=False` (`manager.py:31-34`) unless
  `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` are set. `LogAlertSink.send()`
  (`sinks.py:22-37`) always logs and returns `True`. **Net effect: this step makes a real,
  tested, functional code path to an external channel exist and be reachable — but out of the
  box, with no env vars set, `router.route(event)` still only reaches `LogAlertSink` in practice,
  which is not materially different from today's direct `logger.critical()` call.** Step 6 is what
  makes the webhook path operationally real. Step 7's doc fix states this honestly rather than
  overclaiming.

**Do NOT touch:** `kernel.py:441,600` (the two existing `create_watchdog_trip` call sites) or
their `run_id`/`tick` semantics; `WebhookAlertSink`'s backoff implementation (`sinks.py:87`,
linear not exponential despite the comment — explicitly Epic H scope, not this ticket's).

**Verify:** `tests/unit/observability/test_watchdog.py::test_run_cycle_trip_routes_alert_event`
(new, Step 6 below covers the test file); `tests/unit/observability/test_alert_router.py` must
keep passing unmodified (regression guard that this step didn't touch the factory or router).

**Dependency:** Independent of Steps 1-4 (different subsystem/file). Depends on nothing upstream
in this plan; Step 2's `engine.run_id` field is a soft dependency only in the sense that without
it, `check_health()`'s body-parse in (2) simply never finds a `run_id` key and `self.run_id` stays
at the sentinel — not a hard blocker, but Step 5 should land after Step 2 so the field exists to
parse.

---

### Step 6 — New unit test for watchdog alert-wiring
**Files:** `tests/unit/observability/test_watchdog.py` (new file — confirmed no unit test file
exists for `SimulationWatchdog` today; only indirect E2E coverage would catch a wiring regression)

**Change:** Following `tests/unit/observability/test_alert_router.py`'s existing pattern for
constructing an `AlertRouter` with injected sinks (that file imports `AlertRouter`, `AlertEvent`,
and mocks directly — confirmed by reading its first 100 lines), write:

`test_run_cycle_trip_routes_alert_event` — construct a `SimulationWatchdog()`, monkeypatch
`AlertsManager.get_router` (via `unittest.mock.patch`) to return an `AlertRouter` instance built
with a single injected `unittest.mock.MagicMock(spec=AlertSink)` sink registered via
`register_sink`. Directly set `watchdog.consecutive_failures = watchdog.max_failures` and call
`watchdog.run_cycle()` with `check_health`/`check_metrics`/`check_loki_errors` also monkeypatched
to force the trip condition deterministically (avoid real `requests` calls). Assert the mock
sink's `send()` was called once with an `AlertEvent` whose `alert_type == "WatchdogTrip"` — proving
`route()` actually reached a sink, not just that `logger.critical` still fires (the exact
distinction `test_plan.md`'s Test 4 anti-drift note calls out).

**Other writers:** none — new test file.

**Do NOT touch:** `tests/unit/core/test_watchdog.py` — confirmed unrelated
(`CertificationHarness`/`ArenaStopCondition.WATCHDOG`, an arena-hang-detection mechanism, not
`src/observability/watchdog.py`). Do not open, do not "fix," do not rename anything in it. Include
it in the scoped pytest run only as a passing-unmodified regression guard.

**Verify:** `pytest tests/unit/observability/test_watchdog.py tests/unit/observability/test_alert_router.py tests/unit/core/test_watchdog.py -v`

**Dependency:** Requires Step 5.

---

### Step 7 — Add operator-configurable webhook env vars to the `watchdog` service
**Files:** `docker-compose.yml`

**Change:** In the `watchdog` service's `environment` block (`docker-compose.yml:125-129`,
currently `BACKEND_URL`, `LOKI_URL`, `POLL_INTERVAL`, `LOG_LEVEL` only — confirmed no
`SIM_ALERTS_*`/`RPG_ALERTS_*` vars present), add:
```yaml
      - SIM_ALERTS_WEBHOOK_URL=${SIM_ALERTS_WEBHOOK_URL:-}
      - SIM_ALERTS_WEBHOOK_ENABLED=${SIM_ALERTS_WEBHOOK_ENABLED:-false}
```
using the same `${VAR:-default}` docker-compose substitution syntax already used elsewhere in this
same file (`docker-compose.yml:100`, `"${LOKI_PORT:-3100}:3100"`) — so this is a pattern already
established in the file, not a new convention. **Concrete decision:** default to disabled/empty
(safe-by-default, matches `AlertsManager`'s own default in `manager.py:31-34`) — operators opt in
by setting `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` in their `.env` file or shell
environment before `docker compose up`, without editing this file.

**Other writers to `docker-compose.yml`:** none within this ticket's scope — no other in-flight
ticket touches the `watchdog` service block. This is a single-file, single-writer config change.

**Do NOT touch:** the `watchdog` service's `restart: unless-stopped` (line 134, restarts the
watchdog *container* on its own crash — unrelated to backend engine-thread liveness, do not
conflate), `depends_on` list, or any other service block in this file.

**Verify:** No automated test for docker-compose env var presence exists or is being added (out of
scope — infrastructure config, not code); verified by manual read-and-confirm, recorded in the
ticket's Completion Summary per `test_plan.md`'s Test 5 guidance.

**Dependency:** Logically follows Step 5 (the env vars are meaningless without the code wiring
they configure), though the two touch disjoint files and could technically land in either order.

---

### Step 8 — Fix `docs/architecture/simulation_watchdog.md`
**Files:** `docs/architecture/simulation_watchdog.md`

**Change:**
1. Line 10-11: `## Status` / `Proposed` → `## Status` / `Active` (the described artifact is the
   real, running `docker-compose.yml` `watchdog` service, confirmed lines 120-134 — not a
   proposal).
2. Line 22: `We will implement a standalone **Simulation Watchdog** service
   (`src/utils/watchdog.py`).` → same sentence with the path corrected to
   `src/observability/watchdog.py` (confirmed the real path;
   `find src/utils -iname 'watchdog*'` returns nothing).
3. Line 28 ("Self-Correction/Alerting" responsibility, currently claims "trigger external alerts
   (PagerDuty, Discord, etc.)" unconditionally): rewrite to state the real, honest post-Step-5/6
   behavior: `SimulationWatchdog` emits a `SYSTEM_CRITICAL` log **and** routes a `WatchdogTrip`
   `AlertEvent` through `AlertsManager`'s `AlertRouter` (`src/observability/alerts/`), which
   always logs (`LogAlertSink`) and additionally posts to a webhook
   (`WebhookAlertSink`) **only if** `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` are
   configured on the `watchdog` service (disabled by default). Do not claim PagerDuty/Discord
   integration — none exists; the only real sink type is a generic webhook POST.

**Other writers to this doc:** none — single-file doc fix, no other ticket in flight targets this
file per the investigation's search.

**Do NOT touch:** `docs/engine/contracts/infrastructure_overview.md`'s adjacent "self-healing
watchdog" language (lines 148, 158) — confirmed same-shape overstatement by investigation, but
explicitly **not** named in this ticket's Scope section, and the ticket's own sibling precedent
(`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`) established the pattern of not sweeping in adjacent,
unnamed doc drift. Leave a one-line note in the ticket's Implementation Notes flagging it as a
candidate for a future ticket — do not fix it here.

**Verify:** Manual read-and-confirm (Test 5 in `test_plan.md`) — `Status: Proposed` string and
`src/utils/watchdog.py` string no longer present in the file after this step.

**Dependency:** Should land after Steps 5-7 so it accurately describes the final implemented
behavior, not a planned one.

---

### Step 9 — Update `docs/engine/contracts/api_protocol_contract.md`
**Files:** `docs/engine/contracts/api_protocol_contract.md`

**Change:** Expand line 15 from the current one-liner
(`- `GET /health`: Health status and version.`) to describe the new response shape and status
semantics:
```
- `GET /health`: Engine liveness. Returns `status` (`ok` | `degraded` | `unhealthy`), computed
  from the V2EngineManager background tick thread's liveness and last-tick recency, independent
  of operator-pause state. Also returns `version`, `timestamp`, and an `engine` object
  (`thread_alive`, `paused`, `last_tick_age_seconds`, `staleness_threshold_seconds`,
  `errors_total`, `run_id`). HTTP 503 on `unhealthy` (thread dead); HTTP 200 for `ok`/`degraded`.
```
This doc line "isn't factually wrong today, but... incomplete once `/health` starts returning
degraded/unhealthy statuses with new fields" (investigation's own framing) — this step is the
completion of that, squarely inside the ticket's own named Scope (the ticket's Scope bullet
explicitly covers `/health`'s new behavior).

**Other writers:** none — single-file doc fix.

**Do NOT touch:** the rest of this file's REST/WebSocket/Transport sections (lines 16-30) —
unrelated to this ticket.

**Verify:** Manual read-and-confirm; no automated doc-content test exists or is being added for
this file (consistent with Step 8's Test 5 approach).

**Dependency:** Requires Steps 1-3 (the response shape must be finalized before documenting it).

---

### Step 10 — Add parity ledger entry `INFRA-358`
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed the file is a flat YAML list (`python3 -c "import yaml; ..."` check
performed during planning) and the highest existing ID is `INFRA-357`
(`docs/parity_ledger/infrastructure.yaml:10523`) — **before appending, the implementer must
re-grep for the current highest `INFRA-` ID at implementation time**, since other in-flight
tickets may append entries between planning and implementation (this file has many concurrent
writers across the whole ticket backlog — confirmed by the density of recent IDs INFRA-343 through
INFRA-357 already in the file). Append a new entry (do not insert/reorder) matching the existing
schema (`id`, `text`, `status`, `priority`, `legacy_evidence`, `v2_evidence`, `test_path`):
- `id: INFRA-358` (or next available if the re-grep finds a higher ID already landed)
- `status: verified`
- `priority: P0` (matches ticket priority and both source audits' independent P0 ranking, per
  investigation)
- `legacy_evidence: null` (no V1 equivalent — this is new V2-only liveness behavior)
- `v2_evidence`: cite `src/api/engine_manager.py` (`is_thread_alive`, `last_tick_age_seconds`,
  `get_health_status()` — Steps 1-2), `src/api/server.py`'s `/health` route (Step 3),
  `src/observability/watchdog.py`'s `AlertsManager` wiring (Step 5)
- `test_path`: `tests/unit/api/test_engine_manager.py` (required for `P0` per
  `docs/parity_ledger/schema.json`'s conditional: `status in [verified, divergent]` requires both
  `v2_evidence` and `test_path`)
- `text`: summarize the divergence from legacy (`/health` previously always returned `ok`; now
  reflects real thread liveness/staleness) and the new watchdog-to-AlertsManager wiring, following
  this file's existing prose style (see `INFRA-356` for an example of the expected level of
  detail).

**Other writers to this file:** many — this is a shared, append-only ledger written by every
ticket that changes tracked infrastructure behavior. This step only appends one new entry at the
end (or wherever the re-grepped next-ID lands); it must not reorder, edit, or remove any existing
entry (`INFRA-273` through `INFRA-357` and earlier, all untouched).

**Do NOT touch:** `INFRA-273` (the unrelated in-kernel tick-budget watchdog entry — confirmed by
investigation as a different mechanism, same alert-type name only) or any other existing entry.

**Verify:** `tests/unit/api/test_engine_manager.py` (cited as `test_path`) passes; schema
validation (`validate_frontmatter.py` / ledger schema check, whatever the project's existing
ledger-validation step is) passes.

**Dependency:** Requires Steps 1-6 (needs final file:line citations from the real implementation).

## Scope Guards

- Do not touch `src/engine/kernel.py`'s own existing in-kernel tick-budget watchdog or its two
  `create_watchdog_trip` call sites (lines 441, 600) — different mechanism, already correct,
  explicitly out of this ticket's scope per investigation and `test_plan.md`.
- Do not touch `tests/unit/core/test_watchdog.py` — unrelated `CertificationHarness`/
  `ArenaStopCondition.WATCHDOG` arena-hang-detection mechanism, same word ("watchdog") but a
  different subsystem entirely.
- Do not touch `docs/engine/contracts/infrastructure_overview.md`'s adjacent "self-healing
  watchdog" language (lines 148, 158) — confirmed real drift by investigation, but explicitly not
  named in this ticket's Scope section; leave as a noted future-ticket candidate only.
- Do not weaken or change the field names/semantics `tests/api/test_rest_parity.py:18-22` already
  asserts (`data["status"] == "ok"`, `data["version"] == "v2"`, HTTP 200) for the healthy,
  freshly-started case — the new implementation must keep returning exactly this for a normal
  startup, only adding new failure-mode behavior.
- Do not modify `WebhookAlertSink`'s backoff implementation (`sinks.py:87`, linear despite a
  comment claiming exponential, no jitter, no circuit breaker) — explicitly separate Epic H scope
  per `docs/plans/architecture_resilience_remediation_roadmap.md`; reuse the sink as-is.
- Do not build container-level auto-restart-on-engine-crash orchestration — explicitly Out of
  Scope in the ticket.
- Do not build a bespoke automated doc-path-existence checker for Step 8/9's doc fixes — a manual
  read-and-confirm recorded in the ticket's Completion Summary is sufficient per `test_plan.md`'s
  Test 5 guidance; that general-purpose tooling belongs to Epic C, not this ticket.
- Do not conflate `docker-compose.yml`'s `watchdog` service `restart: unless-stopped` (restarts
  the watchdog container on its own crash) with any backend-engine-thread restart mechanism — no
  such mechanism exists or is being built.
- Do not merge or share state between `get_health_status()` (Step 2) and `get_metrics_snapshot()`/
  `_latest_metrics_snapshot` (the existing `/metrics` read path) — keep them as separate,
  independent read paths.

## Dependency Map

```
Step 1 (raw accessors) ──> Step 2 (get_health_status) ──> Step 3 (route wiring) ──> Step 4 (tests)
                                                                                          │
Step 5 (watchdog → AlertsManager wiring, independent) ──> Step 6 (watchdog tests)         │
        │                                                                                 │
        └──> Step 7 (docker-compose env vars)                                             │
                                                                                            │
Steps 1-7 ──> Step 8 (simulation_watchdog.md doc fix)                                     │
Steps 1-3 ──────────────────────────────────────────> Step 9 (api_protocol_contract.md) ──┤
Steps 1-6 ──────────────────────────────────────────> Step 10 (INFRA-358 ledger entry) ───┘
```

Steps 1-4 (the `/health` liveness work) and Steps 5-6 (the watchdog alert-wiring work) are
independent of each other and can be implemented in either order or interleaved. Steps 7-10
(config, docs, ledger) depend on the corresponding code steps being finalized first, since they
document/configure the real implemented behavior rather than a planned one.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `/health` returns a status that actually changes when the engine thread is killed/hung in a test scenario | Steps 1, 2, 3 | `tests/unit/api/test_engine_manager.py::test_get_health_status_killed_thread_reports_unhealthy`, `::test_get_health_status_stale_tick_reports_degraded`, `tests/api/test_health_liveness.py::test_health_route_wiring_returns_ok_for_healthy_engine` (Step 4) |
| The watchdog doc's status and file-path claims match the real, running implementation | Step 8 | Manual read-and-confirm (Test 5 in `test_plan.md`) |
| At least one critical-escalation path reaches somewhere outside a log line, or the doc explicitly and accurately says it doesn't yet | Steps 5, 6, 7, 8 | `tests/unit/observability/test_watchdog.py::test_run_cycle_trip_routes_alert_event` (Step 6); doc honesty confirmed manually (Step 8) |
| (Implicit regression guard, not a numbered AC but explicitly named in Scope/investigation) `/health` must not report unhealthy during a normal operator pause | Step 2 | `tests/unit/api/test_engine_manager.py::test_get_health_status_paused_stays_ok` (Step 4) |

## Anti-Drift Notes

- **The single most likely implementation shortcut to avoid:** wiring `/health` (or
  `get_health_status()`) against the existing `is_running` property (`engine_manager.py:308-310`,
  `self._running.is_set() and not self._paused.is_set()`) instead of the new `is_thread_alive`
  accessor. `is_running` conflates "alive" with "not paused" — using it would make
  `test_get_health_status_paused_stays_ok` fail. Use `is_thread_alive` + pause-aware staleness, as
  specified in Step 2, not `is_running`.
- **`WebhookAlertSink` is always registered but often inert.** Do not describe Step 5/6/7's wiring
  as "external alerting is now live" without the caveat that it stays disabled (`LogAlertSink`-only
  in practice) until an operator sets `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED`. Step
  8's doc fix must carry this caveat exactly, not overclaim.
- **`AlertDeduplicator`'s 60s suppression window is intentional, not a bug** — once tripped, a
  stable `run_id` means only the first `WatchdogTrip` in any 60s window reaches a sink even though
  `run_cycle()` re-evaluates the trip condition every ~10s poll. Do not "fix" this as if it were
  alert-loss; it is documented storm-prevention behavior of the reused `AlertDeduplicator`.
  component.
- **`docs/parity_ledger/infrastructure.yaml` has many concurrent writers across the ticket
  backlog.** Step 10's implementer must re-check the current highest `INFRA-` ID immediately
  before appending, not trust the `INFRA-358` number decided during planning as final if time has
  passed and other tickets landed entries in between.
- **HTTP 503 on `unhealthy` is a deliberate, scoped decision, not a guess** — it may surprise
  existing external monitoring that assumed `/health` never returns non-200. This is exactly the
  ticket's intent (a healthy-looking process must stop looking healthy when the engine is actually
  dead) and is explicitly named in the AC ("ideally a non-200 status code"); do not walk it back to
  keep monitoring dashboards quiet.

## Deviations

- **Step 3**: after replacing the `/health` stub, `import time` at the top of `src/api/server.py`
  became unused (no other Python-level `time.` call exists in the file; `get_health_status()`
  itself now supplies `timestamp`). Removed the import as a direct, safe consequence of the
  planned edit — not a new plan step, no behavior change, confirmed via grep before removal that
  nothing else in the file depended on it.
- **Verification of Step 3/4's regression guard** (`tests/api/test_rest_parity.py`): the test could
  not be executed in the implementation sandbox — it launches `python3 -m src serve` as a
  subprocess, and the bare `python3` on `PATH` is the system interpreter, which lacks `pydantic`
  (pre-existing, environment-only; confirmed identical on unmodified `main` via `git stash`, not
  caused by this ticket's changes). No change was made to the test file. The healthy-path behavior
  it asserts (`GET /health` -> HTTP 200, `status: "ok"`, `version: "v2"`) was independently
  confirmed correct by starting the real V2 server with `.venv/bin/python3 -m src serve` and
  polling `/health` with `curl` directly — response matched exactly.
