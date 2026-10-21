---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT

## Title
The watchdog GETs backend:8000/metrics, which is behind require_admission (401), so with admission on, check_metrics fails every 10 s and WatchdogTrip fires continuously

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- src/observability/watchdog.py:47 GETs BACKEND_URL/metrics (default http://backend:8000).
- server.py:176 puts /metrics behind Depends(require_admission). The comment in docker/prometheus.yml says it returns 401.
- If admission is enforced in compose, check_metrics fails every 10 s, so WatchdogTrip fires continuously, limited only by the 60 s dedup.
- tests/unit/observability/test_watchdog.py mocks check_metrics, so no test sees it.

## Scope
- Confirm the compose behaviour (admission enforced or not).
- Fix direction:
  - read the R1 metrics port (backend:9109); or
  - retire the watchdog in favour of a Prometheus stall rule. That part is platform's, so coordinate with platform-planner.
- Add a test against the real endpoint shape: an admission-gated 401 must not count as a stall.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The watchdog reads an endpoint it is allowed to read, or is retired with platform's OK.
- A test covers the 401 case.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/watchdog.py, src/api/server.py:176, docker/prometheus.yml, tests/unit/observability/test_watchdog.py

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes
Scoped by reading origin/main 735a1c635 (read-only, nothing run); plan approved by rpg-planner on 2026-10-21, with the 401 ruling below. Built as planned.

### Findings
1. **What the watchdog polls.** `src/observability/watchdog.py` makes three polls per cycle: `GET {BACKEND_URL}/health` (L29), `GET {BACKEND_URL}/metrics` (L47, looks for the `sim_current_tick` line, L53-61), and Loki (L74). `BACKEND_URL` defaults to `http://backend:8000` (L12); compose sets the same (`compose.yaml` L331). `/metrics` is `@app.get("/metrics", dependencies=[Depends(require_admission)])` (`src/api/server.py` L176); `/health` (L186) has no dependency, so it is open.
   - The gate is the API KEY, not the admission mode. `require_admission` (`src/api/admission_control.py` L199) chains `require_api_key` (`src/api/auth.py` L84): no valid `X-API-Key` gives 401 at once; admission control itself only answers 429, and only in SURVIVAL (L204-208). The ticket's "admission" wording should say "API key".
   - Keys come from `--api-key-hashes` (`src/cli/entry.py` L31, default `None`) into `profile.api_key_hashes`, parsed by `configure_api_keys` (`auth.py` L30). With none configured `_client_keys` is empty, so EVERY key fails: 401 for `/metrics` always. Nothing in compose passes the option (no `api-key` in `compose.yaml` or `docker/backend.Dockerfile`), and `docker/prometheus.yml` L6-7 and `compose.yaml` L34-35 say `/metrics` on 8000 returns 401. A real run confirms it: `docs/runbooks/records/2026-10-19-api-slo-alert-fire-test.md` L23, "`GET :8000/metrics` returns 401 (still gated)".
   - By profile: **compose** (observability profile, where `watchdog` lives: `compose.yaml` L5-6, L319-344): 401 unless the operator adds `--api-key-hashes` AND gives the watchdog a key, which it has no setting for; so as shipped, `check_metrics` returns `(False, "Metrics HTTP 401")` every cycle. The loop sleeps `POLL_INTERVAL`=10 s (L139), `consecutive_failures` passes 3 on the third cycle, and the trip is routed every cycle after that, limited only by `AlertDeduplicator`'s suppression window (the ticket says 60 s; I did not verify the number). **local** (`python -m src.cli ... serve`, no watchdog started): the same 401 would apply if someone ran the watchdog by hand. **CI**: no watchdog runs in CI (compose observability profile only); the unit test patches `check_metrics`.
2. **Does 9109 expose the same value?** Yes. `start_metrics_port(self._metrics_registry)` (`src/api/engine_manager.py` L249) serves the SAME registry the API's `/metrics` serves (`generate_latest(manager.metrics_registry)`, `server.py` L177-178), via `prometheus_client.start_http_server` with no auth (`src/api/metrics_port.py` L63-82; port `BACKEND_METRICS_PORT` default 9109, host `BACKEND_METRICS_HOST` default 0.0.0.0). `sim_current_tick` is a collector in that registry (`src/observability/prometheus_collector.py` L29). Compose exposes 9109 on the compose network only (`compose.yaml` L36-37) and Prometheus already scrapes `backend:9109` (`docker/prometheus.yml` L36-38). So "read 9109" works with no auth change. Caveat: if the port cannot be bound, `start_metrics_port` returns None (logged) and 9109 is down while the API runs: the watchdog must treat a refused connection as a failure (as it does today) and not as a stall.
3. **What the test fakes.** `tests/unit/observability/test_watchdog.py` patches `SimulationWatchdog.check_metrics` itself (`return_value=(True, "Tick 42")`, L33) in the one run_cycle test; the other two tests patch `requests.get` for `check_health` only. `check_metrics` has no test at all: no HTTP status, no `sim_current_tick` parsing, no stall branch.
4. **Platform.** The code fix is rpg's (`watchdog.py`, its test, `docs/architecture/simulation_watchdog.md` L26-27 which names `/metrics`). One platform line is needed for compose: `compose.yaml` watchdog service `environment:` gets `METRICS_URL=http://backend:9109` (the code default can already be that, so compose would work unchanged; the line only makes it explicit). The alternative in the ticket, retiring the watchdog for a Prometheus stall rule, would be platform's: `docker/grafana/provisioning/alerting/rules-*.yaml` and `docker/prometheus.yml`, plus removing the `watchdog` service from `compose.yaml`. No alerting change is needed for the read-9109 fix.

### Plan (read 9109; not retire)
- `watchdog.py`: new `METRICS_URL = os.environ.get("METRICS_URL", "http://backend:9109")`; `check_metrics` GETs `{METRICS_URL}/metrics`. Keep `/health` on `BACKEND_URL`. Pure function `parse_tick(text)` for the line parse (exact metric name match, `sim_current_tick ` with a space, so a longer name such as `sim_current_tick_total` cannot match by prefix: today's `startswith` would).
- Classification, kept explicit: HTTP 200 with a tick line: advance/stall logic as today. 401/403 (a gated endpoint): return `(True, "Metrics endpoint gated (HTTP 401); not a stall")` and log a warning once; a gate is a configuration fact, not a sign the sim stopped (the ticket's AC: "an admission-gated 401 must not count as a stall"). Any other non-200, a refused connection or a timeout: still a failure, as today. Tick equal to the last tick: still `Tick Stalled`.
- Tests (`tests/unit/observability/test_watchdog.py`, or a new file next to it): `check_metrics` against a real local `prometheus_client` registry served by `start_metrics_port` on port 0 (the true endpoint shape, no mock of `check_metrics`); a 401 from a tiny local HTTP server is not a failure; a stalled tick is; a refused connection is; a longer metric name is not matched.
- Docs: `simulation_watchdog.md` responsibility 1 says it polls the internal metrics port; ticket Completion Summary; parity entry only if one names the watchdog (grep first).
- Platform ask (one line, after rpg-planner agrees): the `METRICS_URL` env line above in `compose.yaml`; nothing else. Retiring the watchdog is NOT proposed here.
- No simulation file is touched, so no hash check is needed. Serial tests only.

### Ruling (rpg-planner, 2026-10-21) on 401/403
After the switch, a 401/403 from the metrics port means the watchdog is misconfigured and blind, not that the sim stalled. So: reason `Metrics gated (HTTP 401)`; not counted toward `consecutive_failures`; its own `WatchdogBlind` alert (existing alert path and dedup, no new knob). Built: `SimulationWatchdog.metrics_blind` set by `check_metrics`, `run_cycle` routes `AlertEvent.create_watchdog_blind` (alert_type `WatchdogBlind`, severity ERROR, dedup key `watchdog-blind:{run_id}`).

### Built
- `src/observability/watchdog.py`: `METRICS_URL` (default `http://backend:9109`), `parse_tick` (exact name, labels allowed), the 401/403 branch, `_route_blind_alert`. `/health` stays on `BACKEND_URL`.
- `src/observability/alerts/models.py`: `AlertEvent.create_watchdog_blind`.
- `docs/architecture/simulation_watchdog.md`: responsibility 1 rewritten.
- Dedup window verified from code: `AlertDeduplicator(suppression_window_seconds=60.0)` and `AlertsManager.get_router` uses `SIM_ALERTS_DEDUP_WINDOW_SECONDS` else 60.0 (alerts/deduplicator.py, alerts/manager.py L24-28). The ticket's "60 s" is right. It is a fixed window from the first alert (the entry is not refreshed while suppressed).
- Parity: no ledger entry covered the external watchdog (the `watchdog` hits in docs/parity_ledger are the kernel's tick-budget watchdog), so INFRA-438 was added (verified, P2, test_watchdog_metrics_source.py; no schema error on the entry, the ledger-wide ratchet reports 0 new).
- compose.yaml: unchanged by ruling; the code default `http://backend:9109` covers it. fyi for platform-planner (PR notes): the watchdog service now reads `backend:9109` (set `METRICS_URL` to override); nothing in compose needs editing.
- No simulation file touched, no hash check needed.
