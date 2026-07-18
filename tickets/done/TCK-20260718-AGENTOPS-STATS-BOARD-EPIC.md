---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-AGENTOPS-STATS-BOARD-EPIC
phase: done
date: 2026-07-18
tags: [dashboard, observability, reporting, agent-monitoring]
---

# TCK-20260718-AGENTOPS-STATS-BOARD-EPIC

## Title
Epic: Agent Ops Dashboard Stats board — a 4th tab covering agent-monitoring and ticket-corpus statistics

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Direct user request: "a board to view statistical agent monitoring and tickets system." Investigation (search_docs + direct reads, per Context Scan rule) found this gap was already anticipated and deliberately deferred: `docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md` (the dashboard's own origin idea doc) explicitly notes `docs/guides/ticket_reporting.md`'s "pillars" framing lists ticket velocity/throughput and tier/type/priority distribution as not built — the current 3-view dashboard (Gantt/Tickets/Replay) is row-level browsing, not aggregate statistics. Separately, `tools/agent-monitoring/generate_retro.py` already computes a rich set of agent-monitoring aggregate stats (run/gate-failure rates, tier distribution, tag breakdown, duration/agent-count averages, slow-run detection) but only renders them to Markdown — nothing exposes this as structured data any interactive tool can consume.

User confirmed two scope decisions directly: (1) this is a new 4th tab in the existing Agent Ops Dashboard, not a separate tool; (2) v1 covers both agent-monitoring statistics AND ticket-corpus statistics together, not staged sequentially.

Full investigation, architectural constraints, and candidate child-ticket concerns are written up in `docs/plans/agent_ops_dashboard/proposal_stats_board.md` — read that in full before scoping child tickets; do not re-derive.

## Scope
- Refactor `tools/agent-monitoring/generate_retro.py`'s metric computation into a reusable, typed form (not Markdown-only), keeping its existing CLI output byte-identical.
- New backend endpoint(s) in `src/api/agent_ops_dashboard/` exposing agent-monitoring statistics, consuming the refactored computation, as typed Pydantic models.
- New `tools/*_report.py` script (following `tools/tag_report.py`'s established convention) covering the four named-but-unbuilt ticket-corpus reporting pillars: velocity/throughput, tier/type/priority distribution, layer distribution, artifact completeness — plus a backend endpoint exposing it.
- New "Stats" tab in `dashboard-frontend/` rendering charts/stat tiles from both endpoints — must load the `dataviz` skill before any chart code per the proposal's architectural constraints.
- Doc updates: `docs/guides/agent_ops_dashboard.md`, `docs/observability/agent_ops_dashboard_contract.md`, and `docs/guides/ticket_reporting.md`'s "not built" section once the pillars land.

## Out of Scope
- Any change to `generate_retro.py`'s existing Markdown CLI output format.
- New agent-monitoring instrumentation or schema changes — aggregates existing data only.
- Real-time/live-updating stats (polling is an Investigate decision, not assumed).
- Adding frontend CI (out of scope per the dashboard's own origin idea doc, which already deferred this).

## Acceptance Criteria
- [x] Agent-monitoring statistics are available via a new dashboard API endpoint, backed by the same computation `generate_retro.py` uses (not a duplicate).
- [x] `generate_retro.py`'s existing CLI/Markdown output is proven byte-identical before and after the refactor.
- [x] A new ticket-corpus report tool covers velocity/throughput, tier/type/priority distribution, layer distribution, and artifact completeness, following `tag_report.py`'s established pattern (dedicated test file, `make` target).
- [x] The dashboard frontend has a 4th "Stats" tab rendering both statistic domains, built using the `dataviz` skill's design guidance.
- [x] All new endpoints return typed Pydantic models only, per the dashboard's existing API-boundary rule.
- [x] Relevant docs updated to describe the new tab/endpoints.

## Related Tickets
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20260718-AGENTOPS-STATS-API
- TCK-20260718-TICKET-CORPUS-REPORT
- TCK-20260718-STATS-TAB-FRONTEND
- TCK-20260718-STATS-DOCS-UPDATE

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_stats_board.md
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- docs/guides/ticket_reporting.md
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-AGENTOPS-STATS-BOARD-EPIC (epic-level breakdown/sequencing rollup)
- Each child ticket carries its own: stored_artifacts/TCK-20260718-RETRO-STATS-REFACTOR,
  TCK-20260718-AGENTOPS-STATS-API, TCK-20260718-TICKET-CORPUS-REPORT,
  TCK-20260718-STATS-TAB-FRONTEND

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/tag_report.py
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/main.py
- src/api/agent_ops_dashboard/models.py
- dashboard-frontend/src/App.tsx
- dashboard-frontend/src/views/

## Assumptions / Open Questions
- Whether agent-monitoring stats live in `ingest.py` or a new sibling module (`stats.py`) is an Investigate decision, not dictated here.
- Whether the frontend Stats view is one unified section or two sub-sections (agent-monitoring vs ticket-corpus) is a UX call for the frontend child ticket to make and document.
- Chart library choice (none exists in `dashboard-frontend/package.json` today) is an implementation decision guided by the `dataviz` skill, not fixed here.

## Implementation Notes
Scoped from a direct user request following today's canonical-field-enums epic and dashboard-filter-fix work earlier in this session. Fresh-scanned tickets/ for overlap with three prior "dashboard"-named tickets the proposal doc's own investigation had already found (TCK-20260529-OBS-PHASE27-API-DASHBOARD, TCK-20260614-RESOURCE-DASHBOARD, TCK-20260607-MON-DASHBOARD) — confirmed via direct re-read of each: Phase 27 is simulation-runtime observability storage/API, RESOURCE-DASHBOARD is a runtime resource CLI (memory/queue/pressure), MON-DASHBOARD is static Docusaurus integration of retro Markdown reports. None overlap this epic's actual scope (an interactive, chart-based stats tab over ticket-corpus + agent-monitoring aggregate data).

Executed by a worker fork with no Agent-tool subagent access in this context — ticket-scoper role performed directly via Read/Write/Bash, not delegated. Flagging this deviation explicitly per this project's traceability rule.

## Test Summary
All 5 child tickets closed with their own independent test evidence (see each ticket's own Test
Summary / `stored_artifacts/{id}/`). Aggregate: `generate_retro.py`'s CLI output proven
byte-identical pre/post-refactor (git-stash comparison, re-verified independently by the
coordinating session); backend `npm`/`pytest` suites green throughout (final counts: 87 backend
tests, 71 frontend tests passing); live-verified end to end via a freshly-rebuilt `make
dashboard-serve` plus a headless-Chromium run against the actual Stats tab (real numbers matched
direct `curl` output exactly, zero console errors).

## Files Changed
See each child ticket's own Files Changed section. Summary: `tools/agent-monitoring/generate_retro.py`
(refactored), `src/api/agent_ops_dashboard/{main,ingest,models}.py` (2 new routes/12 new models),
`tools/ticket_stats_report.py` (new), `dashboard-frontend/src/{App.tsx,api.ts,views/StatsView.tsx,
components/{BarChart,GroupedBarChart,StatTile}.tsx,lib/chartPalette.ts}` (new 4th tab, no new npm
dependency), `docs/{guides/agent_ops_dashboard.md,observability/agent_ops_dashboard_contract.md,
guides/ticket_reporting.md}` (updated), `docs/parity_ledger/infrastructure.yaml` (INFRA-275
extended across all 4 child tickets).

## Completion Summary
Delivered the user's direct request — "a board to view statistical agent monitoring and tickets
system" — as a 4th "Stats" tab in the existing Agent Ops Dashboard, backed by two new typed API
endpoints. `generate_retro.py`'s computation was extracted into a reusable function
(`compute_retro_metrics`) shared by both its own CLI and the new API, proven byte-identical.
`tools/ticket_stats_report.py` closes all four previously-named-but-unbuilt "ticket_reporting.md"
pillars (velocity, tier/type/priority distribution, layer distribution, artifact completeness). The
frontend Stats tab uses no new charting dependency — plain HTML/CSS bars matching the existing
Gantt-bar convention, with colors validated via the `dataviz` skill against the app's real dark
surface (the app's own pre-existing accent tokens failed that validation and were not reused for
chart marks). All 5 child tickets closed DONE; docs and the parity ledger updated to match the
final landed state.
