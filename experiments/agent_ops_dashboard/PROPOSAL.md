# Proposal: Agent Ops Dashboard — a visual, feature-rich viewer over tickets + agent-monitoring data

**Status:** proposed, design only — no code written
**Location:** `experiments/agent_ops_dashboard/` (sandbox — same convention as the other experiment proposals: `placement_integrity/`, `spatial_rendering/`, `model_routing/`, `loop/`, `audit_expansion/`)
**Date:** 2026-07-16

**Documents in this folder** (each covers a distinct angle, no overlap by design):
- `PROPOSAL.md` (this document) — origin, scope decisions, architecture, the real-time investigation, tooling/deployment
- `IMPLEMENTATION_CONTEXT.md` — reusable code inventory, exact ticket/registry schemas, scale figures
- `MONITORING_INSTRUMENTATION_GAP.md` — the confirmed phase/agent live-labeling gap and its fix
- `DATA_MODEL.md` — concrete API contract (endpoint schemas), `ingest.py`'s internal data structures, concurrency/locking design
- `UI_INTERACTION_SPEC.md` — view-by-view UX/interaction detail (columns, filters, scrubber mechanics, detail drawers)
- `TEST_PLAN.md` — concrete fixture matrix and test-case list for both backend and frontend

---

## 1. Origin

Direct request: the existing Docusaurus integration for agent-monitoring retro reports
(`TCK-20260607-MON-DASHBOARD`) is static Markdown — no interactivity, no cross-cutting views over
tickets + runs + artifacts, no charts beyond what a Markdown table can express. The ask was for
something "advanced, visual-optimized, feature-rich" for reviewing the whole agent working process,
not just weekly retro snapshots.

---

## 2. What already exists — checked before proposing anything new

Per this repo's Context Scan rule, `search_docs` + `graphify query` + direct reads were run before
any design work. Confirmed landscape:

- **`agent-monitoring/{runs,events,tools}.jsonl`** — the real, live, already-populated data source.
  Schema fully documented in `docs/agent-monitoring/schema.md`. ~617 runs, ~2,981 events, ~54,876
  tool-call rows as of this investigation (2026-07-16).
- **`tools/agent-monitoring/generate_retro.py`** — turns this data into static weekly Markdown
  reports (`agent-monitoring/retro/RETRO-*.md`), which `TCK-20260607-MON-DASHBOARD` then wired into
  Docusaurus as a content root. This is the thing being superseded for interactive use, not
  replaced outright — retro reports remain a useful periodic artifact in their own right.
- **`docs/guides/ticket_reporting.md`** — a "pillars" framing for ticket-corpus reporting. Exactly
  one pillar is built (`tools/tag_report.py`, tag-usage counts). It explicitly lists, as **not
  built**: ticket velocity/throughput, tier/type/priority distribution, layer distribution,
  artifact completeness. This proposal's Tickets view covers the first two implicitly (filterable
  table over the same `tickets/` + `working_log.csv` + `docs/REGISTRY.yaml` data those pillars
  would use) but does not attempt the full reporting-pillar treatment — a real future overlap to be
  aware of, not resolved here.
- **Three prior "dashboard" tickets**, all a different shape than this proposal:
  - `TCK-20260529-OBS-PHASE27-API-DASHBOARD` — behavior-profiling API/storage integration, not a
    ticket/monitoring viewer.
  - `TCK-20260614-RESOURCE-DASHBOARD` — a CLI (`python -m src diagnostics resources`), not a web UI.
  - `TCK-20260607-MON-DASHBOARD` — the Docusaurus integration described above (the thing this
    proposal's motivation is reacting to).

No existing implementation overlaps this proposal's actual scope: an interactive, filterable,
visual web dashboard over ticket lifecycle + agent-monitoring runs/events/tools data.

**Correction found during deeper investigation (2026-07-16):** the statement above is still true
for *agent-monitoring/ticket* data specifically, but a directly analogous dashboard for a different
data domain already exists and is highly relevant to *how* to build this one — see §5a, which
reopens part of §3's stack decision with new evidence.

---

## 3. Scope decisions made during design (with rationale)

Each of these was a deliberate choice among named alternatives, not a default:

| Decision | Chosen | Rejected alternative(s) and why |
|---|---|---|
| Interactivity | Read-only viewer + rich client-side filters/drill-downs | Full read-write management (trigger re-runs, approve gates) — much bigger scope, opens a write path into a system this repo treats as agent-authoritative; not requested once framed as a distinct option |
| Data freshness | Live local server, frontend polls on an interval | On-demand snapshot rebuild only — rejected in favor of a server process so the view updates while agents are actively working |
| Stack | FastAPI backend + React/Vite SPA | Streamlit/Dash (lower visual ceiling, not bespoke) — rejected because "visual-optimized, feature-rich" was the explicit ask; server-rendered HTMX (no Node toolchain) — rejected in favor of a real SPA's higher interaction ceiling |
| Serving mode | Single Python process serves the **pre-built** static SPA (`vite build` + FastAPI `StaticFiles`) | Running `vite dev` alongside FastAPI as two processes — rejected once the deployment target was clarified (see §4): this may run on the same VM as the simulation-engine session, so a persistent Node process is unnecessary always-on overhead. Node is only needed once, at build time. |
| Data domains (v1) | Tickets lifecycle + agent-monitoring runs/events/tools | Docs registry / parity ledger / epic rollups — explicitly deferred, not selected for v1; staging/stored artifact completeness — same, deferred |
| Data layer | In-memory cache, rebuilt on file-`mtime` change | SQLite ingestion cache — rejected: introduces a second durable data store that must stay in sync with the JSONL files forever, in tension with this repo's "don't duplicate durable state" architecture rule. Naive per-request reparse — rejected: wasteful at current (~58k-line) and growing scale. |
| Deployment | Local-only, single user, binds to localhost | LAN-shareable (`0.0.0.0`, no auth) — rejected; not needed for a single-user sandbox tool today |

---

## 4. Performance footprint (given likely co-location with the simulation-engine VM)

Direct question raised during design: this may run on the same VM used for implementing/testing
the simulation engine. Addressed concretely rather than reassured vaguely:

- **At rest:** one Python process (uvicorn/FastAPI), no database process, no Node runtime process
  (frontend is a pre-built static bundle served by the same process). Expected RSS in the tens of
  MB, ~0% CPU idle.
- **Per poll:** the mtime-cache design means most polling ticks are a handful of `os.stat()` calls —
  microseconds, not measurable against a running simulation test.
- **On actual change:** a full reparse+rejoin of the current data volume (~58k total JSONL lines)
  is a sub-second Python operation, not a sustained load, and only triggers when
  `agent-monitoring/*.jsonl` or `tickets/**` actually change.
- **No I/O contention with simulation runs specifically:** the dashboard only reads
  `agent-monitoring/*.jsonl` and `tickets/`, never `data/runs/` (the simulation's own chunked
  output) — no shared write path with an active simulation test.
- Default poll interval set to 5-10s (human-review cadence, not a live ticker), keeping even the
  cheap stat-check overhead negligible.

---

## 5. Architecture

```
experiments/agent_ops_dashboard/
├── PROPOSAL.md                          (this document)
├── MONITORING_INSTRUMENTATION_GAP.md     (companion investigation — see §8)
└── prototype/                            (not yet built — design phase only)
    ├── backend/                           # FastAPI app
    │   ├── main.py                         # app, routes, StaticFiles mount for the built SPA
    │   ├── ingest.py                       # reads+joins runs/events/tools.jsonl + ticket frontmatter, mtime-cached
    │   └── models.py                       # Pydantic response shapes — API boundary never returns raw parsed dicts
    └── frontend/                          # React + Vite SPA (built to static assets for serving)
        ├── src/
        │   ├── pages/                       # TicketsView, RunsView (Recent Activity timeline), RunDetail (Replay timeline)
        │   ├── components/                  # Gantt rows, replay scrubber, filter bar, files-touched panel
        │   └── api.ts                        # typed fetch client + polling hook
        └── vite.config.ts
```

**Backend:**
- `ingest.py` owns all file reads. Checks `mtime` of `runs.jsonl`/`events.jsonl`/`tools.jsonl`/
  `tickets/**/*.md` before each cache use; unchanged → serve from memory, changed → reparse just
  the changed file(s) and rejoin. Reuses `tools/agent-monitoring/validate.py`'s existing
  legacy-schema tolerance (5-6 documented historical `runs.jsonl` generations, per `schema.md`'s
  "Known Limitations" section) instead of reimplementing it.
- `main.py` exposes read-only endpoints: `/api/tickets`, `/api/runs`, `/api/runs/{run_id}`,
  `/api/runs/{run_id}/timeline` (events ⋈ tools joined on `run_id`+`seq`, pre-ordered by `seq`),
  `/api/health` (diagnostic — see §6). Responses are `models.py` Pydantic schemas, never raw parsed
  dicts, matching this repo's "don't expose raw domain models" API rule even for a read-only viewer.
  **Exact field-level schemas for every endpoint, `ingest.py`'s internal data structures, and a
  concurrency/locking design not covered anywhere else are in `DATA_MODEL.md`.**

**Frontend:**
- **Tickets view** — table over `tickets/inprogress` + `tickets/done` + `tickets/todos`, filterable
  by tier/layer/status/priority/tag, sortable by date. Rows link to their run detail when a matching
  `run_id` exists.
- **Recent Activity view** (the cross-run timelapse — see §7) — the default landing page.
- **Run detail / Replay timeline** (the per-run timelapse — see §7).

**Concrete view-by-view UX/interaction detail (columns, filters, scrubber mechanics, hover/click
behavior, detail drawers) is in `UI_INTERACTION_SPEC.md`** — this section and §7b describe what
each view shows and why; that document describes exactly how a user interacts with it.

---

## 5a. Critical finding — an already-proven, directly analogous dashboard exists in this codebase

While investigating the real-time question further (§7), a full observability dashboard was found
already live at `GET /api/v1/observability/ui` in `src/api/server.py` (lines ~272-2364) — the "V2
Simulation Live Observatory Dashboard." This is a *different data domain* (live simulation-engine
state: ticks, entities, hard-law violations, anomalies — not tickets/agent-monitoring), but it is
the closest possible precedent for "advanced, visual-optimized, feature-rich dashboard for
reviewing agent/system work," built and running in this exact repo, and it materially changes the
stack question in §3.

**What it actually is, confirmed by direct read, not assumed:**
- A single FastAPI route returns one large `HTMLResponse` containing hand-written CSS and vanilla
  JS — **zero build step, zero Node/React dependency, zero bundler.** Not a toy — it has 5 tabs
  (Live Run, Completed Runs, Sweeps & Baselines, Event Search, Entity Timeline), glassmorphic dark
  styling, filter pills, health-status badges, JSON detail drawers, and a working reconnect-aware
  WebSocket client.
- **Genuinely live data via WebSocket**: `src/api/ws/stream.py`'s `/ws/observability/events`
  endpoint streams live `SimulationEvent`s with server-side query-param filtering
  (severity/entity/category/region/quest), a 10-connection cap, backpressure-triggered disconnect,
  and a 5-second heartbeat — a complete, working example of exactly the kind of genuinely-live push
  channel §7 discusses adding for agent-monitoring's `tools.jsonl` tail, except this one already
  exists and runs today, for a different data source.
- **Periodic-summary data via plain polling**, not WebSocket: `startPollingLoops()`
  (`server.py:1636`) does `setInterval(pollTelemetryAndHealth, 1500)` — a 1.5s poll against
  `/api/v1/observability/live/status` and `/live/health`. Confirms polling and WebSocket
  comfortably coexist in one dashboard, used for the parts of the data that fit each model — the
  same split this proposal's §7b already lands on independently (inferred-live Gantt bars via
  polling, `tools.jsonl` tail via what could be a WebSocket).
- **A working vertical timeline renderer already exists**: `loadEntityTimeline()`
  (`server.py:2297-2359`) fetches a list of `{type, tick, timestamp, severity, message, details}`
  items and renders them as a vertical flow — left column (tick + timestamp), center bullet
  (event vs. anomaly icon), right card (title, severity badge, message, a "View Details JSON"
  toggle drawer). This is structurally almost identical to what §7b's per-run **Replay timeline**
  needs to render (phase/tool-call sequence instead of entity events/anomalies) — a real,
  copy-adapt starting point, not a pattern to design from scratch.
- **Backend precedent for list+detail endpoints**: `src/api/routes/history.py` +
  `src/observability/reporting/history_query.py`'s `HistoricalRunQueryService` —
  `list_historical_runs(limit, offset) -> List[RunManifest]` and
  `get_run_manifest(run_id) -> RunManifest`, with `Query(...)` param validation and
  400/404/500 `HTTPException` handling. This is the exact shape this proposal's own
  `/api/runs` and `/api/runs/{run_id}` endpoints (§5) should mirror.

**Why this reopens §3's stack decision, honestly, not silently:** §3 chose "FastAPI + React/Vite
SPA" before this precedent was found, reasoning that a real SPA gives the highest visual/interaction
ceiling. That reasoning still holds on its own terms. But this discovery adds a real, working,
lower-cost alternative that wasn't on the table during that decision: **a single embedded
HTML+CSS+JS page, mirroring `src/api/server.py`'s own pattern exactly**, which:
- Needs **zero** Node/npm involvement, ever — not even at build time (§4's footprint concern is
  even further reduced: no `node_modules`, no `vite build` step, no bundle to keep in sync).
- Is a pattern **already proven to satisfy** "advanced, visual-optimized, feature-rich" in this
  same codebase, for a comparably complex dashboard (5 tabs, live streaming, timeline
  visualization, filtering, drill-down detail panes) — not a hypothetical lesser option.
- Directly reuses real, working CSS classes and JS functions as a starting template, materially
  cutting implementation effort versus building a React component library from zero.
- Trade-off, named honestly: a single hand-written JS file of this shape (`server.py`'s dashboard
  section is ~2,000 lines of HTML/CSS/JS in one Python string) is harder to unit-test, harder to
  maintain at scale, and has a lower ceiling for complex client-side state management than a real
  component framework — the same reasons React/Vite was chosen in §3 in the first place.

**This is left as an open decision for whoever plans the implementation, not resolved here.** Three
concrete options now exist, all backed by real in-repo precedent (a third was found during the
tooling/deployment investigation in §5b — see there for the evidence):
1. **Vanilla embedded HTML/CSS/JS**, following `src/api/server.py`'s exact pattern — lowest
   footprint, fastest to build from the existing Entity Timeline / Completed Runs code as a
   template, consistent with this repo's own established convention for developer dashboards.
2. **FastAPI + React/Vite SPA** (§3's original choice) — higher long-term interaction/maintainability
   ceiling. §5b found this is **not** actually a new toolchain for this repo — `frontend/` (React 19
   + Vite 7 + TypeScript + Tailwind 4 + Radix UI) already exists as a live, shipping app, built via
   `make build` and served from the same Python process via `make serve` — the exact pattern this
   option describes is already this repo's established production convention, just for a different
   frontend.
3. **A dashboard view added to `frontend/` itself** (new, only surfaced by §5b) — since a real,
   modern React app already exists and is already served by the same backend process pattern, a
   dashboard could in principle be a new route/page inside the *existing* `frontend/` app rather
   than a wholly separate one. Not investigated further here — whether the existing `frontend/`
   app's purpose (a live game/simulation UI) and this dashboard's purpose (ticket/agent-monitoring
   review) belong in the same deployable is a real product-boundary question, not a technical one,
   and should be decided with the user, not assumed.

Recommendation for the next investigator: this is now a three-way judgment call informed by real
precedent in every direction, not a foregone conclusion — confirm with the user before writing any
frontend code.

---

## 5b. Tooling, deployment, and service management — investigated after being flagged as missing

The original design pass covered architecture and the real-time question in depth but never
addressed how this thing actually gets built, started, stopped, tested, or kept running — a real
gap, named directly by the user rather than found independently. Checked this repo's actual
conventions (`Makefile`, `docker-compose.yml`, `.github/workflows/`, `frontend/`) rather than
inventing new ones.

### Ports already in use, confirmed by direct read

| Port | What | Source |
|---|---|---|
| `8000` | Simulation engine backend (`python3 -m src serve --port 8000`) | `Makefile` (`dev-backend`, `serve`, `run-engine`), `src/cli/entry.py:24` default |
| `5173` | `frontend/`'s Vite dev server | `Makefile`'s `dev`/`dev-frontend` targets (Vite's own default) |
| `3000` | Docusaurus docs site (`make docs-serve`) | `Makefile` |
| `6379`, `5672`, `15672` | Redis, RabbitMQ (AMQP + management UI) — Docker-Compose-only, not present in a plain local run | `docker-compose.yml` |

**The dashboard must pick a distinct port**, not reuse any of these — e.g. `8420` (arbitrary, does
not collide with anything above), configurable via a `--port` flag mirroring the existing
`python3 -m src serve --port` convention exactly rather than inventing a new flag style.

### Makefile convention — mirror it, don't reinvent it

This repo's existing full-stack pattern (`Makefile` lines ~14-51) is: `install` (`install-py` +
`install-fe`) → `build` (`cd frontend && npm run build`) → `dev` (backend + Vite dev server
concurrently, trapped so Ctrl-C kills both) → `serve` (`build` then start the single Python
process that now also serves the built frontend). **This is the exact shape this proposal's own
serving model (§5) already independently arrived at** — not a coincidence to ignore. Whichever
frontend option from §5a is chosen, new Makefile targets should follow this same naming pattern
precisely, e.g.:

```
dashboard-install   # pip install (if new deps) + cd .../frontend && npm install (only if option 2/3 chosen)
dashboard-build     # only if option 2/3 chosen — builds the static frontend bundle
dashboard-dev        # hot-reload dev mode, for developing the dashboard itself
dashboard-serve      # the actual day-to-day command: build (if needed) + start the one process
```

Deliberately **separate target names**, not reusing `install`/`build`/`dev`/`serve` — those already
mean "the simulation engine's own frontend," and colliding names would either silently shadow them
or force ambiguous double-duty targets.

### Process management — plain foreground process, not Docker

`docker-compose.yml`'s "production-grade stack" (backend + Redis + RabbitMQ + Kafka + `ai_worker`,
each with healthchecks) exists because those services genuinely need message queues and
inter-service coordination. **The dashboard has none of that** — it only reads local files
(`agent-monitoring/*.jsonl`, `tickets/`) already present on disk. Containerizing it would add
volume-mount complexity (mapping the host repo's `tickets/`/`agent-monitoring/` into a container)
for zero real benefit. Recommendation: **a plain foreground process**, started via
`make dashboard-serve`, stopped with Ctrl-C — matching how `make dev-backend`/`make serve-only`
already work for the simulation engine's own backend, and consistent with §4's "local-only, single
user" deployment decision.

A real resilience pattern already exists in this repo if it's ever needed —
`src/observability/watchdog.py`'s `SimulationWatchdog` (`docs/architecture/simulation_watchdog.md`)
polls `/health`/`/metrics` with a `consecutive_failures`/`max_failures=3` threshold, built for the
Docker Compose stack's genuine uptime requirements. **Not recommended for v1** — adopting a
watchdog for a tool a single human starts and stops by hand would be solving a problem this
dashboard doesn't have. Named here so a future agent doesn't rediscover it and over-apply it.

### Testing and CI — confirmed exact conventions, and one real gap

- **Backend Python tests** would live in `tests/tools/` once this graduates from `experiments/`
  into a real ticket — confirmed as a genuine, CI-gated location: `.github/workflows/test.yml`'s
  "API / tools / logging" job runs `pytest tests/api tests/cli tests/tools tests/logging
  tests/engine tests/observability -m "not slow"`. The `experiments/` prototype itself is correctly
  exempt from all CI today (confirmed by reading `test.yml` in full — it only ever runs `tests/`
  paths and `make lane-*`/`make gate-expansion` targets, nothing under `experiments/`).
- **Frontend testing convention, if option 2/3 is chosen**: `frontend/package.json` already has
  `vitest` + `@testing-library/react` as dependencies, and a real example test exists
  (`frontend/src/test/useSimulation.test.tsx`) — mirror this setup rather than introducing a
  different test runner.
- **Real, surprising gap found: the frontend has zero CI coverage today.** `frontend/package.json`
  defines `lint` (eslint) and the `Makefile` defines `typecheck` (`tsc --noEmit`) — but neither
  appears anywhere in `.github/workflows/test.yml`, which is 100% Python across all 10 of its jobs.
  **Do not assume choosing the React/Vite option gets free CI enforcement** — if that's wanted for
  the dashboard's own frontend, it would need genuinely new CI steps, not something inherited by
  precedent (the precedent, if anything, is that this repo currently does *not* gate frontend
  quality in CI at all).
- `python3 -m mypy src/ --config-file pyproject.toml --no-error-summary || true` — Python type
  checking exists but is explicitly informational (`|| true`, `continue-on-error: true` in CI,
  with a comment noting the baseline error count isn't documented yet) — not a hard gate to match
  or worry about failing.

---

## 6. Error handling

This is a read-only viewer over append-only, occasionally-messy data. Principles:

- Never crash the API on a malformed/legacy line — skip it, count it in `/api/health`'s
  `unparsed_lines` diagnostic, mirroring `validate.py`'s own tolerant posture.
- A run with no `end_ts` yet renders as "presumably active" (see §7's inference logic), not as an
  error state.
- Frontend shows a stale-data banner if polling fails (backend down/restarting) rather than
  silently freezing on last-good data unlabeled.

---

## 7. The real-time question — investigated precisely, not assumed

Direct question raised during design: "can I get a real-time dashboard with this design?" Checked
the actual write path in `.claude/workflows/implement-ticket.js` rather than assume polling alone
would answer it.

### 7a. What's actually live vs. batched — confirmed by reading the code

- **`tools.jsonl` is genuinely real-time.** Written by `PreToolUse`/`PostToolUse` hooks
  (`tools/agent-monitoring/pre_tool_hook.py`, `post_tool_hook.py`) immediately, per tool call.
- **`runs.jsonl` and `events.jsonl` are not.** `pushEvent()` (`implement-ticket.js:180`) only
  appends to an in-memory `events[]` array during the run. `writeMonitoring()`
  (`implement-ticket.js:258`) — the function that actually calls `record_events.py` and
  `record_run.py` to write to disk — is called **exactly once per run**, at whichever exit point
  fires: an early gate failure (e.g. `CONFLICTS_DETECTED` at line 364, `TESTS_FAILED` at line 740)
  or the final `DONE` at line 1179 after Finalize. For a ticket passing cleanly through all phases,
  **zero phase-level data exists on disk until the very end**, then the whole run's history lands
  in one batch.
- **A run in progress has zero rows in `runs.jsonl`/`events.jsonl` — not even an `IN_PROGRESS`
  placeholder.** Confirmed by reading `writeMonitoring` and `record_run.py`'s single call site
  (`implement-ticket.js:311`): there is no separate "write a start record immediately at Scope"
  call anywhere in the current code. The `IN_PROGRESS` value documented in `schema.md` is a value
  the schema/`validate.py` tolerates, not one this code path currently produces — a genuinely
  useful correction to how "live" was first assumed to work.

### 7b. Design response: two complementary timeline views, honest about which parts are live

**Recent Activity view (cross-run, the "timelapse" landing page):** a Gantt-style row per run over
a selectable window (last 24h/7d):
- Completed runs render as solid bars, `start_ts`→`end_ts` (authoritative, from `runs.jsonl`),
  colored by `final_status`.
- Because no run-in-progress record exists anywhere, "currently active" is **inferred** from
  `tools.jsonl`'s live tail: any `run_id` with a recent tool-call timestamp and no matching
  completed row yet in `runs.jsonl` is presumed still running. Rendered as an open-ended,
  visually distinct bar (striped/"LIVE" badge) — its start edge is an *estimate* (first `tools.jsonl`
  timestamp seen for that `run_id`), explicitly labeled as inferred, not authoritative.
- When the run finishes and its batched write lands, the bar swaps from inferred-live to
  solid-authoritative, with a brief visual "settle" transition.

**Run detail / Replay timeline (the per-run timelapse):** once a run completes, every event's `ts`
was captured live via `bash date -u` at the real moment each phase happened (documented in
`schema.md`'s `events.jsonl` field table — "Captured by the orchestrator... immediately before the
paired `agent()` call, not self-reported"), even though the write to disk was batched. So the full
phase-by-phase + tool-call sequence can be **replayed accurately after the fact**: a scrub bar /
adjustable-speed playback control over the reconstructed sequence, not just a static list. Segments
show phase duration (derived from consecutive event timestamps), `cost_proxy_score` per phase, and
a files-touched panel aggregated from `tools.jsonl.input_summary` (already captures file paths for
Read/Edit/Write/MultiEdit, per `post_tool_hook.py`'s `_input_summary()`).

**Confirmed live-view gap, addressed in §8:** while a run is active, `tools.jsonl` rows carry a bare
`seq` integer — no `phase`, no `agent` name — because those only exist in `events.jsonl`, which
isn't written until the run completes. This blocks a genuinely live "currently in Implement phase,
implementer agent" label. §8 documents the confirmed, small, additive fix and why it's out of scope
for this experiment's own prototype code.

### 7c. What this design explicitly does NOT attempt

Modifying `writeMonitoring()`'s call cadence itself (e.g. flushing after every phase instead of once
per run) was considered and rejected for v1 — it's a change to the core orchestration script every
ticket runs through, materially riskier than anything else in this proposal, and not required to
deliver the two timeline views above (both work with the current, unmodified write cadence; the
Recent Activity view's live bar is inferred from `tools.jsonl`, and the Replay timeline only needs
accurate historical `ts` values, which already exist).

---

## 8. Confirmed blocking gap in agent-monitoring instrumentation

Per direct instruction to identify — not just work around — any agent-monitoring feature gaps that
block this epic's goals: one real, confirmed gap was found (live tool-call rows carry no `phase`/
`agent` label). A minimal, evidence-backed fix was investigated and found feasible, but it touches
production orchestration code (`.claude/workflows/implement-ticket.js`) and an existing regression
test, so per this repo's own rules it cannot be built inside `experiments/` — it needs its own real
ticket. Full findings, exact line citations, and the proposed fix are in the companion document:

**`MONITORING_INSTRUMENTATION_GAP.md`** (same folder).

This dashboard's v1 scope does not depend on that fix landing first — the Recent Activity and
Replay timeline views both function with today's instrumentation (§7b). The fix would upgrade the
Recent Activity view's live bars and the Replay timeline's live edge from "tool activity, phase
unknown until completion" to "tool activity, phase + agent labeled live."

---

## 9. Testing plan

- Backend: pytest fixtures covering `ingest.py`'s join logic against sample JSONL files spanning
  the current schema, 2-3 documented legacy schema generations, a crashed run (no `end_ts`), and an
  out-of-workflow tool call (`run_id: null`).
- Frontend: component-level tests for the Replay timeline renderer against a fixed sample run
  payload — not full e2e, out of scope for a v1 sandbox experiment.
- No `tests/` (production suite) coverage needed — this lives entirely under `experiments/` and
  touches no `src/`.
- **The concrete fixture matrix (one row per schema generation/edge case) and the actual test-case
  list for both backend and frontend are in `TEST_PLAN.md`** — this section states the testing
  philosophy; that document states the specific tests.

---

## 10. Explicitly out of scope for v1

- Docs registry / parity ledger / epic-rollup views (not selected as a v1 data domain).
- Any write-back path from the UI (re-running tickets, editing status, approving gates).
- Token-count telemetry — confirmed not recorded anywhere in the current platform
  (`schema.md`: "Token counts are not recorded... no workaround within the current platform").
- Multi-user auth / LAN sharing — local-only, single user.
- Modifying `writeMonitoring()`'s per-run batching (§7c).

---

## Related

- `experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md` — companion reference doc: reusable code inventory, exact ticket/registry schemas, and open verification items for whoever plans the implementation
- `experiments/agent_ops_dashboard/DATA_MODEL.md` — exact API contract, `ingest.py`'s internal data structures, concurrency/locking design
- `experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md` — view-by-view UX/interaction detail
- `experiments/agent_ops_dashboard/TEST_PLAN.md` — concrete fixture matrix and test-case list
- `src/api/server.py` (~L272-2364) — the existing "V2 Simulation Live Observatory Dashboard," the precedent behind §5a
- `src/api/ws/stream.py` — the existing WebSocket streaming pattern (`/ws/observability/events`), a real precedent for genuinely-live push if that's chosen over polling for the `tools.jsonl` tail
- `src/api/routes/history.py`, `src/observability/reporting/history_query.py` — the existing list+detail endpoint pattern (`HistoricalRunQueryService`) this proposal's `/api/runs` endpoints should mirror
- `frontend/` (`package.json`, `src/`) — the real, already-shipping React 19 + Vite 7 + TypeScript + Tailwind 4 + Radix UI + Vitest app; the stack to match if §5a's SPA option is chosen
- `Makefile` (`install`/`build`/`dev`/`serve` targets, ~L14-51), `docker-compose.yml`, `.github/workflows/test.yml` — the tooling/deployment/CI conventions documented in §5b
- `src/observability/watchdog.py`, `docs/architecture/simulation_watchdog.md` — the existing service-resilience pattern, named in §5b as available but not recommended for v1
- `docs/agent-monitoring/schema.md` — full field definitions for `runs.jsonl`/`events.jsonl`/`tools.jsonl`, the legacy-schema generations, and the join pattern this proposal's `ingest.py` reuses
- `docs/guides/agent_monitoring.md` — retro cadence, `validate.py`, `epic_staleness_check.py` — existing read-only monitoring tooling this proposal extends into a visual surface rather than replacing
- `docs/guides/ticket_reporting.md` — the "pillars" framing for ticket-corpus reporting; overlap noted in §2, not resolved here
- `tools/agent-monitoring/validate.py` — legacy-schema tolerance logic this proposal's `ingest.py` (once built) should reuse, not reimplement
- `.claude/workflows/implement-ticket.js` — `pushEvent()` (L180), `writeMonitoring()` (L258), `writeSidecar()` (L202), `record_run.py` call site (L311) — the exact code this proposal's §7 findings are based on
- `tools/agent-monitoring/post_tool_hook.py`, `pre_tool_hook.py` — the hooks that write `tools.jsonl`, confirmed to carry no `phase`/`agent` field today
- `tests/tools/test_current_run_sidecar_orchestrator.py` — the regression test that would need updating alongside any `writeSidecar` signature change (see companion doc)
- `tickets/done/TCK-20260607-MON-DASHBOARD.md`, `TCK-20260614-RESOURCE-DASHBOARD.md`, `TCK-20260529-OBS-PHASE27-API-DASHBOARD.md` — prior "dashboard" work, confirmed non-overlapping (§2)
- `experiments/spatial_rendering/PROPOSAL.md`, `experiments/placement_integrity/PROPOSAL.md` — sibling sandbox proposals this one follows the same format/conventions from
