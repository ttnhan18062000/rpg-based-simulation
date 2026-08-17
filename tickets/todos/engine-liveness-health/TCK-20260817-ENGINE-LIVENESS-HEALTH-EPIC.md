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
EPIC_SCOPED

## Tier
epic

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
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/engine_liveness_health_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (real `/health` liveness check; watchdog doc correction; at least one real external alert
  channel), producing investigated child tickets in `tickets/todos/engine-liveness-health/`.

## Out of Scope
- Container-level auto-restart-on-engine-crash orchestration (a larger deployment decision).
- A full external alerting integration beyond "at least one real channel wired."

## Acceptance Criteria
- [ ] `docs/plans/engine_liveness_health_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

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
- Which external alert channel (webhook, email, etc.) to wire is an open decision for whoever
  scopes the child ticket.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
