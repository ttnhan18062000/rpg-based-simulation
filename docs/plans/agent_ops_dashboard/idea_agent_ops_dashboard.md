---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-16
tags: [idea, agent-infrastructure, observability, dashboard, reporting]
---

# Idea: Agent Ops Dashboard — a visual, feature-rich viewer over tickets + agent-monitoring data

> **Maturity: IDEA** — Not scheduled, no ticket filed yet. Full investigation trail, exact API/data
> schemas, and UX detail live in `experiments/agent_ops_dashboard/` (`PROPOSAL.md` + 5 companion
> documents); this doc distills that trail into the standard idea-doc shape and records the four
> stack/design decisions confirmed with the user on 2026-07-16. See companion idea
> [`idea_agent_monitoring_live_phase_label.md`](idea_agent_monitoring_live_phase_label.md) for the
> related, deliberately-independent instrumentation gap this investigation also found.

## Problem

The existing Docusaurus integration for agent-monitoring retro reports (`TCK-20260607-MON-DASHBOARD`)
is static Markdown — no interactivity, no cross-cutting view over tickets + runs + artifacts, no
charts beyond a Markdown table. Direct request was for something "advanced, visual-optimized,
feature-rich" for reviewing the whole agent working process, not just weekly retro snapshots.

Checked before proposing anything new (`search_docs` + `graphify query` + direct reads, per this
repo's Context Scan rule): `agent-monitoring/{runs,events,tools}.jsonl` is the real, live data
source (~617 runs / ~2,981 events / ~54,876 tool-call rows as of 2026-07-16), already fully
documented in `docs/agent-monitoring/schema.md` and already turned into static retro Markdown by
`tools/agent-monitoring/generate_retro.py`. Three prior "dashboard" tickets exist
(`TCK-20260529-OBS-PHASE27-API-DASHBOARD`, `TCK-20260614-RESOURCE-DASHBOARD`,
`TCK-20260607-MON-DASHBOARD`) — none overlap this proposal's actual scope: an interactive,
filterable, visual web dashboard over ticket lifecycle + agent-monitoring runs/events/tools data.

A real, working precedent for "advanced, visual-optimized, feature-rich dashboard" already exists in
this exact repo for a *different* data domain: `GET /api/v1/observability/ui`
(`src/api/server.py`, ~L272-2364) — the "V2 Simulation Live Observatory Dashboard," a single
FastAPI route returning hand-written HTML/CSS/vanilla-JS with 5 tabs, a working reconnect-aware
WebSocket client (`src/api/ws/stream.py`), a vertical timeline renderer (`loadEntityTimeline()`,
L2297), and polling-loop wiring (`startPollingLoops()`, L1636). This materially shaped the stack
decision below.

## Idea

**Read-only viewer + rich client-side filters/drill-downs** over two v1 data domains: ticket
lifecycle (`tickets/inprogress` + `tickets/done` + `tickets/todos`) and agent-monitoring
runs/events/tools. Three views:

- **Tickets view** — filterable/sortable table (tier/layer/status/priority/tag), row-click links to
  the matching run's Replay timeline.
- **Recent Activity view** (default landing page) — a Gantt-style row per run over a selectable
  time window. Completed runs render as solid, authoritative bars (`start_ts`→`end_ts` from
  `runs.jsonl`); a run with no `runs.jsonl` record yet but recent `tools.jsonl` activity renders as
  an inferred-live, striped bar — explicitly labeled as an estimate, never rendered identically to
  authoritative data.
- **Run Detail / Replay timeline** — a scrubbable phase-by-phase + tool-call playback for a
  completed (or live) run, plus a static files-touched panel derived from
  `tool_calls[].input_summary`.

**Backend:** FastAPI (`main.py`, `ingest.py`, `models.py`) exposing `/api/tickets`, `/api/runs`,
`/api/runs/{run_id}`, `/api/runs/{run_id}/timeline`, `/api/health`. All responses are Pydantic
schemas, never raw parsed dicts, per this repo's "don't expose raw domain models" API rule.
`ingest.py` owns all file reads, rebuilding an in-memory cache on `mtime` change — reusing
`tools/agent-monitoring/validate.py`'s legacy-schema tolerance and
`tools/validate_frontmatter.py::extract_frontmatter()` rather than reimplementing either.

**Serving:** single Python process serves the pre-built static SPA (`vite build` + FastAPI
`StaticFiles`) — Node is needed only at build time, never as a persistent process, given this may
co-locate with the simulation-engine VM.

## Four decisions confirmed with the user (2026-07-16)

Each reopened and investigated further than the original proposal, with concrete evidence, before
being put to the user:

1. **Stack: FastAPI + React/Vite SPA.** A third option — a new view inside the existing
   `frontend/` app — was independently ruled out first: direct read of
   `frontend/src/components/` (`GameCanvas.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`,
   `ClassHallPanel.tsx`) confirmed `frontend/` is a live game/simulation canvas UI, a real
   product-boundary mismatch for an ops/ticket dashboard. Between the SPA and a lower-footprint
   vanilla embedded HTML/CSS/JS option (mirroring `src/api/server.py`'s own dashboard, zero Node
   ever), the user chose the SPA for its higher long-term interaction/maintainability ceiling —
   accepting that no CI coverage exists for any frontend in this repo today
   (`frontend/package.json`'s `lint`/`typecheck`/`vitest` scripts are not wired into
   `.github/workflows/test.yml`), so this dashboard's frontend inherits that same gap unless new CI
   steps are added separately.
2. **Instrumentation gap fix sequencing: independent sibling ticket, not blocking.** See
   [`idea_agent_monitoring_live_phase_label.md`](idea_agent_monitoring_live_phase_label.md).
   Dashboard v1 ships without waiting on it — both timeline views function with today's
   instrumentation, degrading a live run's tail to an honest "phase unknown" rather than a guess.
3. **Ticket↔run ambiguity: return all matches, not one.** A `ticket_id` sharing its value with
   multiple `runs.jsonl` rows (retried/re-run tickets) was assumed rare when first raised. Direct
   query against live data found otherwise: **43 of 618 `runs.jsonl` rows share a `run_id` with
   another row.** `ingest.py`'s ticket↔run join returns every match (sorted `start_ts` descending),
   not a first-match-wins pick that would silently hide genuine retry history.
4. **Concurrency: `RLock`-per-method**, directly reusing `src/api/read_model_cache.py`'s
   `ReadModelCache` pattern rather than a build-outside-lock/atomic-swap design. Simpler, already
   proven in this codebase, and justified by the confirmed sub-second full-rebuild time at current
   data volume — revisit only if `agent-monitoring/*.jsonl` growth (confirmed **unbounded**: no
   retention/rotation policy targets these files anywhere in the repo, unlike `data/runs/`'s
   `RetentionPolicy`/`RetentionManager`) ever makes rebuild time noticeable.

## Architecture Constraints

- API responses are `models.py` Pydantic schemas only — never raw parsed dicts (repo-wide API
  boundary rule).
- Ticket data must be parsed directly from frontmatter (`extract_frontmatter()`) across all three
  lifecycle directories — `docs/REGISTRY.yaml` is confirmed **not** a viable source: it only ever
  contains `tickets/done/` entries, and its ticket-type rows omit `status`/`layer`/`priority`
  entirely (three of the four filter dimensions this dashboard needs).
- `tier`, `ticket_type`, `priority`, and workflow `## Status` are **body-section fields, never
  frontmatter**, for any ticket — reuse `generate_registry.py::parse_body_section()`/
  `parse_h1_title()` rather than assuming `extract_frontmatter()` alone covers them.
- Reuse `tools/agent-monitoring/validate.py`'s `LEGACY_COMPLETION_FIELDS`/
  `LEGACY_TERMINAL_STATUS_VALUES` allowlists for the 5-6 documented historical `runs.jsonl`
  generations — do not re-derive legacy-schema tolerance from scratch.
- Mirror `src/observability/reporting/history_query.py::HistoricalRunQueryService`'s existing
  list+detail endpoint shape (`Query(default=50, ge=1, le=100)` pagination,
  `HTTPException(400/404/500)`) for `/api/runs` and `/api/runs/{run_id}`.
- Distinct port required (existing ports confirmed in use: `8000` sim backend, `5173` sim frontend
  dev, `3000` Docusaurus) — `8420` proposed and confirmed free on the current dev machine, exposed
  via a `--port` flag matching `python3 -m src serve --port`'s existing convention.
- New Makefile targets (`dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve`)
  mirror the existing `install`/`build`/`dev`/`serve` pattern under distinct names — do not reuse
  those names, which already mean the simulation engine's own frontend.
- Plain foreground process (`make dashboard-serve`, Ctrl-C to stop) — not Docker Compose, which
  exists for genuine multi-service coordination this local single-user tool doesn't need.
- Backend tests land in `tests/tools/` once past `experiments/` (confirmed CI-gated location, the
  "API / tools / logging" job in `.github/workflows/test.yml`); frontend tests mirror
  `frontend/src/test/`'s existing Vitest + Testing Library convention.

## Relationship to Planned Tickets

None yet — this is the not-yet-scheduled origin doc for whatever ticket(s) this becomes. The
companion idea [`idea_agent_monitoring_live_phase_label.md`](idea_agent_monitoring_live_phase_label.md)
is a related but independent sibling, not a dependency in either direction. Real, deferred overlap
worth checking before scoping a ticket: `docs/guides/ticket_reporting.md`'s "pillars" framing for
ticket-corpus reporting explicitly lists ticket velocity/throughput and tier/type/priority
distribution as **not built** — this dashboard's Tickets view covers those implicitly via a
filterable table over the same underlying data, but does not attempt the full reporting-pillar
treatment. Not resolved here.

## Open Questions

- Whether `tools/generate_registry.py::parse_related_code_areas()` should be reused if the Tickets
  view ever wants a "Related Code Areas" column — not required for v1, not investigated further.
- Whether `MONITORING_INSTRUMENTATION_GAP.md`'s (now `idea_agent_monitoring_live_phase_label.md`'s)
  fix should be scoped as a real ticket before, after, or fully independent in timing from this
  dashboard's own ticket — decided as *non-blocking*, but relative sequencing/priority is still
  unset.
- Whether frontend CI (lint/typecheck/vitest wired into `.github/workflows/test.yml`) should be
  added as part of this dashboard's own ticket, given the repo currently has none for any frontend —
  a real scope-size question, not resolved by the stack decision alone.
- Whether the confirmed-unbounded growth of `agent-monitoring/*.jsonl` warrants its own retention
  policy as separate, prerequisite work, or stays purely an in-memory-cache concern for this
  dashboard to revisit later.
- `experiments/agent_ops_dashboard/TEST_PLAN.md` row 9's ticket-data-quality signal (a ticket with
  valid frontmatter but missing `## Tier`/`## Priority`/`## Type` body sections) — worth its own
  assertion per that document, not silently defaulted, but not decided here either.

---

*Raised: 2026-07-16, distilled from `experiments/agent_ops_dashboard/PROPOSAL.md` and its five
companion documents (`IMPLEMENTATION_CONTEXT.md`, `DATA_MODEL.md`, `UI_INTERACTION_SPEC.md`,
`TEST_PLAN.md`, `MONITORING_INSTRUMENTATION_GAP.md`) — see that folder for the full investigation
trail, exact endpoint/field schemas, and view-by-view UX detail this idea's claims are drawn from.
Four open design decisions (stack, gap-fix sequencing, ticket↔run ambiguity, concurrency) were
investigated further and confirmed with the user on 2026-07-16; those documents were updated in
place with dated decision notes rather than left as open questions.*
