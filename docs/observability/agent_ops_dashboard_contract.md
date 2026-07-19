---
status: active
layer: observability
authority: P1
audience: agent
tags: [documentation, observability, api-design]
---

# Agent Ops Dashboard Contract

## Purpose

The Agent Ops Dashboard backend (`src/api/agent_ops_dashboard/main.py`) is a
standalone FastAPI app — not mounted on `src/api/server.py`, the main
simulation API — exposing read-only, typed projections over `tickets/**` and
`agent-monitoring/{runs,events,tools}.jsonl` for the dashboard SPA. It never
touches `AuthoritativeState` or the tick loop; it is a separate product on a
separate port. Content here reflects the shipped state as of
TCK-20260717-AGENTOPS-DASHBOARD-DOCS, updated by TCK-20260718-STATS-DOCS-UPDATE
for the two Stats-tab endpoints and by TCK-20260718-GLOSSARY-DOCS-UPDATE for
the glossary endpoint and hover tooltips — re-verify against source before
relying on exact behavior after further code changes.

## Contract

### Backend routes (`main.py`)

| Route | Returns | Params | Backing |
|---|---|---|---|
| `GET /api/tickets` | `TicketsPage` (`items`/`total_count`/`facets`) | `tier`, `layer`, `status`, `priority` (single-value); `tag` (repeatable); `lifecycle`, `q`, `sort` (default `date_desc`); `limit` (1-500, default 100), `offset` (default 0) | `DashboardCache.get_tickets` |
| `GET /api/runs` | `List[RunSummary]` | `limit` (1-100, default 50), `offset`, `status`, `workflow`, `since` (ISO string, compared lexically, never parsed to `datetime`) | `DashboardCache.get_runs` |
| `GET /api/runs/{run_id}` | `RunDetail`, 404 on miss | — | `DashboardCache.get_run` |
| `GET /api/runs/{run_id}/timeline` | `RunTimeline`, 404 on miss | — | `DashboardCache.get_timeline` |
| `GET /api/stats/agent-monitoring` | `AgentMonitoringStats` | `days` (int, optional), `all` (bool, default `false`, query alias `all`), `week` (ISO-week string, optional) — mirrors `generate_retro.py`'s own CLI period-selection flags; priority order `all` > `days` > `week` (defaults to the current ISO week if none are set), no combination validation at the route | `DashboardCache.get_agent_monitoring_stats` |
| `GET /api/stats/tickets` | `TicketCorpusStats` | — (whole `tickets/done/` corpus, no time window) | `DashboardCache.get_ticket_corpus_stats` |
| `GET /api/glossary` | `GlossaryResponse` | — | `DashboardCache.get_glossary` |
| `GET /api/health` | `HealthStatus` | — | `DashboardCache.get_health` |

Every route declares `response_model=`; no raw dict or domain payload is ever
returned (`models.py`'s Pydantic models are the only shapes crossing the route
boundary).

### Response models (`models.py`)

`RunMatchSummary`, `TicketSummary` (`status` = frontmatter doc-lifecycle
field, always present; `workflow_status` = the ticket body's `## Status`
section, nullable — two distinct fields, never conflated), `RawToolCall`
(no `phase`/`agent` field at all — absent from the type, not merely
nullable), `FileTouch`, `TimelineEntry` (has its own `phase`/`agent` fields,
both nullable — distinct from `RawToolCall`), `RunSummary`, `RunDetail`
(extends `RunSummary` with `ticket_title`, `ticket_lifecycle_state`),
`RunTimeline`, `HealthStatus` (`status` field is hardcoded `"ok"`, never
derived from `unparsed_lines` counts). `TicketFacets` (distinct
`tiers`/`layers`/`statuses`/`priorities`/`tags` across the filtered-but-
unpaginated result) and `TicketsPage` (`items: list[TicketSummary]`,
`total_count: int`, `facets: TicketFacets`) — both real Pydantic models,
never a raw dict at the route boundary.

`AgentMonitoringStats` (`run_summary: RunSummaryStats`,
`gate_failure_breakdown`/`reason_code_breakdown: Dict[str, int]`,
`tag_breakdown_subsystem: Dict[str, SubsystemTagStats]`,
`tag_breakdown_skill: Dict[str, SkillTagStats]`,
`tier_distribution: Dict[str, TierDistributionStats]`,
`agent_status_distribution: Dict[str, Dict[str, int]]`,
`phase_status_distribution: Dict[str, Dict[str, int]]`,
`spend_proxy_by_phase`/`spend_proxy_by_agent: Dict[str, SpendProxyStats]`,
`summary_quality: SummaryQualityStats`, `slow_runs: List[SlowRunEntry]`,
`outliers: OutlierStats`) is a field-for-field mirror of
`tools/agent-monitoring/generate_retro.py::compute_retro_metrics()`'s return
dict — the route computes nothing of its own, it only wraps that function's
output in typed models. A literal `None` key in `gate_failure_breakdown`
(from a `runs.jsonl` row with neither `final_status` nor `status` set) is
sanitized to the string `"unknown"` at this API boundary only —
`compute_retro_metrics()` itself is untouched, preserving its
byte-identical-CLI-output guarantee.

`phase_status_distribution` has the identical `{phase: {ok, failed, blocked,
skipped}}` shape as `agent_status_distribution` (open `Dict[str, int]` inner
type, not a fixed-field submodel — the status key set is whatever literal
strings appear in `events.jsonl`, not guaranteed to be exactly those four).
`OutlierStats` (`duration_s: List[DurationOutlierEntry]`,
`cost_proxy_score: List[CostProxyOutlierEntry]`) is a new submodel pair:
`DurationOutlierEntry` (`run_id`, `tier`, `duration_s`, `median`, `ratio`) and
`CostProxyOutlierEntry` (`run_id`, `seq: Optional[int]`, `phase`, `agent`,
`cost_proxy_score`, `median`, `ratio`) mirror
`compute_retro_metrics()`'s `outliers["duration_s"]`/`outliers["cost_proxy_score"]`
list-of-dicts exactly. `CostProxyOutlierEntry.seq` is nullable because
`generate_retro.py` builds it via `item.get("seq")` with no fallback — legacy
events without a `seq` produce a real `None`, same nullability class as
`gate_failure_breakdown`'s `None`-key sanitization above (though `seq` needs
no sanitization, since `None` is a valid JSON field value, just not a valid
JSON object key).

`TicketCorpusStats` (`scanned_files`, `included_tickets`,
`skipped: Dict[str, int]`, `velocity: VelocityStats`,
`distribution: TicketDistributionStats`,
`artifact_completeness: ArtifactCompletenessStats`) is a field-for-field
mirror of `tools/ticket_stats_report.py::build_json_report()`'s return dict —
same relationship as `AgentMonitoringStats` above, the route wraps rather than
recomputes.

`GlossaryEntry` (`term`, `category`, `description`) and `GlossaryResponse`
(`terms: Dict[str, GlossaryEntry]`) back `GET /api/glossary`, the tooltip
description source for the whole frontend. `DashboardCache.get_glossary`
merges three sources at read time, none of them copied into a second file:
every entry from `tools/glossary_registry.py`'s
`docs/guidelines/glossary_registry.jsonl`
(ticket-status/tier/priority/type/run-status/reason-code/event-status terms),
every layer from `tools/layer_registry.py`'s
`docs/guidelines/layer_registry.jsonl` (reusing that registry's existing
`note` field as the description under `category="layer"`), and every
`.claude/agents/*.md` role file (reusing each file's own frontmatter
`description:` field as the description under `category="agent"`, via the
module-level `_load_agent_role_descriptions()` helper — tolerant of a
missing `.claude/agents/` directory or a role file with no `description:`,
returning `{}`/skipping rather than raising, since one malformed role file
must never break the whole endpoint). Each merge step applies the same
`if term in terms: continue` first-registered-wins guard, protecting against
a future term-name collision across any of the three sources, though none
currently exists (35 glossary terms, 19 layer names, 13 agent names, all
verified disjoint — 67 total).

### Ingest / cache (`ingest.py`)

All file reads over `tickets/**` and `agent-monitoring/*.jsonl` live in this
module — `main.py` never reads a file directly. It reuses, rather than
reimplements:
- `tools/validate_frontmatter.py`'s `extract_frontmatter` for ticket
  frontmatter.
- `tools/generate_registry.py`'s `parse_body_section`/`_strip_frontmatter` for
  ticket body-section fields, including `title` (read from the `## Title`
  body section, not the H1 heading — the H1 is mandated to equal the
  ticket_id, so `parse_h1_title` would return the ticket_id, not a title).
- `tools/agent-monitoring/validate.py`'s tolerant `load_jsonl` (skips
  unparseable lines, continues) and its legacy status allowlists.

`DashboardCache` holds a single `threading.RLock` guarding every public
method (`get_tickets`, `get_runs`, `get_run`, `get_timeline`, `get_health`,
`get_agent_monitoring_stats`, `get_ticket_corpus_stats`, `get_glossary`), matching
`src/api/read_model_cache.py`'s `ReadModelCache` pattern — not the
swap-based build-outside-lock alternative. `_maybe_rebuild`/`_rebuild`
re-run the full parse+join+inference pipeline under that same lock whenever
any source `mtime` changes. `_rebuild` also retains `self._runs_all`/
`self._events_all` — the raw, ungrouped `runs.jsonl`/`events.jsonl` lists,
previously local-only to `_rebuild` — since `get_agent_monitoring_stats`
needs the same unfiltered/undeduplicated shape `generate_retro.py`'s own CLI
passes to `compute_retro_metrics()`, not `_runs_by_id`'s
deduplicated-by-`run_id` view (which would silently under-count retried
tickets).

`get_ticket_corpus_stats` is the **one** `DashboardCache` method that does not
read from the mtime-cached parse state at all — it performs its own fresh
`tickets/done/` file walk on every call (via
`tools/ticket_stats_report.py`'s imported functions), since that tool's
output shape (velocity/distribution/artifact-completeness) isn't a subset of
what `parse_ticket_file` already extracts and caches. This is a deliberate,
documented exception to the mtime-cache pattern every other method follows,
not an accidental divergence.

`get_glossary` follows the same independent-fresh-read exception, for the
same reason — its two source files (`glossary_registry.jsonl`,
`layer_registry.jsonl`) are small and append-only, not worth restructuring
`_rebuild()` for.

`build_matching_runs` returns **every** `runs.jsonl` row matching a
`ticket_id`, sorted `start_ts` descending (rows without a `start_ts` sort
last) — never collapsed to a single match, since a ticket can legitimately
have multiple runs (retries/re-runs).

`compute_inferred_active` implements the `ACTIVE_WINDOW_MINUTES = 10`
heuristic: a `run_id` present in `tools.jsonl` but absent from the
`runs.jsonl`-derived `runs_by_id` map, whose most recent tool-call timestamp
falls within the window, is `is_inferred_active=True`. This set is
recomputed fresh on every rebuild, never carried over from a prior snapshot,
so a run that completes falls out of it on the very next rebuild.

`get_tickets`'s filtering is AND across `tier`/`layer`/`status`
(= `workflow_status`)/`priority`, OR within the `tags` selection (set
intersection). Sorting is date-only (`date_asc`/`date_desc`) — there is no
server-side sort support for tier/layer/status/priority/tag; the shipped
`TicketsView.tsx` compensates with a client-side re-order for those columns,
which is inherently page-scoped once pagination applies (it sorts only the
currently-fetched page, not the full corpus).

`get_tickets` computes `total_count` and `facets` over the full filtered
result *before* slicing to `[offset:offset+limit]`, so filter-dropdown
options always reflect the whole corpus even when only one page of rows is
loaded. The `limit` param defaults to `None` at the cache-method level
(existing zero-arg call sites — the three AND/OR filter tests — still get
the full filtered set); the route layer (`main.py`) always passes a bounded
`limit` (1-500, default 100) through `Query(...)`.

As of TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL, `facets.tags` is the
**only** facet still derived from the filtered corpus — genuinely
open-vocabulary and multi-value, so "every value that could ever exist"
isn't a bounded list. The other four (`tiers`, `layers`, `statuses`,
`priorities`) are all fixed canonical lists, sourced from
`tools/ticket_field_values.py`'s `TIER_VALUES`/`LAYER_VALUES`/
`WORKFLOW_STATUS_VALUES`/`PRIORITY_VALUES` — independent of active filters,
pagination, and current corpus content. `layers` in particular is
registry-backed (`docs/guidelines/layer_registry.jsonl` via
`tools/layer_registry.py`, TCK-20260718-LAYER-REGISTRY-CONVERSION), not a
hardcoded literal. A value with zero matching tickets right now (e.g.
`BLOCKED` status, or a rarely-used `Tier`) is still a selectable filter
option rather than silently invisible — unlike `tags`, which only ever
shows a value that at least one matching ticket actually has.

### Frontend SPA structure (`dashboard-frontend/src/`)

- `App.tsx` — top-level view-switch state
  (`'activity' | 'tickets' | 'replay' | 'stats'`), no router library; owns
  `selectedRunId`, wired to each view's run-selection callback so a
  Gantt-row or Tickets-row click navigates to Replay.
- `api.ts` — TypeScript interfaces mirroring `models.py` field-for-field, plus
  typed fetch helpers (`fetchTickets`, `fetchRuns`, `fetchRunTimeline`,
  `fetchAllRunsSince`, `fetchAgentMonitoringStats`, `fetchTicketCorpusStats`,
  `fetchGlossary`) and `useRunsPolling`, a polling hook that offset-loops
  `fetchAllRunsSince` to guard against `GET /api/runs`'s per-page result cap.
  `useGlossary` is a separate fetch-once hook: a module-level
  `_glossaryPromise` singleton ensures exactly one `/api/glossary` request
  per app load regardless of how many views/components call the hook; its
  `.then()` coerces any non-object response to `{}` so a malformed or
  differently-shaped fetch mock never crashes a consumer.
- `views/RecentActivityGantt.tsx` — default landing view; composes
  `useRunsPolling` with `GanttBar`/`Legend`/`TimeAxis`; tracks an
  active→completed settle transition so a run's bar style change is not an
  instant cut.
- `views/ReplayTimelineView.tsx` — one fetch per run selection (no
  independent polling loop); renders phase-timeline segments from the
  fetched entries in order; the live-tail caption is unconditional, never
  derived from a field check (there is no `phase`/`agent` field on
  `RawToolCall` to check).
- `views/TicketsView.tsx` — fetch-and-render table over `GET /api/tickets`;
  filter changes go through the backend query params (never re-filtered
  client-side); non-date column sort is a client-side re-order over the
  already-fetched array, since the backend `sort` param is date-only. The
  tag filter renders `optionsFacets.tags` (never `rows`, never
  `docs/guidelines/tag_registry.jsonl`) through a manual-loop `narrowTags()`
  helper — never `Array.prototype.filter` — capped at `MAX_VISIBLE_TAGS`
  (40) and narrowed further by a local search input; selecting a tag still
  round-trips through the existing `toggleTag()`/`applyFilters()` ->
  `fetchTickets()` path with one repeated `tag=` param per selection.
- `components/GanttBar.tsx` — `classifyFinalStatus` buckets `DONE`→green,
  any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`→red, else neutral gray; the
  inferred-active and authoritative-completed render branches share no CSS
  class tokens. Exports `toPercent(ts, windowStartIso, windowEndIso)`, the
  time-to-horizontal-position mapping both the bars and `TimeAxis` use, so
  the two can never visually diverge. Each render branch also carries an
  on-chart `data-testid="gantt-bar-run-label"` span with the full `run_id`
  in `textContent` (untruncated in the DOM, for tests and accessibility)
  but visually clamped via a `max-w-[180px]`/`overflow-hidden`/`text-ellipsis`/
  `whitespace-nowrap` class so a long, hyphen-heavy id can neither soft-wrap
  inside a narrow (<1%-wide) bar nor bleed into neighboring rows. Additive
  to (not a replacement for) the existing hover tooltip.
- `components/Legend.tsx` — reuses `GanttBar`'s status-bucket class map so
  the legend and bars can never visually diverge.
- `components/TimeAxis.tsx` — renders 7 evenly-spaced ticks with local-time
  labels above the scrollable row list, using `GanttBar`'s exported
  `toPercent` for tick positioning.
- `components/PlaybackScrubber.tsx` — takes a bare integer index range;
  imports no types from `api.ts` and has no knowledge of
  `RunTimeline`/`TimelineEntry`, so "scrub never fetches" is structural.
- `views/StatsView.tsx` — fetches both `/api/stats/agent-monitoring` and
  `/api/stats/tickets` in parallel via `Promise.all` on mount (fetch-once,
  no polling); either request failing surfaces one shared error state rather
  than a partial render of just the successful domain. Renders two
  `<section>`s (Agent Monitoring, Ticket Corpus) built from `BarChart`,
  `GroupedBarChart`, and `StatTile`, plus two plain `<table>`s (top agents
  by call volume, slow runs) following `TicketsView.tsx`'s existing table
  conventions. The per-ticket "Incomplete artifacts" table was removed
  (kept the aggregate "Artifact completeness" `StatTile` only) — the
  underlying data remains fully available via `GET /api/stats/tickets`'s
  `artifact_completeness.incomplete` field, just not rendered as a UI
  table.
- `components/BarChart.tsx` — generic single-hue horizontal magnitude bar
  chart (`{label, value}[]` in, sorted desc and capped to `maxBars` by
  default, or `sortByValue={false}` to preserve caller order for a
  time-series caller like the velocity chart). No new charting dependency —
  plain divs with inline `backgroundColor`, matching `GanttBar.tsx`'s
  existing convention; hover tooltips reuse the already-installed
  `@radix-ui/react-tooltip`.
- `components/GroupedBarChart.tsx` — 2-series grouped bar chart (used only
  for tier distribution: count vs. done), with a legend since ≥2 series are
  present.
- `components/StatTile.tsx` — `label`/`value` tile, no delta/trend (this is a
  point-in-time status board, not a period-over-period comparison view).
- `components/GlossaryTooltip.tsx` — `{term, glossary, children}` wrapper
  around Radix `Tooltip`; renders `children` completely unwrapped (no
  tooltip, no crash) when `term` is null, the glossary has no matching entry,
  or the glossary hasn't loaded yet — guarded independently of `useGlossary`'s
  own `.then()` coercion, so a consumer is safe even if it's ever called with
  a differently-shaped glossary object. Wired into `TicketsView.tsx`
  (Tier/Layer/ticket-status/Priority cells), `ReplayTimelineView.tsx` (event
  `status`), and `StatsView.tsx` (Slow Runs `final_status` cell); `BarChart`/
  `GroupedBarChart` take a separate optional `descriptions` prop that appends
  a second line to their existing tooltip content rather than nesting a
  second `Tooltip.Root`. All description text is sourced from `/api/glossary`
  — there is no hardcoded description string anywhere in
  `dashboard-frontend/src/`, enforced by a source-string regression guard in
  `StatsView.test.tsx`. Deliberately **not** wired into `GanttBar.tsx`/
  `Legend.tsx`: `GanttBar` renders only `run.run_id` as text (never a raw
  status string) and colors bars via a synthetic 3-way bucket
  (`done`/`failed`/`neutral`) that collapses many status values many-to-one,
  and `Legend`'s three labels are hand-written descriptive prose, not a
  single glossary term — no 1:1 term-to-label mapping exists there. Also not
  wired onto ticket frontmatter `status` (a different doc-lifecycle enum) or
  Replay's `call.status`/`tailCall.status` (an unconfirmed, different
  vocabulary from event-status).
- `lib/chartPalette.ts` — two hex constants (`CHART_SERIES_1` blue,
  `CHART_SERIES_2` green) used by the two chart components above. Validated
  via the project's `dataviz` skill's `scripts/validate_palette.js` against
  this app's actual dark chart surface (`--color-bg-tertiary: #242835`) — the
  app's own pre-existing `--color-accent-*` tokens failed that validation for
  chart-mark use and were not reused here.

## Architecture Law

- **`main.py` never gains a static-file mount.** `serve.py`'s `build_app`
  constructs a *separate* `FastAPI()` instance, copies `main.py`'s routes
  onto it via `include_router` (a copy, never a mutation of `main.app`), and
  mounts `StaticFiles` only on that new instance. `main.py`'s own `app`
  object must never contain a `StaticFiles(`/`.mount(` reference. Guarded by
  `test_main_mounts_no_static_files`
  (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
- **Port allocation** (five distinct values, no collisions): `8000` — main
  simulation API's `make serve`. `8420` — `dashboard-serve` production
  (`serve.py`'s `DEFAULT_PORT`). `8471` — `dashboard-dev`'s backend half
  (`--reload`). `5174` — `dashboard-frontend`'s Vite dev server
  (`vite.config.ts`'s `server.port`). `3000` — Docusaurus `docs-serve`.
  `5173` is `frontend/`'s unrelated main-app dev port, listed only to
  disambiguate it from `5174` — never the dashboard's own port.
- **`dashboard-serve` never invokes Node or npm at runtime.** Its Makefile
  recipe is exactly `python3 -m src.api.agent_ops_dashboard.serve`; only
  `dashboard-install`, `dashboard-build`, and `dashboard-dev` invoke `npm`.
  Guarded by `test_serve_module_has_no_node_npm_invocation`
  (`tests/tools/test_agent_ops_dashboard_serve.py`) and
  `test_dashboard_serve_recipe_has_no_npm_or_node`
  (`tests/tools/test_dashboard_makefile_targets.py`).

## Known Limitation

`RawToolCall` still has no `phase` or `agent` field at all — this remains a
genuine gap in the type, not a nullable field, confirmed unchanged as of
2026-07-19. Live (in-progress) tool-call rows therefore still render an
unconditional "phase unknown — run still in progress" caption in
`ReplayTimelineView.tsx` rather than any derived or guessed value. **The
source data this type would need now exists**: `TCK-20260719-LIVE-PHASE-AGENT-LABEL`
added nullable `phase`/`agent` fields to the raw `agent-monitoring/tools.jsonl`
records themselves (populated for workflow runs after 2026-07-19) — but that
ticket deliberately stopped at the data-production boundary and never touched
`models.py`/`ingest.py`/`ReplayTimelineView.tsx`. Wiring `RawToolCall` and its
consumers to the new fields remains a real, identified, unticketed follow-up —
see `docs/plans/archive/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md`'s
own Archived note.

## Related

- Parity ledger: `docs/parity_ledger/infrastructure.yaml`, INFRA-275 (backend
  routes, ingest, cache, ticket-run join, inferred-active heuristic, and the
  two Stats-tab endpoints/frontend consumption).
- Parity ledger: `docs/parity_ledger/infrastructure.yaml`, INFRA-276
  (`serve.py` design, Makefile targets).
- Parity ledger: `docs/parity_ledger/infrastructure.yaml`, INFRA-279
  (glossary registry + `/api/glossary` endpoint) and INFRA-280 (glossary
  frontend tooltip wiring).
- `docs/guides/agent_ops_dashboard.md` — user/developer guide: build/run/serve
  commands and a usage walkthrough for each view.
- `docs/guides/ticket_reporting.md` — CLI-side counterpart ("Pillar 2") to the
  Stats tab's Ticket Corpus section; both read from the same
  `tools/ticket_stats_report.py` computation functions.
