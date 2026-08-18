---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
phase: open
date: 2026-08-17
tags: [observability, engine]
---

# TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

## Title
Make /health reflect real engine liveness; fix watchdog doc/implementation mismatch

## Status
OPEN

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
- [ ] `/health` returns a status that actually changes when the engine thread is killed/hung in a
      test scenario.
- [ ] The watchdog doc's status and file-path claims match the real, running implementation.
- [ ] At least one critical-escalation path reaches somewhere outside a log line, or the doc
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
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
