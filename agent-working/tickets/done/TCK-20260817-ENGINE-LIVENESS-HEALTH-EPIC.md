---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
phase: done
date: 2026-08-17
tags: [observability, engine]
---

# TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

## Title
Make /health reflect real engine liveness; fix watchdog doc/implementation mismatch

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
`/health` (`src/api/server.py:126-128`) is a hardcoded `{"status": "ok"}` with no relationship to
whether `V2EngineManager`'s background tick thread is alive. If that thread dies while the
FastAPI process stays up, `/health` reports healthy forever. The one system meant to notice —
`SimulationWatchdog` — only logs after 3 stalled 10s cycles, with no external alert dispatch
despite `docs/architecture/simulation_watchdog.md` describing it as able to trigger external
alerts; that doc is also marked `Status: Proposed` while referenced elsewhere as operative, and
cites a file path (`src/utils/watchdog.py`) that doesn't match the real implementation
(`src/observability/watchdog.py`). Both audits rank this alongside dead-infra removal as the two
highest-priority findings across the whole review — a silent engine stall behind a
healthy-looking process is the failure mode with the worst detection latency.

## Scope
Full findings are in `docs/plans/engine_liveness_health_epic.md`. Concrete scope:
- Make `/health` check `V2EngineManager` background-thread liveness plus last-tick recency,
  returning a real degraded/unhealthy status rather than a hardcoded `ok`.
- Wire at least one real external alert channel for `SimulationWatchdog`'s critical escalation,
  or explicitly correct the doc to state it's log-only today.
- Fix `docs/architecture/simulation_watchdog.md`'s file-path claim
  (`src/utils/watchdog.py` → `src/observability/watchdog.py`) and its `Status: Proposed` header.

## Out of Scope
- Container-level auto-restart-on-engine-crash orchestration (a larger deployment decision).
- A full external alerting integration beyond "at least one real channel wired."

## Acceptance Criteria
- [x] `/health` returns a status that actually changes when the engine thread is killed/hung in a
      test scenario.
- [x] The watchdog doc's status and file-path claims match the real, running implementation.
- [x] At least one critical-escalation path reaches somewhere outside a log line, or the doc
      explicitly and accurately says it doesn't yet.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/engine_liveness_health_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/architecture/simulation_watchdog.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/api/server.py
- src/api/engine_manager.py
- src/observability/watchdog.py

## Assumptions / Open Questions
- Which external alert channel (webhook, email, etc.) to wire is an open decision for Plan phase.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; doesn't meet the "large multi-ticket
  initiative" bar — a code fix, a doc fix, and one integration, closable in one standard ticket.
  `staging_artifacts/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC/` not yet created.

## Implementation Notes
Implemented all 10 steps of `staging_artifacts/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC/plan.md`
in order, no logical deviations from the plan's design decisions (staleness threshold, run_id
sourcing, pause-vs-crash disambiguation, dedup behavior all match the plan exactly).

- **Step 1-2**: Added `V2EngineManager.is_thread_alive`, `V2EngineManager.last_tick_age_seconds`,
  and `V2EngineManager.get_health_status()` in `src/api/engine_manager.py`, placed after the
  existing `errors_total` property, exactly per the plan's spec. `get_health_status()` uses
  `is_thread_alive` (not `is_running`) as the crash signal and evaluates staleness independent of
  `is_paused`, so a normal operator pause never reports unhealthy.
- **Step 3**: Wired `GET /health` in `src/api/server.py` to `Depends(get_engine_manager)` and
  `manager.get_health_status()`; HTTP 503 only on `unhealthy`, 200 for `ok`/`degraded`.
- **Step 5**: `SimulationWatchdog` (`src/observability/watchdog.py`) now tracks `self.run_id`
  (seeded `"external-watchdog-unknown"`, updated from `/health`'s new `engine.run_id` field on
  every successful poll, malformed bodies degrade to "keep last known" via a wrapping
  `try/except`). The existing critical-escalation block in `run_cycle()` now also routes a
  `WatchdogTrip` `AlertEvent` through `AlertsManager.get_router().route(...)`, wrapped in its own
  `try/except` mirroring the two existing `kernel.py` call sites; the existing
  `logger.critical(...)` line is untouched.
- **Step 7**: `docker-compose.yml`'s `watchdog` service gained
  `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` env vars, both default-disabled/empty via
  `${VAR:-default}` substitution.
- **Step 8-9**: `docs/architecture/simulation_watchdog.md` — `Status: Proposed` -> `Active`,
  `src/utils/watchdog.py` -> `src/observability/watchdog.py`, and the "Self-Correction/Alerting"
  responsibility rewritten to describe the real `AlertsManager`/webhook-gated behavior (no
  PagerDuty/Discord claim). `docs/engine/contracts/api_protocol_contract.md`'s `GET /health` line
  expanded to describe the new response shape and status/HTTP-code semantics.
- **Step 10**: Appended `INFRA-358` to `docs/parity_ledger/infrastructure.yaml` (re-grepped
  immediately before appending; highest existing id was still `INFRA-357`, no collision).
  Validated the new entry against `docs/parity_ledger/schema.json`'s per-item schema directly
  (`jsonschema.validate`) — passes. A pre-existing, unrelated schema violation at a different
  index (`proof_type: "feature"`, not in this ticket's scope) exists elsewhere in the file and was
  not introduced or touched by this change.
- **Minor, in-scope-adjacent cleanup**: removed `import time` from the top of `src/api/server.py`
  — it became unused once `/health` stopped calling `time.time()` directly (the value now comes
  from `get_health_status()`'s own `now = time.time()`), and no other code in the file uses the
  `time` module. Not called out as a plan step but a direct, safe consequence of Step 3's edit
  (confirmed via grep no other Python-level `time.` usage in the file before removing).
- **Regression risk (flagged in the assignment) verified by direct run, not just by reading**:
  `tests/api/test_rest_parity.py:18-22` cannot execute in this sandbox at all — it launches
  `python3 -m src serve ...` as a subprocess, and the bare `python3` on `PATH` is the system
  interpreter (`/usr/bin/python3`), which lacks `pydantic` (only the project's `.venv` has it).
  Confirmed via `git stash` that this subprocess-launch failure is 100% pre-existing and
  identical on unmodified `main` — not a regression introduced by this ticket. To verify the
  actual behavior this test asserts, the real V2 server was started directly with
  `.venv/bin/python3 -m src serve` and polled with `curl`: response was HTTP 200,
  `{"status":"ok","version":"v2",...}` — i.e. the exact shape/status/HTTP-code the test's
  assertions require for a healthy freshly-started engine is preserved bit-for-bit. No change was
  made to `tests/api/test_rest_parity.py` itself, consistent with the plan's Scope Guard.

## Test Summary
Final re-scoped command, per `test_plan.md`'s "Scoped Pytest Commands" section (Finalize
re-verification, `.venv/bin/python3 -m pytest`):
```
tests/api/test_health_liveness.py tests/api/test_rest_parity.py tests/api/test_live_health_api.py \
tests/api/test_scenario_runtime_api.py tests/unit/api/ \
tests/unit/observability/test_watchdog.py tests/unit/observability/test_alert_router.py \
tests/unit/core/test_watchdog.py -v
```
Result: **63 collected, 60 passed, 3 failed.** Per-file breakdown:
- `tests/api/test_health_liveness.py` (1 new test) — passes.
- `tests/unit/api/test_engine_manager.py` (6 new tests) — all pass.
- `tests/unit/api/` remaining regression surface (`test_economy_route.py`,
  `test_read_model_cache.py`, `test_read_model_service.py` — 15 tests, unmodified) — all pass.
- `tests/unit/observability/test_watchdog.py` (3 new tests) — all pass.
- `tests/unit/observability/test_alert_router.py` (regression guard, unmodified, 23 tests) — all
  pass, including `test_factory_watchdog_trip`.
- `tests/unit/core/test_watchdog.py` (regression guard, unrelated arena-watchdog mechanism,
  unmodified, 1 test) — passes.
- `tests/api/test_scenario_runtime_api.py` (11 tests, unmodified) — all pass, confirming no
  import-time/startup regression from touching `server.py`.
- `tests/api/test_rest_parity.py::test_api_rest_parity`,
  `tests/api/test_rest_parity.py::test_api_compression`, and
  `tests/api/test_live_health_api.py::test_live_health_api_suite[asyncio]` — the 3 deselection-
  worthy failures. All three launch a real server via bare `subprocess.Popen(["python3", ...])`;
  the sandbox's bare `python3` (distinct from `.venv/bin/python3`) lacks `pydantic`, so the
  subprocess dies at import (`ModuleNotFoundError: No module named 'pydantic'`) before it can bind
  its port, and every request against it then fails with `ConnectionError`. Confirmed identical on
  unmodified `main` via `git stash` — pre-existing, environment-only, not a regression introduced
  by this ticket. Real behavior independently verified via direct server run + `curl` (see
  Implementation Notes): the healthy-path response shape/status/HTTP-code is unchanged.

## Files Changed
- `src/api/engine_manager.py` — new `is_thread_alive`, `last_tick_age_seconds` properties and
  `get_health_status()` method.
- `src/api/server.py` — `/health` route wired to `V2EngineManager.get_health_status()`; added
  `JSONResponse` import; removed now-unused `import time`.
- `src/observability/watchdog.py` — `self.run_id` tracking, `check_health()` parses
  `engine.run_id` from `/health`'s body, `run_cycle()`'s trip block routes a `WatchdogTrip`
  `AlertEvent` through `AlertsManager`.
- `docker-compose.yml` — `watchdog` service gained `SIM_ALERTS_WEBHOOK_URL`/
  `SIM_ALERTS_WEBHOOK_ENABLED` env vars (default-disabled).
- `docs/architecture/simulation_watchdog.md` — `Status: Proposed` -> `Active`, file-path fix,
  honest "Self-Correction/Alerting" rewrite.
- `docs/engine/contracts/api_protocol_contract.md` — `GET /health` line expanded to describe the
  new response shape/status/HTTP-code semantics.
- `docs/parity_ledger/infrastructure.yaml` — appended `INFRA-358`.
- `tests/unit/api/test_engine_manager.py` (new file) — unit tests for the new engine-liveness
  accessors and `get_health_status()`.
- `tests/api/test_health_liveness.py` (new file) — in-process `TestClient` integration test for
  the `/health` route wiring.
- `tests/unit/observability/test_watchdog.py` (new file) — unit tests for the watchdog-to-
  `AlertsManager` wiring and `run_id` capture from `/health`.
- `tickets/inprogress/TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Status, AC checkboxes).

## Completion Summary
`/health` now reflects real `V2EngineManager` background-thread liveness and last-tick recency
instead of a hardcoded `ok` stub, returning `ok`/`degraded`/`unhealthy` (HTTP 503 only on
`unhealthy`) while staying pause-safe. `SimulationWatchdog`'s critical escalation now routes a
`WatchdogTrip` alert through the existing `AlertsManager`/`AlertRouter`/`WebhookAlertSink` stack in
addition to its existing log line, with the webhook path operator-enabled via new
`docker-compose.yml` env vars (default-disabled, so out-of-the-box behavior stays effectively
log-only until an operator opts in — documented honestly, not overclaimed).
`docs/architecture/simulation_watchdog.md` and `docs/engine/contracts/api_protocol_contract.md`
were corrected to match the real implementation, and parity ledger entry `INFRA-358` was added.
All new/changed-file-adjacent tests pass; the one pre-existing regression-risk test
(`tests/api/test_rest_parity.py`) could not run in this sandbox due to an unrelated, pre-existing
environment issue (confirmed via `git stash`), and its asserted healthy-path behavior was
independently verified correct by directly running the real server.
