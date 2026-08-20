---
status: historical
layer: observability
authority: P1
audience: agent
maturity: shipped
archived: 2026-08-20
tags: [observability, engine]
---

# Epic Plan — Engine Liveness & Real Health Signal

**Tracking ticket:** `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §D, §K (R2)
**Priority:** P0 — the second of the two findings both audits independently rank highest; a silent engine stall behind a healthy-looking process is the worst kind of failure (invisible until someone notices gameplay has stopped).

## Status
Resolved by `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`. The Problem section below now describes
pre-fix history, not current state: `/health` (`src/api/server.py`) now calls
`V2EngineManager.get_health_status()`, returning `ok`/`degraded`/`unhealthy` computed from the
background tick thread's `.is_alive()` state and last-tick staleness (pause-aware — a deliberate
`POST /api/v1/control/pause` no longer reads as unhealthy), and the route maps `unhealthy` to HTTP
503. `SimulationWatchdog`'s critical escalation (`src/observability/watchdog.py`) now also routes
a `WatchdogTrip` `AlertEvent` through the existing `AlertsManager`/`AlertRouter`/`WebhookAlertSink`
stack, using a `run_id` read from `/health`'s new `engine.run_id` field; the webhook sink stays
disabled by default (new, default-disabled env vars added to `docker-compose.yml`'s `watchdog`
service) until an operator configures `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED`.
`docs/architecture/simulation_watchdog.md`'s `Status`, file-path, and responsibility claims were
corrected in the same change. Parity ledger entry `INFRA-358` (`docs/parity_ledger/infrastructure.yaml`)
tracks this. Left in place (not archived) per this repo's convention that whole-epic archival is a
separate human decision.

## Problem

`/health` (`src/api/server.py:126-128`) is a hardcoded stub:

```python
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    return {"status": "ok", "version": "v2", "timestamp": time.time()}
```

It never checks whether `V2EngineManager`'s background thread (`"v2-engine-loop"`) is alive,
ticking, or has crashed. If that thread dies while the FastAPI process stays up, `/health`
continues reporting `ok` forever. The only real signal today is `/metrics`' `sim_current_tick`
stall detector inside `SimulationWatchdog` (`src/observability/watchdog.py`), which polls every
10s and, after 3 consecutive stalled cycles, calls `logger.critical(...)` — and nothing else. No
PagerDuty/Discord/webhook dispatch is implemented despite `docs/architecture/simulation_watchdog.md`
describing the watchdog as able to "trigger external alerts"; that doc is also marked
`Status: Proposed` while being referenced elsewhere as if built, and cites a file path
(`src/utils/watchdog.py`) that doesn't match the real implementation. `docker-compose.yml`'s
`restart: unless-stopped` restarts the *container*, not anything engine-aware — a hung engine
thread inside a healthy container will never trigger a restart.

## Scope for the eventual `create-tickets` pass

- Make `/health` check `V2EngineManager` background-thread liveness plus last-tick recency
  (e.g. thread `.is_alive()` plus a max-staleness check on the current tick timestamp), returning
  a real degraded/unhealthy status rather than a hardcoded `ok`.
- Wire at least one real external alert channel for `SimulationWatchdog`'s critical escalation
  path, or explicitly correct `docs/architecture/simulation_watchdog.md` to state it is log-only
  today rather than implying external dispatch exists.
- Fix `docs/architecture/simulation_watchdog.md`'s file-path claim (`src/utils/watchdog.py` →
  `src/observability/watchdog.py`) and its `Status: Proposed` header if the doc's own scope is
  meant to describe what's actually running.

## Out of scope

- Container-level auto-restart-on-engine-crash orchestration (e.g. a supervisor process) — a
  larger deployment-infrastructure decision than this epic's scope; `/health` reflecting the
  truth is the prerequisite for any such mechanism to even be built correctly later.
- Building a full external alerting integration (PagerDuty, Discord, etc.) beyond "at least one
  real channel wired" — scope the specific channel choice into the eventual child ticket(s).

## Acceptance signal for this epic (not yet broken into child tickets)

- `/health` returns a status that actually changes when the engine thread is killed/hung in a
  test scenario.
- The watchdog doc's status and file-path claims match the real, running implementation.
- At least one critical-escalation path reaches somewhere outside a log line, or the doc
  explicitly and accurately says it doesn't yet.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic B)
- `docs/audits/D23_architecture_resilience.md` (R2, Stage 1 item 1)
