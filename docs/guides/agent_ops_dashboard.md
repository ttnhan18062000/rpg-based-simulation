---
status: active
layer: observability
authority: P1
audience: developer
tags: [documentation, observability, api-design]
---

# Agent Ops Dashboard

A read-only visual viewer over `tickets/` and `agent-monitoring/*.jsonl` — recent
run activity, per-run replay, a filterable ticket table, and a statistics
board. It is purely presentational: it never mutates `tickets/`,
`agent-monitoring/`, or any `AuthoritativeState`, and it is not itself a
source of truth for anything it displays. Written as of
TCK-20260717-AGENTOPS-DASHBOARD-DOCS and updated by
TCK-20260718-STATS-DOCS-UPDATE for the Stats tab — commands, ports, and
behavior below reflect the shipped state at that point; re-check against
source if the underlying code has changed since.

## What it is

A series of tickets have built this feature incrementally: a standalone FastAPI
backend over the ticket corpus and agent-monitoring logs, a React/Vite
single-page app with four views, build/serve tooling to package both into one
process, and a statistics board layered on top of the first two. See
`docs/observability/agent_ops_dashboard_contract.md` for the technical
reference (API contract, cache/ingest design, frontend structure, hard
constraints).

## Build / run / serve

| Command | What it does | Port(s) |
|---|---|---|
| `make dashboard-install` | `cd dashboard-frontend && npm install` | — |
| `make dashboard-build` | `cd dashboard-frontend && npm run build` | — |
| `make dashboard-dev` | Backend (`uvicorn src.api.agent_ops_dashboard.main:app --reload`) and the Vite dev server, concurrently | Backend `8471`, Vite dev server `5174` |
| `make dashboard-serve` | Depends on `dashboard-build`; single foreground process serving API + built SPA together | `8420` |

For disambiguation only (this guide does not cover these): the main
simulation API's own `make serve` runs on `8000`, and Docusaurus's
`make docs-serve` runs on `3000`. The main game-UI app's unrelated `make dev`
frontend runs on `5173` — not to be confused with the dashboard's own Vite dev
port, `5174`.

## Using the four views

The header nav switches between four views; there is no URL router, so
navigation state is local to the page session.

### Recent Activity Gantt

The default landing view. Shows recent runs as horizontal bars over a rolling
time window. Solid, color-coded bars represent authoritative `runs.jsonl`
rows (green = `DONE`, red = any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`
status, gray = anything else). A visually distinct hatched fill marks
inferred-live runs — ones with recent `tools.jsonl` activity but no
`runs.jsonl` row yet, i.e. still in progress. When an inferred-live run
completes, its bar transitions to the solid authoritative style rather than
cutting over instantly. Clicking a row navigates to the Replay Timeline view
for that run.

A fixed time axis (7 evenly-spaced ticks with local-time labels) renders
above the scrollable row list, positioned via the same time-to-position
mapping the bars themselves use, so axis ticks and bar edges never visually
diverge. Each bar also carries an on-chart run-id label distinct from the
hover tooltip, so identifying a run no longer requires hovering it.

### Replay Timeline

A scrubbable phase/tool-call playback for one run, plus a files-touched
panel. Selecting a run (via Gantt row click, or directly) fetches its full
timeline once; the playback scrubber itself never re-fetches — it only moves
through the already-loaded entries. For a run still in progress, any
tool-call activity beyond the last known phase is shown with the caption
"(phase unknown — run still in progress)" rather than a guessed phase or
agent name — see Known Limitation below.

### Tickets view

A filterable, sortable table over the ticket corpus, fetched one bounded
page (up to 100 rows) at a time rather than the whole corpus at once.
Filters are single-select per dimension for tier/layer/status/priority, and
multi-select for tags — this matches the backend's actual query-parameter
shape (each of the first four accepts one value; only `tag` is repeatable).
Filtering across dimensions is AND (a ticket must match every active
filter); filtering within the tag selection is OR (a ticket matches if it
has any selected tag). The Tier/Layer/Status/Priority dropdowns always list
their full canonical sets (Tier: `hotfix`/`standard`/`epic`; Layer: every
value registered in `docs/guidelines/layer_registry.jsonl`; Status: `OPEN`/
`INPROGRESS`/`BLOCKED`/`DONE`/`EPIC_SCOPED`; Priority: `P0`-`P3`) regardless
of whether any ticket currently holds a given value — so e.g. `BLOCKED`
stays selectable (returning zero rows) instead of disappearing whenever no
ticket happens to be blocked right now, and selecting one filter never
narrows what another dropdown can offer. Only the tag list is genuinely
corpus-derived (open-vocabulary, not a small closed enum), sourced from a
server-computed summary of the full filtered corpus so it never narrows to
just the current page either. The tag list itself is capped at 40
always-visible options with a search box to narrow further, instead of
dumping every tag in the corpus as an unbroken wall of buttons. Clicking
the date column header re-sorts via the backend (the only server-side sort
dimension); clicking any other column header (tier, layer, status,
priority, tag) re-orders the current page's rows client-side — the backend
does not support server-side sorting on those dimensions. Each row links
to its matching run(s) in Replay Timeline.

### Stats

A fetch-once-per-view-load statistics board over two backend endpoints,
`GET /api/stats/agent-monitoring` and `GET /api/stats/tickets` (see
`docs/observability/agent_ops_dashboard_contract.md` for both routes' shapes).
Unlike the other three views, it does not poll or re-fetch on an interval —
switching away and back to the tab re-fetches once, on mount.

Two sections, stacked in one scrollable page rather than further nav tabs
(both domains are meant to be read together for a status check):

- **Agent Monitoring** — stat tiles (total runs, done, gate fails, average
  duration, total agent calls), a top-10 magnitude bar chart each for gate
  failure and reason-code breakdowns, a 2-series grouped bar chart for tier
  distribution (count vs. done), summary-quality stat tiles, a top-15 table of
  agents by call volume (with per-status counts), and a table of slow runs.
- **Ticket Corpus** — stat tiles (scanned files, included tickets, skipped,
  artifact-completeness percentage), a 14-day velocity bar chart, and four
  distribution bar charts (tier/type/priority/layer). This is the same data
  `tools/ticket_stats_report.py` (`make ticket-stats-report`) produces on the
  command line — see
  [`docs/guides/ticket_reporting.md`](ticket_reporting.md)'s "Pillar 2" section
  — the CLI and this view read from the exact same computation functions, so
  their numbers always match for the same corpus state.

Chart marks are plain HTML/CSS (no charting library dependency), following
the same convention the Recent Activity Gantt bars already use. Colors were
validated against this app's actual dark chart surface using the project's
`dataviz` skill rather than reusing the app's pre-existing `--color-accent-*`
tokens, which failed that validation for chart-mark use (they remain in use
elsewhere for plain inline status text, a different role). The dashboard has
no live light theme today (no `.dark` class is ever applied, no theme
toggle exists anywhere in the app) — chart colors are still read from named
constants rather than hardcoded inline, so a future app-wide theme toggle
would only need those constants' values swapped, not a chart rewrite.

## Hover tooltips

Enum-like labels across the dashboard show a description on hover — a dotted
underline marks a label as hoverable. Descriptions are fetched once per app
load from `GET /api/glossary` (backed by `docs/guidelines/glossary_registry.jsonl`
and, for Layer, `docs/guidelines/layer_registry.jsonl`'s existing per-layer
note) and rendered as-is; nothing is hardcoded in the frontend. Covered today:

- **Tickets view** — Tier, Layer, ticket status, and Priority cells.
- **Replay Timeline** — event status.
- **Stats** — gate-failure/reason-code/tier/type/priority/layer bar labels,
  and the Slow Runs table's status cell.

Not covered, deliberately: the Recent Activity Gantt bars and their legend.
A Gantt bar's only visible text is the run ID, and its color reflects a
3-way bucket (done / failed / neutral) that groups many distinct statuses
together rather than a single enum value — there is no one glossary term a
tooltip there could point to.

## Responsive Behavior

At viewport widths at or below the `sm:` Tailwind breakpoint (~480px), the
header's title and nav wrap onto a second line instead of crowding each
other, and the header's height is no longer fixed so the wrapped line has
room to render (the fixed height returns at `sm:` and above). Separately,
the Recent Activity Gantt view's hover tooltip is bounded to a max width and
wraps its text rather than overflowing past the right edge of the viewport.

## Known limitation

Live (in-progress) tool-call rows have no `phase` or `agent` label — the
underlying data type has no such fields at all for live entries, not merely
empty ones. The Replay Timeline view renders the honest
"phase unknown — run still in progress" caption for these rows unconditionally.
This is a known, tracked gap (`MONITORING_INSTRUMENTATION_GAP`), not something
this dashboard works around or guesses at.

## See also

- `docs/observability/agent_ops_dashboard_contract.md` — technical reference:
  API contract, cache/ingest design, frontend SPA structure, hard design
  constraints.
- `docs/parity_ledger/infrastructure.yaml` — see INFRA-275 (backend, including
  the two Stats-tab endpoints) and INFRA-276 (build/serve tooling) for the
  verified evidence trail.
- [`docs/guides/ticket_reporting.md`](ticket_reporting.md) — the CLI-side
  counterpart to the Stats tab's Ticket Corpus section ("Pillar 2").
