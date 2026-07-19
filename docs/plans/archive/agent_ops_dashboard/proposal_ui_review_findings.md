---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-17
archived: 2026-07-19
tags: [idea, agent-infrastructure, observability, dashboard]
---

# Proposal: Agent Ops Dashboard UI issues found via live walkthrough

**Archived:** 2026-07-19 — all six findings shipped: `TCK-20260717-GANTT-TIME-AXIS` (#1, time axis +
on-chart labels), `TCK-20260717-TICKETS-TAG-SEARCH` (#2, searchable collapsed tag multi-select),
`TCK-20260717-CSS-LAYER-PADDING-FIX` (#3, Tier/Layer column concatenation — root cause was an
unlayered CSS reset silently zeroing Tailwind padding utilities app-wide, not a markup bug),
`TCK-20260717-TICKET-TITLE-PARSE-FIX` (#4, Ticket/Title duplication — backend ingest was returning
`ticket_id` as the title for every row), `TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT` (#5, responsive
header + Gantt tooltip), `TCK-20260717-TICKETS-TABLE-PAGINATION` (#6, table pagination). All in
`tickets/done/`. This document is the historical record of the findings as originally reproduced.

**Maturity: SHIPPED** — found by driving the shipped dashboard
(`make dashboard-serve`) with a headless browser across all three views
(Recent Activity Gantt, Tickets, Replay Timeline), immediately after
TCK-20260717-AGENTOPS-DASHBOARD-DOCS documented it. Not a design critique —
every item below was reproduced and screenshotted against the running app.

Frontend: `dashboard-frontend/`. Backend: `src/api/agent_ops_dashboard/`.
Reference docs: `docs/guides/agent_ops_dashboard.md`,
`docs/observability/agent_ops_dashboard_contract.md`.

## 1. Recent Activity Gantt has no time axis or on-chart labels

Bars are colored rectangles with zero text on them. The legend says what
the colors mean, but nothing on the chart says which run a given bar is,
or when it happened. Hovering a bar does show a tooltip with the ticket
ID, tier, workflow, duration, and agent count — that part works — but
there is no time/date axis anywhere on the chart, so a user can't tell
when in the rolling window any bar falls without hovering every single
one individually. For a Gantt-style view this is a significant legibility
gap.

## 2. Tickets view tag filter dumps the entire tag registry as unstyled buttons

The tag filter renders every tag in `docs/guidelines/tag_registry.jsonl`
(~1,262 entries) as individual flat pill buttons
(`data-testid="filter-tag-*"`) in one unbroken wrapped block, with no
search box, grouping, or collapse. This pushes the actual ticket table
far below the fold and bloats the page to a >1.2MB DOM on initial load.
The Tier/Layer/Status/Priority filters are proper `<select>` dropdowns
and work fine — only the tag filter has this problem. Needs a
searchable/collapsible multi-select instead of a flat button dump for
every registered tag.

## 3. Ticket table: Tier and Layer columns render with no visible separation

In the ticket table, adjacent "Tier" and "Layer" column values run
together with no space or visible cell boundary — e.g. "standard" +
"engine" renders as "standardengine", "standard" + "misc" as
"standardmisc", "standard" + "world" as "standardworld". Reproduced
consistently across many rows. Looks like missing cell padding/spacing
in the table markup rather than a data problem (the values are correct,
just visually concatenated).

## 4. Ticket table: Ticket and Title columns are fully duplicate

Every row's "Ticket" column and "Title" column show the exact same
string (the ticket ID itself, e.g.
`TCK-20260612-WORLDBUILDING-CONTRACT` in both). This wastes roughly a
third of the table's horizontal width and suggests the frontend isn't
pulling a distinct human-readable title from the ticket data (or the
backend isn't returning one).

## 5. No responsive/narrow-viewport layout

At a 480px viewport width: the header nav ("Recent Activity Tickets
Replay") crowds directly against the "Agent Ops Dashboard" title with no
wrapping or spacing, the Gantt tooltip box overflows/clips past the
right edge of the viewport instead of repositioning, and the Tickets
view's tag-button wall (see #2) completely dominates the screen before
the table becomes reachable at all. There appears to be no responsive
design consideration anywhere in the current layout.

## 6. Ticket table renders all ~1,109 rows unpaginated

The Tickets view fetches and renders the full ticket corpus (1,109 rows
observed) as one unvirtualized `<table>` with no pagination. Works today
but is a scalability risk as the corpus keeps growing — lower priority
than the other items, worth tracking separately.

## Out of scope for this proposal

The "phase unknown — run still in progress" caption on live-run rows in
Replay Timeline is a known, already-tracked gap
(`MONITORING_INSTRUMENTATION_GAP`, documented in
`docs/guides/agent_ops_dashboard.md`) — do not re-ticket it here.
