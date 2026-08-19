---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
artifact_type: investigation
tags: [observability, engine]
---

# Investigation — TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

## Current Behavior

**`/health` is a hardcoded stub.** `src/api/server.py:126-128`:
```python
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    return {"status": "ok", "version": "v2", "timestamp": time.time()}
```
It takes no dependency on `V2EngineManager` at all — confirmed, it is the only route handler in
`server.py` that does not use `Depends(get_engine_manager)`. It cannot reflect engine state because
it never reads it.

**`V2EngineManager` (`src/api/engine_manager.py:17`) has no last-tick-recency tracking exposed, but
does have the raw material for it.** Confirmed:
- `self._thread: Optional[threading.Thread]` (line 28) is never exposed via a public property —
  there is no `.is_alive()` accessor today. `kernel`, `started_at`, `errors_total`, `tick`,
  `is_running`, `is_paused`, `is_stopped`, `is_stopping` are all public properties (lines 303-334);
  thread liveness is not among them.
- `self._tick_times = deque(maxlen=100)` (line 50) already records `time.time()` on every
  successfully completed tick (`_run_loop`, line 288: `self._tick_times.append(time.time())`,
  inside `self._state_lock`). This is a real, already-running last-tick-recency signal — it just
  isn't exposed through any accessor. `get_tps()` (lines 64-71) is the only current consumer, and
  it only uses the *spread* between the oldest/newest entries, not "how long ago was the last one."
- `is_running` (line 308-310) is **not** thread-aliveness — it's `self._running.is_set() and not
  self._paused.is_set()`. A deliberately paused engine (`POST /api/v1/control/pause`, a supported,
  intentional operator action) reports `is_running == False` even though the thread is alive and
  healthy. Naively wiring `/health` to `is_running` would make a normal pause look like an outage.
  This is a real design trap for the Plan phase — the health check needs `_thread.is_alive()` (new
  accessor) as the liveness signal, and last-tick recency (new accessor over `_tick_times[-1]`) as
  the staleness signal, evaluated independently of pause state (a fresh-enough last tick plus an
  alive thread is healthy whether or not `_paused` is set; a crashed thread — `_run_loop`'s
  `except Exception` at line 291-295 sets `self._errors_total += 1` then `break`s the loop, so the
  thread exits and `_running.clear()` never even fires per this exact path since `break` skips the
  loop's post-condition check — is unhealthy regardless of pause state).
- `_errors_total` (line 55, incremented at line 294) is already a public property (`errors_total`,
  line 332-334) and is a second, already-available "the engine tried to tick and failed" signal
  independent of thread-alive/recency.

**`SimulationWatchdog` (`src/observability/watchdog.py:16-121`) is confirmed log-only, exactly as
the ticket claims.** `run_cycle()` (lines 82-108) polls `/health` (`check_health`, lines 25-34) and
`/metrics`' `sim_current_tick` (`check_metrics`, lines 36-56, tick-stall detection by comparing
successive polls — not a wall-clock staleness check, a monotonic-non-increase check), and Loki
error logs (`check_loki_errors`, lines 58-80). On 3 consecutive failed cycles
(`self.max_failures = 3`, line 22; `POLL_INTERVAL=10s` default, line 14 → ~30s to trip), the only
escalation is `logger.critical(...)` at lines 106-108, `extra={'component': 'watchdog',
'diagnostics': status_report}`. No import of any alert-dispatch mechanism exists anywhere in this
file — confirmed via full read, not partial.

**A real, already-wired external-alert-dispatch mechanism exists elsewhere in the codebase and is
directly reusable — this is the single most important finding for planning.**
`src/observability/alerts/` (built by `TCK-20260520-SIM-OBS-M40`, "Alert Routing and Incident
Workflow") provides:
- `AlertsManager.get_router()` (`manager.py:16-67`) — a lazily-built, thread-safe singleton
  `AlertRouter`, configured entirely from environment variables (`SIM_ALERTS_WEBHOOK_URL`,
  `SIM_ALERTS_WEBHOOK_ENABLED`, `SIM_ALERTS_SEVERITY_THRESHOLD`, `SIM_ALERTS_DEDUP_WINDOW_SECONDS`,
  `SIM_ALERTS_WEBHOOK_TIMEOUT`, `SIM_ALERTS_WEBHOOK_RETRIES`, or the `RPG_ALERTS_*` aliases).
- `WebhookAlertSink` (`sinks.py:39-92`) — a real, already-implemented external HTTP(S) POST sink
  with bounded retry (linear backoff, not the exponential backoff the in-code comment at line 87
  claims — flagged separately by D23 §D as Epic H scope, not this ticket's concern) on a dedicated
  2-thread executor so delivery can never block a caller.
- `AlertEvent.create_watchdog_trip(run_id, tick, message, details)` (`models.py:62-73`) — **a
  factory method that already exists, specifically named for this exact use case, and is already
  called twice from `src/engine/kernel.py`** (line 441 — tick-budget-exceeded warning path; line
  600 — mid-tick emergency-throttle path) **but never from `SimulationWatchdog`.** Both existing
  call sites are for the *in-process, per-tick* kernel watchdog (tick-duration budget), a
  completely different mechanism from the *external, poll-based* `SimulationWatchdog` process this
  ticket is about — same alert type name, two different trigger sources, confirmed by reading both
  call sites and `stored_artifacts/TCK-20260520-SIM-OBS-M40/plan.md:29,40,88` (which describes the
  "Watchdog Trip" alert as specifically the in-kernel tick-budget mechanism).
- This means "wire at least one real external alert channel" for `SimulationWatchdog`'s critical
  escalation does **not** require writing a new sink — it requires importing
  `src.observability.alerts.manager.AlertsManager` and `src.observability.alerts.models.AlertEvent`
  into `src/observability/watchdog.py` and calling `AlertsManager.get_router().route(
  AlertEvent.create_watchdog_trip(...))` at the same point `logger.critical(...)` fires today
  (lines 106-108). `manager.py`'s only imports are `router.py`/`deduplicator.py`/`sinks.py` — no
  coupling to `src.engine` or `src.core.state` — so importing it from the standalone `watchdog.py`
  process (a separate container in `docker-compose.yml`, not the `backend` process) is safe with no
  circular-import or heavyweight-dependency risk.
- **Real gap for Plan to resolve:** `docker-compose.yml`'s `watchdog` service (lines 120-134)
  currently passes only `BACKEND_URL`, `LOKI_URL`, `POLL_INTERVAL`, `LOG_LEVEL` as environment
  variables — none of the `SIM_ALERTS_*`/`RPG_ALERTS_*` webhook-config vars. Without adding at
  least `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` (or documenting that they must be
  supplied at deploy time), the webhook sink stays disabled by default
  (`webhook_enabled=False` unless explicitly configured — `manager.py:31-34`) and the watchdog's
  escalation remains effectively log-only in practice even after the code wiring lands. Also:
  `create_watchdog_trip` requires a `run_id` and `tick` the external watchdog process doesn't
  naturally have (it only tracks `self.last_tick`, a float from `/metrics` text parsing, and has no
  concept of "run_id" — that's an engine-internal concept). A placeholder (e.g.
  `run_id="external-watchdog"`, `tick=int(self.last_tick)`) is workable but is a real design
  decision, not a mechanical wiring step — flagged under Open Questions.
- **Dedup interacts with the trip cadence.** `AlertDeduplicator`'s default suppression window is
  60s (`manager.py:26`, `dedup_key=f"watchdog:{run_id}"` — `models.py:72`). With
  `POLL_INTERVAL=10s` and `max_failures=3`, a trip fires every ~10s cycle once tripped (the
  `consecutive_failures >= max_failures` condition stays true every cycle until recovery, at
  `watchdog.py:106`), so a fixed `run_id` would silently suppress all but the first trip within any
  60s window — actually desirable (storm prevention) but should be a stated, not accidental,
  property of the implementation.

**No last-tick wall-clock timestamp is exposed via `/metrics` today.**
`PrometheusMetricsCollector.collect()` (`src/observability/prometheus_collector.py:16-184`) exposes
23 metrics (`sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, etc.) sourced from
`V2EngineManager.get_metrics_snapshot()` — none of them is a last-tick wall-clock timestamp. This
confirms `SimulationWatchdog.check_metrics()`'s approach (compare successive `sim_current_tick`
polls for non-increase) is the only existing staleness signal, and it is poll-interval-grained
(detects "hasn't ticked since I last checked," not "hasn't ticked in N seconds"). This is a
distinct, coarser mechanism from what `/health` needs to build (a direct, in-process max-staleness
check against `_tick_times[-1]`), and the two need not be unified for this ticket's scope.

**`docs/architecture/simulation_watchdog.md` mismatches, confirmed exactly as the ticket states:**
- Line 10-11: `## Status` / `Proposed` — but the described artifact is the real, running
  `docker-compose.yml` `watchdog` service (lines 120-134), not a proposal.
- Line 22: "`src/utils/watchdog.py`" — that path does not exist
  (`find src/utils -iname 'watchdog*'` → nothing). The real file is
  `src/observability/watchdog.py`.
- Line 28: "trigger external alerts (PagerDuty, Discord, etc.)" as a described "Key
  Responsibility" — not implemented; confirmed log-only above.
- Adjacent, same-shape drift **not** named in this ticket's explicit scope but discovered during
  investigation: `docs/engine/contracts/infrastructure_overview.md:148,158` independently
  describes the Docker Compose stack as managing "self-healing watchdogs" and the `watchdog`
  service as a "**Self-healing** daemon auditing endpoint availability and deadlocks" — the same
  overstatement (no self-healing/remediation action exists anywhere in `watchdog.py`, only
  logging, even after this ticket's alert-wiring fix, which adds *notification*, not
  *remediation*). Flagged under Docs Requiring Update as optional/adjacent, since the ticket's own
  Scope names only `docs/architecture/simulation_watchdog.md` for the doc fix — left as an explicit
  open question for Plan rather than silently left un-mentioned.

**`GET /health` is documented, minimally and not incorrectly, in
`docs/engine/contracts/api_protocol_contract.md:15`:** `"GET /health: Health status and version."`
This line doesn't claim engine-liveness semantics today, so it isn't factually wrong — but it will
be incomplete once `/health` starts returning degraded/unhealthy statuses with new fields, so it is
a real doc-update candidate under this ticket's own scope (the API contract should describe what
the response shape and status values now mean).

## Mechanics / Engine Constraints

This is an infrastructure/observability ticket, not a simulation-mechanics change — no
`docs/mechanics/` chapter governs `/health`, `V2EngineManager` thread liveness, or watchdog alert
dispatch. The one engine-contract constraint that applies:
`docs/architecture/observability_hot_path_safety_contract.md` forbids synchronous blocking I/O in
the simulation tick's hot path. `/health`'s planned implementation (reading `_thread.is_alive()`
and `_tick_times[-1]` under the existing `_state_lock`) is read-only, O(1), and off the tick thread
(FastAPI's own async request path) — consistent with the contract, does not touch it. Wiring
`SimulationWatchdog` to `AlertsManager` is entirely outside the engine process and outside the tick
loop — no hot-path exposure either way. No divergence from `docs/guidelines/intentional_divergences.md`
is created by this ticket as scoped.

## Docs Requiring Update

- `docs/architecture/simulation_watchdog.md`: fix `## Status` from `Proposed` to reflect the real,
  running implementation; fix the `src/utils/watchdog.py` path claim to
  `src/observability/watchdog.py`; correct or qualify the "trigger external alerts" responsibility
  claim to match whatever this ticket actually wires (real dispatch via `AlertsManager`, or an
  explicit "log-only until `SIM_ALERTS_WEBHOOK_URL` is configured" statement if wiring is deferred).
- `docs/engine/contracts/api_protocol_contract.md`: `GET /health` (line 15) needs its one-line
  description expanded to state that the response now reflects real engine-thread liveness and
  last-tick recency, and to name the status values the route can return (e.g. `ok`/`degraded`/
  `unhealthy`), once that shape is decided during Plan.

## Parity Ledger Overlap

No existing parity ledger entry covers `/health`'s liveness semantics or the external
`SimulationWatchdog` service's escalation path. Searched all of `docs/parity_ledger/*.yaml` by
`text` field for `health`/`watchdog`/`/health` — the only hit is
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-273`, which is about the **in-kernel** tick-budget
watchdog / mid-tick emergency throttle (a simulation-quality/determinism finding,
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`) — a different mechanism from this ticket's scope
(confirmed above: same "WatchdogTrip" alert *type* name, unrelated trigger source). This ticket's
work has **no existing ledger entry to update** — a new `INFRA-*` entry should be added once
implemented, `priority: P0` (matching the ticket's own priority and both audits' independent P0
ranking), with a `test_path` pointing at whichever new test asserts `/health` degrades on a
killed/hung engine thread (required for P0 per `schema.json`'s conditional: `status in
[verified, divergent]` requires both `v2_evidence` and `test_path`).

## Prior Work

- `TCK-20260520-SIM-OBS-M40` (`tickets/done/TCK-20260520-SIM-OBS-M40.md`, artifacts in
  `stored_artifacts/TCK-20260520-SIM-OBS-M40/`) — built the entire `AlertsManager`/`AlertRouter`/
  `WebhookAlertSink`/`AlertEvent` stack this ticket should reuse rather than duplicate. Its
  `plan.md` explicitly scoped `create_watchdog_trip` to the in-kernel tick-budget mechanism only
  (lines 29, 40, 88) — extending it to the external `SimulationWatchdog` process is new scope, not
  a fix to something M40 got wrong.
- `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` (just-closed sibling ticket in the same roadmap,
  `stored_artifacts/TCK-20260817-DEAD-INFRA-REMOVAL-EPIC/`) — precedent for how a downgraded
  standard-tier ticket from this same roadmap approached parity-ledger and docs work: it treated
  "no existing ledger entry for this exact finding" as a signal to add a new entry rather than
  force-fit into an unrelated one, and scoped doc fixes narrowly to what the ticket's own Scope
  named rather than sweeping in every adjacent drift discovered along the way (mirrors this
  investigation's treatment of `infrastructure_overview.md`'s "self-healing" language as an
  adjacent-but-optional finding, not mandatory scope).
- `staging_artifacts/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC/{investigation,plan,test_plan}.md`
  (pre-existing, dated 2026-08-19 00:07, this session): these are placeholder artifacts written
  while this ticket was still epic-tier ("scope-only", explicitly stating "No fresh investigation
  performed... deferred to when this epic is formally scoped"). This file replaces the stale
  placeholder `investigation.md` and `test_plan.md` now that the ticket has been downgraded to
  standard tier and requires real pre-implementation artifacts; `plan.md` is unchanged by this
  investigation and remains the planner's responsibility to replace next.

## Risks and Open Questions

- **Blocks Plan — pause-vs-crash disambiguation.** `/health` must not report unhealthy just because
  an operator called `POST /api/v1/control/pause`. The implementation must use `_thread.is_alive()`
  (new accessor) + last-tick recency independent of `is_paused`, not the existing `is_running`
  property (which conflates "alive" with "not paused"). Flagging so Plan doesn't default to the
  more obvious-looking `is_running` property.
- **Open — max-staleness threshold value.** No existing constant defines "how stale is too stale."
  Candidates: a multiple of `self._tick_rate` (0.05s / 20 TPS default, `engine_manager.py:34`), or
  a fixed wall-clock bound (e.g. 5-10s) independent of tick rate. Needs a decision in Plan; not
  guessable from existing code since nothing today measures tick-to-tick wall-clock gaps for this
  purpose.
- **Open — external-watchdog `run_id`/`tick` values for `create_watchdog_trip`.** The external
  `SimulationWatchdog` process has no `run_id` concept and only a float-parsed `last_tick` from
  `/metrics` text. A placeholder scheme is workable but should be an explicit Plan decision, not
  silently improvised in Implement.
- **Open — whether wiring is sufficient without `docker-compose.yml` env var changes.** Code-level
  wiring to `AlertsManager` achieves nothing operationally unless
  `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` are actually set on the `watchdog` service
  (currently absent from `docker-compose.yml:120-134`). Plan must decide whether to add them (with
  a placeholder/documented-as-required value) or explicitly document that operators must supply
  them — either satisfies the AC's "at least one real channel... or explicitly and accurately
  documents that it doesn't yet," but only if the choice is deliberate and reflected in the doc fix.
- **Not blocking, but worth flagging:** `_run_loop`'s exception path (`engine_manager.py:291-295`)
  catches, logs, increments `_errors_total`, then `break`s — the loop exits and the thread ends
  without ever going through `self._running.clear()`'s normal post-loop line (line 300, which is
  after the `while` loop, so it *does* still execute on `break` — re-checked, this is actually fine:
  `break` exits the `while`, execution falls through to line 300 `self._running.clear()` and line
  301's log). No inconsistency here; `_running` does get cleared, and `_thread.is_alive()` would
  also correctly go `False` once `_run_loop` returns. Included for the record since the two
  liveness signals (`_running` flag vs. `_thread.is_alive()`) should agree in this path — confirmed
  they do.

## Anti-Drift Hazards

- **Do not confuse `tests/unit/core/test_watchdog.py`'s "watchdog" with `SimulationWatchdog`.**
  That test (`test_arena_watchdog_trigger`) exercises `CertificationHarness`'s
  `ArenaStopCondition.WATCHDOG` — an unrelated hang-detection mechanism inside the
  certification/arena test harness, not `src/observability/watchdog.py`. Same word, different
  subsystem; do not touch or "fix" it as part of this ticket.
- **`tests/api/test_rest_parity.py:18-22` currently asserts `data["status"] == "ok"` unconditionally
  after a freshly-started server (~3s uptime).** Once `/health` returns real status values, this
  test will still need to pass for a healthy freshly-started engine — do not weaken this assertion
  to "accept anything," and do not let the new implementation report degraded/unhealthy during the
  engine's normal brief startup window (a false-positive-unhealthy `/health` during normal startup
  would itself be a regression).
- **Do not extend the `AlertEvent.create_watchdog_trip` dedup/factory changes to touch the two
  existing `kernel.py` call sites (lines 441, 600).** Those are a different, already-working
  mechanism (in-kernel tick-budget watchdog) with their own `run_id`/`tick` semantics that are
  already correct — this ticket only adds a *third* call site from the external
  `SimulationWatchdog`, it does not modify the existing two.
- **Do not scope-creep into Epic H's `WebhookAlertSink` backoff/circuit-breaker fix** (linear vs.
  claimed-exponential backoff, no jitter, no circuit breaker — `docs/plans/architecture_resilience_remediation_roadmap.md`
  Epic H, `sinks.py:87`) — that is explicitly separate scope in a different epic; reuse
  `WebhookAlertSink` as-is.
- **Do not scope-creep into container-level auto-restart-on-crash** — explicitly Out of Scope in
  the ticket; `/health` reflecting the truth is the prerequisite for such a mechanism, not this
  ticket's job to build it.
- **`docker-compose.yml`'s `watchdog` service `restart: unless-stopped` (line 134) restarts the
  watchdog container itself if it crashes — it does not and should not be conflated with restarting
  the `backend` container on an engine-thread crash.** Any doc fix should not imply otherwise.
