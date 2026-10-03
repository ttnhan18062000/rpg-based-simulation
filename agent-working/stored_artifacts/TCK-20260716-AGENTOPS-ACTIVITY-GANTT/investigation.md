---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-ACTIVITY-GANTT
artifact_type: investigation
tags: [observability, agent-monitoring]
---

# Investigation — TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Current Behavior

**The ticket's own "Related Code Areas" list is stale and must not be used.** It lists
`.claude/workflows/implement-ticket.js`, `tools/agent-monitoring/{post_tool_hook,pre_tool_hook,record_run,validate}.py`,
`src/api/read_model_cache.py`, `src/api/routes/history.py`, `src/observability/reporting/history_query.py`,
`src/api/server.py`, `src/api/ws/stream.py` — these were the backend ticket's own *reuse-source*
references, written before `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND` was implemented. That ticket is
now DONE and built a **standalone** FastAPI app that is not mounted on `src/api/server.py` and does
not use `src/api/ws/stream.py`. Confirmed by direct read of `src/api/agent_ops_dashboard/main.py:1-8`
(module docstring: *"Not mounted on src/api/server.py ... No StaticFiles mount here (owned by the
sibling AGENTOPS-BUILD-SERVE ticket)"*).

**Real ground-truth API surface** (`src/api/agent_ops_dashboard/main.py`, `models.py`):

- `GET /api/runs` (`main.py:52-60`) — query params `limit: int = Query(default=50, ge=1, le=100)`,
  `offset: int = 0`, `status: Optional[str]`, `workflow: Optional[str]`, `since: Optional[str]` (ISO
  timestamp string, compared as a plain string, not parsed as a `datetime`). Returns
  `List[RunSummary]`.
- `RunSummary` (`models.py:66-77`): `run_id`, `workflow`, `tier`, `final_status`,
  `start_ts: Optional[str]`, `end_ts: Optional[str]`, `duration_s: Optional[int]`, `agent_count: int`,
  `is_inferred_active: bool`, `inferred_start_ts: Optional[str]`.
- `GET /api/runs/{run_id}` → `RunDetail` (adds `ticket_title`, `ticket_lifecycle_state`), 404 via
  `HTTPException` if unmatched.
- `GET /api/runs/{run_id}/timeline` → `RunTimeline`.
- `GET /api/health` → `HealthStatus`.

**`GET /api/runs` filtering/sort/pagination implementation** (`src/api/agent_ops_dashboard/ingest.py:487-513`,
`DashboardCache.get_runs`):

```python
all_run_ids = set(self._runs_by_id) | set(self._inferred_active)
summaries = []
for run_id in all_run_ids:
    summary = _build_run_summary(...)
    if status is not None and summary.final_status != status: continue
    if workflow is not None and summary.workflow != workflow: continue
    if since is not None and (summary.start_ts is None or summary.start_ts < since): continue
    summaries.append(summary)
summaries.sort(key=lambda s: s.start_ts or "", reverse=True)
return summaries[offset : offset + limit]
```

Critical implementation detail: **`since` filters the candidate set, but does not change the
`limit`/`offset` slicing behavior.** The full `since`-matched set is sorted `start_ts` descending,
then sliced to `[offset:offset+limit]`. If more than `limit` (max 100) runs fall inside the polled
window, the response silently truncates to the most recent `limit` — the response carries no
total-count field, so the client cannot tell "there were exactly N results" from "there were more
than `limit` results and this is a truncated page." A caller that issues a single `since=<ISO>` request
per poll and assumes it got everything in the window will silently drop older-but-still-in-window
runs whenever the window is busy. See Risks below — this is a real correctness gap for anything wider
than the default 24h pill at current-and-growing data volume.

- `GET /api/runs/{run_id}` and `/timeline` are true 404s (`main.py:66-67`, `:74-75`), not empty 200s.
- `is_inferred_active`/`inferred_start_ts` are computed fresh every cache rebuild
  (`compute_inferred_active`, confirmed in the backend ticket's Implementation Notes) — never carried
  over — so a completing run atomically drops out of the inferred-active set on the same rebuild that
  its `runs.jsonl` row appears. The `ACTIVE_WINDOW_MINUTES=10` constant lives entirely in
  `ingest.py` and is out of this ticket's scope to touch.

**Frontend: there is currently no dashboard frontend of any kind.** `frontend/` (`/home/vboxuser/Work/rpg-based-simulation/frontend/`)
is the existing React 19.2 + Vite 7.2 + TypeScript 5.9 + Tailwind 4.1 + Radix UI + Vitest 4 game/simulation
canvas UI (`GameCanvas.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, confirmed via
`frontend/src/App.tsx:1-7` imports). `docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md` §"Four
decisions" #1 explicitly ruled out adding the dashboard as a new view inside `frontend/` — direct read of
`frontend/src/components/` confirmed it is a live game-simulation UI, "a real product-boundary mismatch
for an ops/ticket dashboard." The user chose a separate SPA. `PROPOSAL.md` §5's architecture diagram
shows the dashboard's frontend as its own top-level tree, siblings to a separate `backend/` — not nested
inside the existing `frontend/`. No `dashboard-frontend/` (or any other candidate top-level name) directory
exists yet — confirmed via direct `ls` of the repo root and `frontend/`.

**Stale path in this ticket's own Related Code Areas**: `expected: frontend/src/views/RecentActivityGantt.tsx`.
This same generic `frontend/src/views/<View>.tsx` pattern also appears verbatim in the two sibling
frontend tickets (`AGENTOPS-TICKETS-VIEW` → `frontend/src/views/TicketsView.tsx`,
`AGENTOPS-REPLAY-TIMELINE` → `frontend/src/views/ReplayTimelineView.tsx`), which is strong evidence
this was a boilerplate placeholder path written before the "separate SPA, not inside `frontend/`"
decision was confirmed with the user on 2026-07-16 (same day the idea doc and these tickets were
authored) — it directly contradicts that decision and must not be followed literally. See Risks below.

**Sequencing** (`tickets/todos/agent-ops-dashboard/SEQUENCE.md`): implementation order is
`AGENTOPS-DASHBOARD-BACKEND` (done) → `AGENTOPS-ACTIVITY-GANTT` (this ticket) → `AGENTOPS-REPLAY-TIMELINE`
→ `AGENTOPS-TICKETS-VIEW` → `AGENTOPS-BUILD-SERVE`. **This ticket is confirmed the first of the three
frontend view tickets to run** — no scaffold exists yet, and none of REPLAY-TIMELINE/TICKETS-VIEW/BUILD-SERVE
have run.

`TCK-20260716-AGENTOPS-BUILD-SERVE.md` (todos, not yet started) Scope is: new Makefile targets
(`dashboard-install/-build/-dev/-serve`), `vite build` wiring, and a `FastAPI` `StaticFiles` mount on
port 8420. Its own Assumptions/Open Questions state: *"This ticket has no independent value until
AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE, and AGENTOPS-DASHBOARD-BACKEND's
outputs exist to package."* — i.e. BUILD-SERVE **packages** an already-existing, already-buildable
frontend project; it does not create the initial `package.json`/`vite.config.ts`/`tsconfig`/entrypoint.
Nothing else in the batch owns scaffold creation. See Anti-Drift Hazards for the scope boundary this
implies.

**Existing frontend conventions to mirror** (`frontend/package.json`, `frontend/vite.config.ts`,
`frontend/tsconfig.json`, `frontend/src/App.tsx`):
- `package.json`: React `^19.2.0`, Vite `^7.2.4`, TypeScript `~5.9.3`, Tailwind `^4.1.18` (via
  `@tailwindcss/vite`), Radix UI primitives (`@radix-ui/react-{scroll-area,slider,slot,tabs,tooltip}`),
  `class-variance-authority`/`clsx`/`tailwind-merge`, `vitest ^4.0.18` + `@testing-library/react ^16.3.2`.
- `vite.config.ts`: `defineConfig` from `vitest/config`, `@vitejs/plugin-react` + `@tailwindcss/vite`
  plugins, `@` path alias to `./src`, dev-server proxy of `/api`, `/openapi.json`, `/docs`, `/redoc` to
  `http://127.0.0.1:8000` (the *simulation* backend — the new dashboard scaffold's proxy target must
  instead point at the dashboard backend's own port, per `idea_agent_ops_dashboard.md`'s confirmed `8420`).
  `test.environment: 'jsdom'`, `test.setupFiles: './src/test/setup.ts'`.
- `tsconfig.json` is a references-only shell pointing at `tsconfig.app.json`/`tsconfig.node.json` (the
  standard Vite React-TS template split).
- **No router library is installed or used.** `frontend/src/App.tsx:1-13` switches views via a plain
  `useState<PageView>` + a `Header` component exposing a `PageView` union type — simple state-based
  view switching, not `react-router`. This is the pattern to mirror for a 3-view dashboard shell
  (Recent Activity / Tickets / Replay), not introducing a new routing dependency.
- Test convention: `frontend/src/test/useSimulation.test.tsx` + `frontend/src/test/setup.ts` — Vitest +
  Testing Library, colocated under `src/test/`.
- **No CI wiring exists for any frontend today** — confirmed in `PROPOSAL.md` §5b: `frontend/package.json`'s
  `lint`/`Makefile`'s `typecheck` scripts are not in `.github/workflows/test.yml` (100% Python, 10 jobs).
  `AGENTOPS-BUILD-SERVE`'s own Out of Scope explicitly excludes "Adding frontend CI coverage." This
  ticket inherits that same gap — tests should still be written (Vitest, local-run convention) but will
  not be CI-gated.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter applies — this is presentation-layer tooling over agent-monitoring
telemetry (`docs/agent-monitoring/schema.md`), not simulation gameplay mechanics, and touches no
`AuthoritativeState`. The one repo-wide constraint that does apply is the API-boundary rule from
`CLAUDE.md` ("Do not expose raw domain models from APIs") — already satisfied on the backend side
(`models.py`'s typed Pydantic responses, confirmed `INFRA-275`'s `v2_evidence`); on the frontend side
the equivalent obligation is to consume the typed `RunSummary` JSON shape as documented rather than
inferring/duck-typing additional fields that aren't in `models.py`.

`experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md` §2 ("Recent Activity view") is the closest
thing to a governing spec for this ticket and is authoritative for behavior not otherwise pinned down
by the ticket's own Acceptance Criteria:
- Time window pills: `Last 24h` / `Last 7d` / `Custom range`, default `Last 24h`, backing `since`.
- Row layout: one row per `run_id`, chronological by `start_ts`/`inferred_start_ts` descending;
  concurrent overlapping runs get additional rows, never a rescaled time axis.
- Bar fill by `final_status`: `DONE` green, any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED` red,
  `EPIC_SCOPED`/`NOTHING_TO_CREATE` neutral gray.
- Inferred-active bar: striped/animated fill, left edge `inferred_start_ts` (visually softer/"~"
  annotated), right edge pinned to "now" and advancing.
- Fixed legend (once, not per-row).
- Hover tooltip: `run_id`, `tier`, `workflow`, duration-so-far or `duration_s`, `agent_count` — no
  tool-level detail (that belongs to the Replay timeline view, out of scope here).
- Click → navigate to that run's Replay timeline (stub target only; `AGENTOPS-REPLAY-TIMELINE` is not
  yet built — the click target should be a placeholder route/no-op today, not a broken deep link).
- Settle transition: ≤300ms animated fill+edge transition from striped/inferred to solid/authoritative,
  never an instant cut.

## Parity Ledger Overlap

None applicable directly. `docs/parity_ledger/infrastructure.yaml` entry `INFRA-275` covers the
backend this frontend consumes (`status: verified`, `priority: P2`) — no P0 entries in this area, so
no test_path gating is inherited by this ticket. This ticket adds no simulation-mechanics behavior and
does not need a new parity ledger entry; presentation-only frontend code over an already-parity-tracked
read-only API is not itself a parity-ledger concern per `docs/parity_ledger/schema.json`'s subsystem
scope (combat/economy/strategy/world/progression/social/infrastructure — "infrastructure" already
covers the backend piece via INFRA-275).

## Prior Work

- `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND` (done, `stored_artifacts/TCK-20260716-AGENTOPS-DASHBOARD-BACKEND/`):
  the shared backend this ticket consumes. Its `plan.md`/`investigation.md` confirm the same
  `since`-comparison-as-plain-string behavior and the `RLock`-per-method cache design; no frontend
  content.
- No prior frontend/dashboard UI ticket exists in `tickets/done/` — `docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md`
  confirms three *prior* "dashboard" tickets (`TCK-20260529-OBS-PHASE27-API-DASHBOARD`,
  `TCK-20260614-RESOURCE-DASHBOARD`, `TCK-20260607-MON-DASHBOARD`) exist but were investigated and
  ruled non-overlapping with this proposal's scope (different data domains / static Markdown output,
  not an interactive filterable dashboard).
- `src/api/server.py`'s `GET /api/v1/observability/ui` (~L272-2364) is a real, working precedent for a
  hand-rolled polling-loop + legend + timeline renderer in this exact codebase (`PROPOSAL.md` §5a) —
  useful as a design reference for polling-loop wiring and legend conventions, even though it is
  vanilla HTML/JS rather than React and belongs to a different product (the simulation engine, not this
  dashboard).

## Risks and Open Questions

1. **Scaffold ownership (needs an explicit decision, not an assumption).** This ticket's own Scope
   section says only "Build a RecentActivityGantt frontend component as the dashboard's default-landing
   view." It does not explicitly say "create the project scaffold." However: (a) `SEQUENCE.md` confirms
   this is the first frontend ticket to run; (b) `AGENTOPS-BUILD-SERVE`'s own Assumptions state it has
   "no independent value until [the three view tickets'] outputs exist to package" — i.e. BUILD-SERVE
   packages an existing project, it does not bootstrap one; (c) neither `AGENTOPS-REPLAY-TIMELINE` nor
   `AGENTOPS-TICKETS-VIEW` (read, not yet started) claims scaffold ownership either — both are worded
   identically to this ticket ("Build a `<View>` frontend component..."). No ticket in the batch
   explicitly claims "create `package.json`/`vite.config.ts`/`tsconfig`/entrypoint." Recommendation:
   this ticket should own creating the minimal shared scaffold, since it is first in sequence and the
   alternative (leaving it fully unowned) blocks all three view tickets. This is a judgment call the
   planner should confirm explicitly rather than silently inherit from this investigation.
2. **Scaffold location: `frontend/src/views/*.tsx` (as literally written in all three view tickets'
   Related Code Areas) is very likely stale/wrong**, per Current Behavior above — it collides with
   `idea_agent_ops_dashboard.md`'s confirmed decision that this dashboard is a separate deployable, not
   a view inside the existing game-UI `frontend/` app. A new top-level directory (e.g.
   `dashboard-frontend/`) is the pattern implied by `PROPOSAL.md` §5's architecture diagram. This is a
   naming/location decision, not a behavior question — flagging for the plan to state explicitly rather
   than silently defaulting to the ticket's own stale path text.
3. **`since`-only polling can silently truncate results** once a window's matching-run count exceeds
   `limit` (default 50, max 100) — see Current Behavior. At current data volume (~623 total runs,
   ~7 in a rough last-24h sample) this is not yet observably broken for the default `Last 24h` pill, but
   the `idea_agent_ops_dashboard.md` doc explicitly confirms `agent-monitoring/*.jsonl` growth is
   **unbounded** (no retention policy), and `Last 7d`/`Custom range` pills can plausibly exceed 50-100
   rows already or soon. The polling logic must not assume a single `since=<ISO>` request returns the
   full window — it needs to paginate (loop `offset += limit` while the returned page length equals
   `limit`) to be safe. This determination is made here; the plan should treat it as a required
   behavior, not defer it.
4. `ACTIVE_WINDOW_MINUTES=10` (backend-owned, unvalidated against real crashed-run timing data per this
   ticket's own Assumptions) directly bounds how long a truly-crashed run's bar keeps rendering as
   "inferred-active" before quietly aging out of `/api/runs`'s inferred set entirely (it never becomes a
   `runs.jsonl` row, so once outside the window it simply disappears rather than resolving to any
   terminal state). This view has no way to distinguish "crashed and aged out" from "never ran" — worth
   noting as a known limitation, not something this ticket can fix (the heuristic itself is out of
   scope).
5. `live_tail` `phase`/`agent` fields remaining null (independent `MONITORING_INSTRUMENTATION_GAP` /
   `idea_agent_monitoring_live_phase_label.md` fix, explicitly out of scope) does not affect this view —
   the Gantt view's hover tooltip (`run_id`, `tier`, `workflow`, duration, `agent_count`) does not depend
   on `live_tail` phase/agent labeling at all (that only affects the Replay timeline view, `RunTimeline.entries[].phase/agent`).

## Anti-Drift Hazards

- Do not implement or modify `is_inferred_active`, `inferred_start_ts`, or `ACTIVE_WINDOW_MINUTES` logic
  — that is `ingest.py`'s `compute_inferred_active`, explicitly out of scope, owned by the (already-done)
  backend ticket.
- Do not build the Replay timeline (click-through target) or Tickets table view — stub the navigation
  target only (e.g. a no-op or placeholder route), do not implement `AGENTOPS-REPLAY-TIMELINE`'s or
  `AGENTOPS-TICKETS-VIEW`'s scope early.
- Do not add Makefile targets, a `vite build` production pipeline, `FastAPI` `StaticFiles` mounting, or
  pick/hardcode port `8420` as a serving decision — that is `AGENTOPS-BUILD-SERVE`'s scope. This ticket
  should only need a **dev-mode** Vite setup (`npm run dev`) to develop/test the component; it must not
  pre-empt BUILD-SERVE's packaging decisions (e.g. do not write Makefile targets even as a "convenience").
- Do not attempt to fix `live_tail` phase/agent null labeling — independent sibling gap, explicitly out
  of scope, and not needed for this view's tooltip fields.
- Do not touch `src/api/server.py`, `src/api/ws/stream.py`, `src/api/routes/history.py`, or
  `src/api/read_model_cache.py` — none of these are the real API surface for this dashboard (see Current
  Behavior); any edit there would be scope creep into the *simulation engine's* API, a different product.
- Do not introduce a routing library (`react-router` or similar) — the existing `frontend/` convention is
  plain `useState`-based view switching; mirror it rather than adding a new dependency mid-batch (the
  other two view tickets will build on whatever shell this ticket creates).
- Do not silently assume `since` alone bounds the result set — see Risk #3. A naive implementation that
  fires one `since=<ISO>` request per poll and renders exactly what comes back will look correct today
  and quietly drop data as volume grows; this is the single highest-value regression-prevention test in
  this ticket (see test_plan.md).
- Bar styling for inferred-active vs. authoritative-completed must never share a CSS class/style token —
  AC #4 is explicit ("never sharing styling with authoritative completed bars"); a shared base class with
  only a modifier flag risks this drifting invisibly in later refactors. A test asserting mutual exclusivity
  of the style tokens (not just presence of an "estimate" label) is warranted.
