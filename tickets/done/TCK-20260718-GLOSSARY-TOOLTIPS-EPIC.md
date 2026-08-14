---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-GLOSSARY-TOOLTIPS-EPIC
phase: done
date: 2026-07-18
tags: [dashboard, observability, reporting, agent-monitoring]
---

# TCK-20260718-GLOSSARY-TOOLTIPS-EPIC

## Title
Epic: Backend-owned glossary registry + hover tooltips across the Agent Ops Dashboard

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Direct user follow-up request during review of `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC`: add
hover tooltips on enum-like labels (ticket status, run/gate status, reason codes, "everything you
think it needs") across the whole dashboard, explicitly requiring the descriptions be
backend-owned metadata — "in the best scenario, this should be stored as metadata somewhere in
the backend, not the UI-layer data, UI only load it" — not hardcoded frontend strings. User
confirmed via a direct question: broad first pass across the whole app, not scoped to the Stats
tab alone. Full investigation and scope reasoning already captured in
`docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md`.

## Scope
- A new backend-owned glossary registry (`docs/guidelines/glossary_registry.jsonl` +
  `tools/glossary_registry.py`), mirroring the `tag_registry.py`/`layer_registry.py` pattern
  established earlier today.
- A new dashboard API endpoint exposing the glossary as typed JSON.
- Frontend tooltip wiring across the Tickets, Stats, and Replay views using the existing Radix
  Tooltip primitive, sourcing all description text from the fetched glossary — never hardcoded.
- Documentation of the new endpoint/mechanism.

## Out of Scope
- Any change to the underlying meaning/behavior of ticket status, run status, reason codes, tier,
  or priority.
- Editable/user-authorable descriptions from the dashboard UI itself.
- Any change to `LAYER_VALUES`/`WORKFLOW_STATUS_VALUES`/`TIER_VALUES`/`PRIORITY_VALUES`'s actual
  membership.

## Acceptance Criteria
- [x] All child tickets closed DONE.
- [x] Glossary registry seeded with real, accurate descriptions for every ticket-status/tier/
      priority/type value plus the run/gate-status and reason-code/event-status values actually
      emitted by this repo's tooling (54 total terms: 35 glossary + 19 layers).
- [x] `GET /api/glossary`-shaped endpoint returns the registry as a typed Pydantic model, verified
      live.
- [x] At least the Tickets, Stats, and Replay views render real backend-sourced tooltip text on
      hover, verified live via headless browser, zero console errors.
- [x] No description text hardcoded as a literal string in `dashboard-frontend/src/*.tsx` —
      enforced by an anti-drift source-string test guard.

## Related Tickets
Child tickets to be added below as each is created.
- TCK-20260718-GLOSSARY-REGISTRY
- TCK-20260718-GLOSSARY-API
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
- TCK-20260718-GLOSSARY-DOCS-UPDATE

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md
- docs/agent-monitoring/schema.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-GLOSSARY-REGISTRY/
- stored_artifacts/TCK-20260718-GLOSSARY-API/
- stored_artifacts/TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND/
- stored_artifacts/TCK-20260718-GLOSSARY-DOCS-UPDATE/

## Related Code Areas
- tools/tag_registry.py
- tools/layer_registry.py
- src/api/agent_ops_dashboard/
- dashboard-frontend/src/

## Assumptions / Open Questions
None — user's two scope decisions (backend-owned metadata; broad first pass) were confirmed
directly before this epic was scoped.

## Implementation Notes
Scoped from a direct user follow-up request during the stats-board epic's review. Proposal at
`docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md` contains the full background
investigation (no existing glossary infra found; registry pattern from `tag_registry.py`/
`layer_registry.py` is the direct template; known label domains compiled from the dashboard's
actual rendered views).

Executed directly (Read/Edit/Bash/Write) rather than via the standard multi-agent
Scope→Investigate→Plan→Review→Implement→Architecture-Verify→Test→Parity→Verify→Finalize
pipeline — this execution context (a forked worker) has no Agent-tool subagent access. All the
same work products (investigation.md/plan.md/test_plan.md per child ticket, code/test changes,
verification steps) were produced directly instead. Flagging this deviation explicitly per this
project's traceability rule.

## Test Summary
Backend: `python3 -m pytest tests/tools/test_glossary_registry.py
tests/tools/test_agent_ops_dashboard_glossary.py
tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_stats.py
tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py
tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` — 84/84 passing. Frontend:
`cd dashboard-frontend && npm run test -- --run` — 11 files / 82 tests passing; `tsc -b --noEmit`
clean; `npm run build` clean. Live verification via headless Chromium against a freshly rebuilt
`make dashboard-serve`: 5 distinct label types across Tickets and Stats views showed real
backend-sourced description text on hover, zero console errors.

## Files Changed
Backend: `tools/glossary_registry.py` (new), `docs/guidelines/glossary_registry.jsonl` (new),
`src/api/agent_ops_dashboard/{models,ingest,main}.py`,
`tests/tools/test_glossary_registry.py` (new), `tests/tools/test_agent_ops_dashboard_glossary.py`
(new), `tests/tools/test_agent_ops_dashboard_api_boundary.py`. Frontend:
`dashboard-frontend/src/api.ts`, `dashboard-frontend/src/components/GlossaryTooltip.tsx` (new),
`dashboard-frontend/src/components/{BarChart,GroupedBarChart}.tsx`,
`dashboard-frontend/src/views/{TicketsView,ReplayTimelineView,StatsView}.tsx`,
`dashboard-frontend/src/test/{GlossaryTooltip,BarChart,StatsView}.test.tsx`. Docs:
`docs/observability/agent_ops_dashboard_contract.md`, `docs/guides/agent_ops_dashboard.md`,
`docs/parity_ledger/infrastructure.yaml` (`INFRA-279`, `INFRA-280`).

## Completion Summary
All 4 child tickets closed DONE. Backend-owned glossary registry (54 terms: 35 seeded +
19 layer descriptions merged at read time) is live via `GET /api/glossary`. Hover tooltips wired
across Tickets, Replay, and Stats views, sourcing all description text from that endpoint — zero
hardcoded strings in the frontend, enforced by an anti-drift test guard. Gantt/Legend deliberately
excluded (no 1:1 enum-to-term mapping exists there) and that decision is documented, not silent.
Live-verified via headless Chromium with zero console errors. Docs and parity ledger fully
updated. Delivers the user's direct request end to end.
