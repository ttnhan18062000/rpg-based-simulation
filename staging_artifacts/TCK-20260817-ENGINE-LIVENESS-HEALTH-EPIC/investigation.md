---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
artifact_type: investigation
tags: [observability]
---

# Investigation — TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC

No fresh investigation performed for this scope-only epic — findings are sourced directly from
`docs/audits/D23_architecture_resilience.md` (§D, §K, R2), evidence-cited with file:line
references (`src/api/server.py:126-128`, `src/observability/watchdog.py:106-108`,
`docs/architecture/simulation_watchdog.md`). Full detail is consolidated in
`docs/plans/engine_liveness_health_epic.md`.

A real codebase investigation (confirming current `/health` implementation and watchdog wiring)
is deferred to when this epic is formally scoped via `create-tickets`.

No duplicate or conflicting ticket was found for this scope.
