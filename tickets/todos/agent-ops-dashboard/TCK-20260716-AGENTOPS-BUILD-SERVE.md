---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-BUILD-SERVE
phase: open
date: 2026-07-16
tags: []
---

# TCK-20260716-AGENTOPS-BUILD-SERVE

## Title
Build/serve tooling and deployment shape for the agent ops dashboard

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The author wants the dashboard packaged as a pre-built static React/Vite SPA served by a single Python process, with Node only involved at build time. This means new Makefile targets (dashboard-install/dashboard-build/dashboard-dev/dashboard-serve) mirroring the existing install/build/dev/serve pattern without colliding, running as a plain foreground process on port 8420 rather than via Docker Compose.

## Scope
- Add new .PHONY Makefile targets dashboard-install, dashboard-build, dashboard-dev, dashboard-serve mirroring the existing install/build/dev/serve naming pattern without redefining or shadowing existing targets
- Implement dashboard-build to run vite build producing a static asset directory
- Implement dashboard-serve as a single foreground Python process mounting the pre-built static SPA via FastAPI StaticFiles, listening on port 8420 by default, configurable via --port
- Restrict Node/npm invocation to dashboard-install/dashboard-build/dashboard-dev only; dashboard-serve never invokes Node at runtime

## Out of Scope
- The TicketsView, RecentActivityGantt, and ReplayTimelineView frontend components themselves (owned by AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE)
- The FastAPI backend routes/ingest logic being served (owned by AGENTOPS-DASHBOARD-BACKEND)
- Any Docker Compose service changes
- Adding frontend CI coverage

## Acceptance Criteria
- [ ] make dashboard-install, dashboard-build, dashboard-dev, dashboard-serve exist as new .PHONY Makefile targets and do not redefine or shadow the existing install/build/dev/serve targets
- [ ] make dashboard-serve starts a single foreground Python process mounting the pre-built static SPA via FastAPI StaticFiles, listening on port 8420 by default, configurable via a --port flag
- [ ] make dashboard-build runs vite build to produce a static asset directory that dashboard-serve mounts
- [ ] Node/npm is invoked only during dashboard-install/dashboard-build/dashboard-dev, never at dashboard-serve runtime
- [ ] Running make dashboard-serve alongside make serve (port 8000), make dev-frontend (port 5173), and make docs-serve (port 3000) succeeds with no port collision

## Related Tickets
- TCK-20260716-AGENTOPS-TICKETS-VIEW
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
- TCK-20260607-MON-DASHBOARD
- TCK-20260614-RESOURCE-DASHBOARD
- TCK-20260529-OBS-PHASE27-API-DASHBOARD
- TCK-20260623-TYPE-CHECKER

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md

## Related Stored Artifacts
None.

## Related Code Areas
- Makefile
- docker-compose.yml
- frontend/package.json
- src/cli/entry.py
- experiments/agent_ops_dashboard/PROPOSAL.md
- expected: src/api/agent_ops_dashboard/main.py

## Assumptions / Open Questions
- No existing FastAPI route in this codebase currently serves a built SPA as static files (a direct grep for StaticFiles/.mount( across src/ found zero matches); the StaticFiles-mount serving mechanism is new implementation, not a copy of proven code, despite the Makefile target-naming precedent being real and mirrorable
- Frontend has zero CI coverage today; this is an inherited gap not fixed by this ticket
- This ticket has no independent value until AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE, and AGENTOPS-DASHBOARD-BACKEND's outputs exist to package

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
