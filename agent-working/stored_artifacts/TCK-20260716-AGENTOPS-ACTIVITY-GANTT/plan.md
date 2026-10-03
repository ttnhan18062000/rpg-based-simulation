---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-ACTIVITY-GANTT
artifact_type: plan
tags: [observability, agent-monitoring]
---

# Implementation Plan — TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Summary

This ticket is the first of three frontend view tickets (`AGENTOPS-ACTIVITY-GANTT` →
`AGENTOPS-REPLAY-TIMELINE` → `AGENTOPS-TICKETS-VIEW`) and, because nothing else in the batch claims
it, it also owns creating the minimal shared dashboard frontend scaffold. The approach: (1) stand up
a new top-level `dashboard-frontend/` project — separate from the existing game-UI `frontend/` app,
per the confirmed "separate SPA" architecture decision — mirroring `frontend/`'s exact dependency
versions and `useState`-based view-switching pattern (no router library); (2) build a typed
`api.ts` client against the real backend contract in `src/api/agent_ops_dashboard/models.py`
(`RunSummary`, not the stale `frontend/src/views/*` / `src/api/server.py` references in the
ticket's own boilerplate), including a polling hook that loops on `offset` while a page returns
exactly `limit` rows, so a busy time window is never silently truncated; (3) build two small
presentational components (`Legend`, `GanttBar`) with mutually exclusive style tokens for
authoritative-completed vs. inferred-active bars, plus explicit settle-transition state/CSS for the
active→completed flip; (4) compose them into `RecentActivityGantt`, the view this ticket's
Acceptance Criteria are actually about; (5) wire a minimal `App.tsx` shell that lands on this view
by default with stub-only placeholders for the not-yet-built Tickets/Replay views; (6) confirm the
untouched backend regression suite is still green. No backend code, Makefile targets, build
pipeline, or other tickets' views are touched.

## Steps

### Step 1 — Scaffold the shared dashboard-frontend project
**Files:**
- `dashboard-frontend/package.json`
- `dashboard-frontend/vite.config.ts`
- `dashboard-frontend/tsconfig.json`
- `dashboard-frontend/tsconfig.app.json`
- `dashboard-frontend/tsconfig.node.json`
- `dashboard-frontend/index.html`
- `dashboard-frontend/src/main.tsx`
- `dashboard-frontend/src/test/setup.ts`

**Change:**
- `package.json`: mirror `frontend/package.json` dependency versions exactly — React `^19.2.0`,
  Vite `^7.2.4`, TypeScript `~5.9.3`, `@tailwindcss/vite` + Tailwind `^4.1.18`, the same
  `@radix-ui/react-{scroll-area,slider,slot,tabs,tooltip}` set (only `react-tooltip` is actually
  needed for the hover tooltip in Step 6, but keep the set aligned for consistency with the sibling
  view tickets that will build on this scaffold), `class-variance-authority`/`clsx`/`tailwind-merge`,
  `vitest ^4.0.18` + `@testing-library/react ^16.3.2`. Add an explicit `"test": "vitest run"` script
  (per test_plan.md — `frontend/package.json` has no `test` script today despite having `vitest`
  installed; this scaffold must add one rather than assume it's inherited).
- `vite.config.ts`: `defineConfig` from `vitest/config`, `@vitejs/plugin-react` + `@tailwindcss/vite`
  plugins, `@` path alias to `./src`, `test.environment: 'jsdom'`, `test.setupFiles: './src/test/setup.ts'`.
  Dev-server proxy of `/api` to the dashboard backend's own dev port (`src/api/agent_ops_dashboard/main.py`
  is a standalone FastAPI app, not mounted on the simulation's `127.0.0.1:8000`) — do **not** copy
  `frontend/vite.config.ts`'s proxy target verbatim; point at the dashboard backend's dev-server address
  instead. Do not hardcode port `8420` or add any production build/serve wiring — that is
  `AGENTOPS-BUILD-SERVE`'s scope; this step only needs `npm run dev` to work for local development.
- `tsconfig.json`/`tsconfig.app.json`/`tsconfig.node.json`: standard Vite React-TS references-only
  split, mirroring `frontend/tsconfig*.json`.
- `src/main.tsx`: standard Vite React 19 entrypoint (`createRoot(...).render(<App />)`), importing
  `App.tsx` (built in Step 7).
- `src/test/setup.ts`: Vitest + Testing Library jsdom setup, mirroring `frontend/src/test/setup.ts`.

**Do NOT touch:** `frontend/` (the existing game-UI app) — this is a wholly new sibling directory,
not a modification to `frontend/`. Do not add Makefile targets or CI workflow entries.

**Verify:** `cd dashboard-frontend && npm install && npm run build` succeeds (TypeScript compiles,
Vite bundles) with no view code yet beyond a placeholder `App.tsx` stub. This step has no
test_plan.md test of its own — it is the foundation Steps 2–8 build and test against.

---

### Step 2 — Typed API client (`api.ts`, fetch layer only)
**Files:** `dashboard-frontend/src/api.ts`

**Change:** Define TypeScript interfaces mirroring `src/api/agent_ops_dashboard/models.py` exactly
— `RunSummary` (`run_id`, `workflow`, `tier`, `final_status`, `start_ts: string | null`,
`end_ts: string | null`, `duration_s: number | null`, `agent_count: number`,
`is_inferred_active: boolean`, `inferred_start_ts: string | null`), plus `RunDetail`, `RunTimeline`,
`HealthStatus` shapes for completeness (only `RunSummary` / `GET /api/runs` is consumed by this
ticket's view, but the typed contract should not be partial). Add a plain
`fetchRuns(params: { since?: string; limit?: number; offset?: number; status?: string; workflow?: string })`
function that calls `GET /api/runs` and returns `RunSummary[]`, parsed and typed — no duck-typing of
fields not in `models.py`. No polling logic yet (Step 3).

**Do NOT touch:** `src/api/agent_ops_dashboard/main.py`, `models.py`, `ingest.py` (backend, out of
scope). Do not import from or reference `src/api/server.py`, `src/api/ws/stream.py`,
`src/api/routes/history.py`, or `src/api/read_model_cache.py` anywhere in this file — none of these
are the real API surface for this dashboard (confirmed in investigation.md; they were the ticket's
own stale boilerplate references).

**Verify:** No dedicated test_plan.md test at this granularity; verified transitively by Step 3's
`useRunsPolling.test.ts` (which exercises `fetchRuns` through mocked `fetch`).

---

### Step 3 — Polling hook with offset-loop pagination (`api.ts`, extended)
**Files:** `dashboard-frontend/src/api.ts` (same file — polling hook lives alongside the fetch client
per the resolved scaffold-ownership decision), `dashboard-frontend/src/test/useRunsPolling.test.ts`

**Change:** Add a `useRunsPolling(sinceIso: string, intervalMs = 5000)` hook that, on each poll tick:
1. Calls `fetchRuns({ since: sinceIso, limit: 100, offset: 0 })`.
2. If the returned page length equals the requested `limit` (100), issues a follow-up call with
   `offset += limit` and appends the results, repeating until a page returns fewer than `limit` rows.
   This is required because `GET /api/runs` truncates to `limit` with no total-count field — `since`
   alone does not bound the result set once a window's match count exceeds one page (investigation.md
   Risk #3 / Anti-Drift Hazards).
3. Merges all pages into a single `RunSummary[]` keyed by `run_id`, sorted `start_ts` (or
   `inferred_start_ts` for inferred-active rows) descending, and returns it plus a `isLoading`/`error`
   state.
4. A single sub-`limit` page must **not** trigger a second request (no wasted calls in the common
   case) — the loop condition is strictly `page.length === limit`, not `page.length > 0`.

**Do NOT touch:** Do not compute `is_inferred_active` or any active/inactive heuristic client-side —
this hook only merges and paginates what the backend already returned; it must never independently
infer activity state from timestamps (test_plan.md Anti-Drift Test Guard).

**Verify:** `dashboard-frontend/src/test/useRunsPolling.test.ts` — "time-window polling paginates
when a since-window's match count reaches the page limit" (mocked `/api/runs` returning exactly
`limit` results on page 1, fewer on page 2 with `offset` advanced; assert both pages merge, and that
a single sub-`limit` page does not trigger a second request).

---

### Step 4 — Legend component
**Files:** `dashboard-frontend/src/components/Legend.tsx`

**Change:** A small, stateless component rendering the fixed legend once (not per-row): a swatch +
label for each `final_status` bucket (`DONE` → green, `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED` →
red, `EPIC_SCOPED`/`NOTHING_TO_CREATE` → neutral gray, per `UI_INTERACTION_SPEC.md` §2) and a
separate swatch + label for the inferred-active striped/estimate style. Reuses the same CSS class
tokens defined in Step 5's `GanttBar.tsx` so the legend and the bars never visually diverge.

**Do NOT touch:** Do not make this component poll or fetch data — it is purely presentational,
driven by static status-to-style mapping.

**Verify:** No standalone test_plan.md test; rendered and implicitly exercised inside Step 6's
`RecentActivityGantt.test.tsx` suite (legend renders once per view mount, not per row).

---

### Step 5 — GanttBar component (bar rendering + settle-transition + mutually exclusive styling)
**Files:** `dashboard-frontend/src/components/GanttBar.tsx`

**Change:** A presentational component taking one `RunSummary`-shaped prop plus a `nowIso` (current
time, for right-edge pinning of active bars) and rendering a single Gantt row:
- **Authoritative-completed** (`is_inferred_active: false`, `start_ts`/`end_ts` set): solid fill bar,
  left/right edges from `start_ts`/`end_ts`, fill color keyed by `final_status` (same bucket mapping
  as Legend). CSS class token: `gantt-bar--authoritative` (plus a `final_status`-keyed modifier, e.g.
  `gantt-bar--status-done`).
- **Inferred-active** (`is_inferred_active: true`, `start_ts`/`end_ts` null,
  `inferred_start_ts` set): striped/animated fill, left edge from `inferred_start_ts`, right edge
  pinned to `nowIso` (advances each poll tick), and an explicit estimate label element (e.g. `~est.`
  text, distinct DOM node, not just a CSS pattern) rendered only on this variant. CSS class token:
  `gantt-bar--inferred` — **must not share any class/style token with `gantt-bar--authoritative`**;
  this is a hard requirement (AC #4) verified by an explicit disjointness test, not just visual
  inspection, so implement the two variants as fully separate class branches, never one base class
  plus a boolean modifier.
- **Settle transition**: accept an optional `justSettled: boolean` prop. When `true` (set by the
  parent view in Step 6 for exactly one render cycle after a run flips from inferred to
  authoritative), apply a CSS transition class (`gantt-bar--settling`, plain Tailwind/CSS
  `transition-all duration-300` utility — no new animation dependency) so the fill/edges animate from
  the striped/inferred look to the solid/authoritative look over ≤300ms rather than an instant class
  swap. The DOM's final state after the transition must be indistinguishable from a bar that was
  always `gantt-bar--authoritative` — no lingering inferred-only DOM nodes (estimate label) after
  settling.

**Do NOT touch:** Do not add hover-tooltip or click-navigation logic here — that belongs to the
composing view (Step 6), per the "one component, one concern" split implied by
`dashboard-frontend/src/components/` (shared UI) vs. `dashboard-frontend/src/views/` (page-level
composition + interaction).

**Verify:** Exercised via `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (Step 6) —
"completed run renders as a solid authoritative bar" (AC #1), "run present only in the
inferred-active set renders as an inferred bar anchored at inferred_start_ts" (AC #2), "inferred-active
bar and authoritative-completed bar never share styling" (AC #4).

---

### Step 6 — RecentActivityGantt view (composition, transition-state tracking, tooltip, click stub)
**Files:**
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

**Change:**
- Compose `useRunsPolling` (Step 3) + `GanttBar` (Step 5) + `Legend` (Step 4) into the default
  Recent Activity view. Use a fixed default `since` window (hardcoded "last 24h" computed from
  `nowIso`, e.g. `new Date(Date.now() - 24*3600*1000).toISOString()`) — no interactive time-window
  pill picker in this ticket (see Scope Guards; `UI_INTERACTION_SPEC.md`'s Last 24h/7d/Custom pills
  are a future enhancement, not required by any AC).
- Row layout: one row per `run_id`, sorted `start_ts`/`inferred_start_ts` descending (already sorted
  by the Step 3 hook); concurrent overlapping runs get additional stacked rows, never a rescaled time
  axis (per `UI_INTERACTION_SPEC.md` §2, adopted here as the governing behavior for anything the AC
  doesn't pin down).
- **Settle-transition state tracking**: keep a `previousRunsRef` (keyed by `run_id` →
  `is_inferred_active`) across poll ticks. On each new poll result, for any `run_id` where the
  previous tick had `is_inferred_active: true` and the new tick has `is_inferred_active: false`, pass
  `justSettled: true` to that row's `GanttBar` for one render, then clear it. This is the mechanism
  that satisfies AC #3 — no stale "still active" state is ever shown post-transition, and the
  authoritative `start_ts`/`end_ts` (not the earlier `inferred_start_ts`) are what render once
  settled.
- Hover tooltip (Radix `@radix-ui/react-tooltip`, already in `package.json` from Step 1): `run_id`,
  `tier`, `workflow`, duration-so-far (computed from `inferred_start_ts`/`nowIso` for inferred rows)
  or `duration_s` (for completed rows), `agent_count`. No tool-level detail.
- Click handler: a stub only — e.g. `onClick={() => console.debug('navigate to replay timeline', run_id)}`
  with a comment noting this is a placeholder for `AGENTOPS-REPLAY-TIMELINE`, not a real navigation.
  Do not implement any routing or detail view here.

**Do NOT touch:** Do not implement the Replay timeline detail view or Tickets table view content —
click/nav targets are stubs only. Do not compute `is_inferred_active` client-side; the transition
tracking above only reacts to the field the backend already computed, it never derives it.

**Verify:**
- `RecentActivityGantt.test.tsx`: "completed run renders as a solid authoritative bar" (AC #1)
- `RecentActivityGantt.test.tsx`: "run present only in the inferred-active set renders as an
  inferred bar anchored at inferred_start_ts" (AC #2)
- `RecentActivityGantt.test.tsx`: "active-to-completed transition across polls updates the bar
  without a stale 'still active' state" (AC #3)
- `RecentActivityGantt.test.tsx`: "inferred-active bar and authoritative-completed bar never share
  styling" (AC #4)

---

### Step 7 — App.tsx shell (default landing view, stub-only sibling views)
**Files:**
- `dashboard-frontend/src/App.tsx` (replacing the Step 1 placeholder)
- `dashboard-frontend/src/test/App.test.tsx`

**Change:** Mirror `frontend/src/App.tsx`'s pattern exactly: a `useState<PageView>` (union type
`'activity' | 'tickets' | 'replay'`) with a small header/nav exposing the three view names, no
router library. Default state is `'activity'`, rendering `RecentActivityGantt` (Step 6) on initial
mount with no other view selected. The `'tickets'` and `'replay'` branches render an explicit
placeholder/stub element (e.g. "Coming soon" text, not a functional view) — do not build any real
content for those two branches; they exist only so the shell has somewhere to route to when
`AGENTOPS-TICKETS-VIEW`/`AGENTOPS-REPLAY-TIMELINE` land later.

**Do NOT touch:** Do not add `react-router` or any routing dependency — plain `useState` switching
only, matching `frontend/src/App.tsx`'s existing convention (this scaffold is what the next two view
tickets will build on, so the pattern must be the one they inherit, not a new one).

**Verify:** `dashboard-frontend/src/test/App.test.tsx` — "scaffold smoke test: dashboard-frontend
builds and the default landing view is RecentActivityGantt" (asserts `RecentActivityGantt` renders
by default on mount, and that Tickets/Replay branches render only placeholder/stub content, not
functional views — the scope-creep guard from test_plan.md).

---

### Step 8 — Regression sanity check (backend untouched)
**Files:** None changed — verification only.

**Change:** No code change. Run the scoped backend regression suite to confirm this ticket's
frontend-only changes did not inadvertently touch `src/api/agent_ops_dashboard/` or reintroduce
coupling into `src/api/read_model_cache.py`/`src/api/server.py`.

**Do NOT touch:** Nothing under `src/api/agent_ops_dashboard/`, `src/api/server.py`,
`src/api/ws/stream.py`, `src/api/routes/history.py`, `src/api/read_model_cache.py`.

**Verify:**
```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```
and
```
cd dashboard-frontend && npm test
```
Both must pass green before this ticket is considered complete.

## Scope Guards

- No changes to `src/api/agent_ops_dashboard/main.py`, `models.py`, `ingest.py`, or any backend code
  — `is_inferred_active`, `inferred_start_ts`, `ACTIVE_WINDOW_MINUTES` logic is owned by the
  already-done `AGENTOPS-DASHBOARD-BACKEND` ticket.
- No changes to `src/api/server.py`, `src/api/ws/stream.py`, `src/api/routes/history.py`, or
  `src/api/read_model_cache.py` — these are the simulation engine's own API surface, not this
  dashboard's backend, and are not referenced anywhere in this ticket's code or tests.
- No changes to `frontend/` (the existing game-UI app) — `dashboard-frontend/` is a new, wholly
  separate top-level directory.
- No Makefile targets, `vite build` production pipeline, `FastAPI` `StaticFiles` mount, or hardcoded
  port `8420` — that is `AGENTOPS-BUILD-SERVE`'s scope. This ticket only needs `npm run dev` /
  `npm test` to work locally.
- No Replay timeline detail view (`AGENTOPS-REPLAY-TIMELINE`) or Tickets table view
  (`AGENTOPS-TICKETS-VIEW`) content — both render as explicit stub/placeholder branches in `App.tsx`
  only.
- No `react-router` or other routing dependency — plain `useState` view switching only.
- No time-window pill picker UI (`Last 24h`/`Last 7d`/`Custom range`) — a hardcoded default
  since-window (last 24h) satisfies this ticket's Scope/AC; interactive pill switching is a
  reasonable future ticket, not part of this one (avoids overbuilding beyond what the ACs require).
- No fix for `live_tail` `phase`/`agent` always being null (`MONITORING_INSTRUMENTATION_GAP`) —
  independent sibling gap, and not consumed by this view's tooltip fields anyway.
- No CI wiring for the new frontend — `AGENTOPS-BUILD-SERVE`'s Out of Scope explicitly excludes
  adding frontend CI; tests are written and run locally only.
- No client-side re-derivation of "is this run active" from raw `tools.jsonl` timestamps — always
  render strictly from `is_inferred_active`/`inferred_start_ts` as returned by the backend.

## Dependency Map

- Step 1 (scaffold) blocks every other step — nothing else can start until `package.json`,
  `vite.config.ts`, `tsconfig*.json`, and `main.tsx` exist.
- Step 2 (api.ts fetch client) depends on Step 1 only.
- Step 3 (polling hook) depends on Step 2 (extends the same file, calls `fetchRuns`).
- Step 4 (Legend) depends on Step 1 only — independent of Steps 2/3/5.
- Step 5 (GanttBar) depends on Step 1 only — independent of Steps 2/3/4; shares style-token naming
  with Step 4 by convention, not by import dependency.
- Step 6 (RecentActivityGantt view) depends on Steps 3, 4, and 5 (composes all three).
- Step 7 (App.tsx) depends on Step 6 (renders `RecentActivityGantt` as default view).
- Step 8 (regression check) depends on Steps 1–7 being complete (final gate, no code change).

Steps 2+3, 4, and 5 can be implemented in any order relative to each other once Step 1 is done; they
only converge at Step 6.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — completed runs render as solid bars using authoritative `start_ts`/`end_ts`, `is_inferred_active` false | Steps 2, 3, 5, 6 | `RecentActivityGantt.test.tsx` — "completed run renders as a solid authoritative bar" |
| AC #2 — run in `tools.jsonl`/active window but absent from `runs_by_id` renders as inferred-active bar anchored at `inferred_start_ts` | Steps 2, 3, 5, 6 | `RecentActivityGantt.test.tsx` — "run present only in the inferred-active set renders as an inferred bar anchored at inferred_start_ts" |
| AC #3 — active→completed transition updates bar to authoritative style/values with no stale "still active" state | Steps 3, 5 (settle-transition prop), 6 (transition-state tracking) | `RecentActivityGantt.test.tsx` — "active-to-completed transition across polls updates the bar without a stale 'still active' state" |
| AC #4 — inferred-active bars always visually distinct with explicit estimate label, never sharing styling with authoritative bars | Step 5 (disjoint class tokens), Step 4 (matching legend swatches) | `RecentActivityGantt.test.tsx` — "inferred-active bar and authoritative-completed bar never share styling" |
| (Scope bullet) default-landing view | Step 7 | `App.test.tsx` — "scaffold smoke test: dashboard-frontend builds and the default landing view is RecentActivityGantt" |
| (Anti-drift / Risk #3) pagination safety under busy windows | Step 3 | `useRunsPolling.test.ts` — "time-window polling paginates when a since-window's match count reaches the page limit" |

## Anti-Drift Notes

- **Stale path in the ticket boilerplate**: the ticket's own Related Code Areas lists
  `expected: frontend/src/views/RecentActivityGantt.tsx`. Do not follow this literally — it predates
  the confirmed "separate SPA" decision in `docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md`.
  The real path is `dashboard-frontend/src/views/RecentActivityGantt.tsx`.
- **Stale backend references**: `.claude/workflows/implement-ticket.js`,
  `tools/agent-monitoring/*_hook.py`, `src/api/read_model_cache.py`, `src/api/routes/history.py`,
  `src/observability/reporting/history_query.py`, `src/api/server.py`, `src/api/ws/stream.py` in the
  ticket's Related Code Areas were the backend ticket's own reuse-source references, not this
  dashboard's real API surface. The real backend is `src/api/agent_ops_dashboard/{main,models,ingest}.py`,
  already done, consumed read-only via `GET /api/runs`.
- **Pagination correctness is the single highest-value regression-prevention test in this ticket**
  (per investigation.md): `GET /api/runs` has no total-count field, and `since` alone does not bound
  the result set once a window's matches exceed `limit` (max 100). A naive single-request
  implementation looks correct today (~7 runs in a rough last-24h sample) and will silently drop
  older-but-in-window runs as `agent-monitoring/*.jsonl` grows (unbounded, no retention policy). Step
  3's offset-loop and its test are the guard.
- **Styling mutual exclusivity is a hard requirement, not a nice-to-have**: AC #4 says inferred and
  authoritative bars must "never" share styling. Implement `GanttBar`'s two variants as fully
  separate class branches (Step 5) — a shared base class plus a boolean modifier is exactly the
  pattern the AC and its test are guarding against, and is easy to drift into during a later refactor.
- **`ACTIVE_WINDOW_MINUTES=10` is unvalidated** against real crashed-run timing data (backend-owned,
  out of scope). This view has no way to distinguish "crashed and aged out of the inferred set" from
  "never ran" — accepted as a known limitation, not something to work around client-side (e.g. do not
  add client-side heuristics to detect this case).
- **`live_tail` `phase`/`agent` nulls** (`MONITORING_INSTRUMENTATION_GAP`) do not affect this view;
  the tooltip fields (`run_id`, `tier`, `workflow`, duration, `agent_count`) don't depend on them. Do
  not attempt to fix this here.
- No parity ledger entry is needed — this is presentation-only frontend code over an
  already-parity-tracked (`INFRA-275`, `docs/parity_ledger/infrastructure.yaml`) read-only API, and
  touches no simulation mechanics or `AuthoritativeState`.

## Deviations

Implementation followed all 8 steps in order with no scope changes. Two points in this plan were
underspecified and were resolved during implementation as follows:

1. **`package.json` dependency set (Step 1)**: the plan's Summary says "mirror `frontend/`'s exact
   dependency versions" while Step 1's own detail list enumerates only React/Vite/TypeScript/Tailwind/
   Radix-UI/Vitest plus a note that "only `react-tooltip` is actually needed ... but keep the set
   aligned for consistency." The implementation mirrored *versions* exactly for every package this
   ticket's code actually imports, but did not carry over `lucide-react` (icons, unused — no icon
   usage anywhere in this ticket's components) or the `eslint`/`eslint-plugin-*`/`typescript-eslint`/
   `globals` devDependency block (no lint script or config was written; `frontend/`'s own
   `eslint.config.js` was not mirrored since nothing in Step 1–8 asked for a lint pipeline). Rationale:
   CLAUDE.md's "no unnecessary abstractions" / "don't design for hypothetical future requirements" rule
   — adding unused dependencies to satisfy a "keep the set aligned" aesthetic, when nothing in this
   ticket's 8 steps uses them, is exactly that. `AGENTOPS-REPLAY-TIMELINE`/`AGENTOPS-TICKETS-VIEW` can
   add `lucide-react` or a lint pipeline in their own tickets if/when they need them — this scaffold is
   not frozen, just started minimal.
2. **Vite dev-proxy target (Step 1)**: the plan's exact wording — "point at the dashboard backend's
   dev-server address instead. Do not hardcode port `8420`" — describes a target address that doesn't
   concretely exist: `src/api/agent_ops_dashboard/main.py` has no separate "dev port" distinct from its
   confirmed production port (`8420`, owned by `AGENTOPS-BUILD-SERVE`); a standalone FastAPI app run via
   `uvicorn` during local dev binds to whatever port it's told. Rather than hardcode `8420` (explicitly
   forbidden) or invent an equally-arbitrary literal port number as a silent fallback, the proxy target
   was made configurable via a `VITE_DASHBOARD_API_TARGET` environment variable, with a
   clearly-commented placeholder default (`http://127.0.0.1:8471`, distinct from every port already in
   use per `PROPOSAL.md`'s port table) purely so `npm run dev` starts without a crash. This does not
   preempt `AGENTOPS-BUILD-SERVE`'s port/serving decisions — no literal `8420` appears anywhere in this
   ticket's code, and the actual value used for real local development against a running backend is left
   to whoever sets the env var.

## Deviations (follow-up fix pass — DOD_BLOCKED remediation)

The initial Implement pass (Steps 1–8 above) closed all four Acceptance Criteria and the pagination
guard, but omitted two tests that `test_plan.md`'s "Anti-Drift Test Guards" section explicitly
specified. The done-checker caught this at Verify and set the ticket to `DOD_BLOCKED`. This follow-up
pass adds exactly the two missing guards; no other code from Steps 1–8 was touched.

3. **API-surface guard test (test_plan.md Anti-Drift Test Guards, bullet 1) — missing from the initial
   pass.** Implemented as a Python test,
   `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, following the same forbidden-literal-
   string-scan pattern as `tests/architecture/test_no_old_structural_content_paths.py` (walk a root
   directory, read each source file's text, flag any of a fixed set of forbidden path strings). Chosen
   over a Vitest test because the guard is checking source *text* for stale backend path references
   (`src/api/server.py`, `src/api/read_model_cache.py`, `src/api/routes/history.py`,
   `src/api/ws/stream.py`) — a static-analysis concern with an established Python-side convention in
   this repo (`tests/architecture/`), not a frontend runtime behavior. Scans
   `dashboard-frontend/src/**/*.{ts,tsx}` and fails if any forbidden path string appears anywhere in the
   file text (literal string, import specifier, or comment). Verified passing against the current
   `dashboard-frontend/src/api.ts`, which correctly references only `src/api/agent_ops_dashboard/models.py`
   in its docstring comment, not any of the four forbidden paths.
4. **No client-side `is_inferred_active` duplication guard (test_plan.md Anti-Drift Test Guards, bullet
   2) — missing from the initial pass.** Implemented as a Vitest test,
   `dashboard-frontend/src/test/GanttBar.test.tsx` (new file — `GanttBar.tsx` had no dedicated unit test
   of its own before this pass; it was previously exercised only indirectly through
   `RecentActivityGantt.test.tsx`). Four assertions: (a) a source-text guard (via Vite's `?raw` import
   suffix, typed through the already-present `vite/client` types — no new dependency, no `node:fs`/
   `@types/node` needed) asserting `GanttBar.tsx` never calls `Date.now()` or constructs `new Date(...)`
   anywhere in its source (it legitimately uses `Date.parse` to convert already-known timestamps into
   percentages, which is not activity inference); (b) a source-text guard asserting the branch selection
   is a direct `if (run.is_inferred_active)` check, not a locally recomputed boolean; (c) a behavioral
   test rendering `GanttBar` with `is_inferred_active: false` but a suspiciously "still running"-looking
   fixture (`start_ts` 5 seconds ago, `end_ts: null`) and asserting it still renders the authoritative
   branch — proving the component trusts the flag rather than second-guessing it from missing `end_ts`;
   (d) the inverse case — `is_inferred_active: true` with an `inferred_start_ts` three hours old (well
   past the backend's `ACTIVE_WINDOW_MINUTES=10`) still renders the inferred branch, proving the
   component does not reimplement staleness/window logic client-side.

Both tests were verified passing together with the full existing suite: `cd dashboard-frontend && npm
test` (4 test files, 12 tests, all green — the prior 8 plus these 4 new `GanttBar.test.tsx` cases),
`npx tsc -b` (clean), `npm run build` (clean), and the backend regression command extended to include
the new guard test:
```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```
31 passed (the prior 30 plus the new guard test).
