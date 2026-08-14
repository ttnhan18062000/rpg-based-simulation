---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-AGENTOPS-DASHBOARD-DOCS
artifact_type: investigation
tags: [documentation, observability, api-design]
---

# Investigation — TCK-20260717-AGENTOPS-DASHBOARD-DOCS

## Current Behavior

This ticket is pure documentation authoring over five already-DONE, already-parity-tracked
tickets. There is no "current behavior" for the module itself (no `src/`/`dashboard-frontend/src/`
code exists for this ticket to touch) — the relevant current behavior is the real, shipped surface
this ticket must describe accurately. All of the below is confirmed by direct read, not by the
stale boilerplate any of the five source tickets' own "Related Code Areas" carried forward.

**Backend — `src/api/agent_ops_dashboard/main.py`** (82 lines): standalone `FastAPI(title="Agent
Ops Dashboard API")` (`main.py:24`), module-level `_cache = DashboardCache()` (`main.py:26`), five
typed routes:
- `GET /api/tickets` (`main.py:29-49`) — params `tier`, `layer`, `status`, `priority` (each
  `Optional[str]`, single-value), `tag: Optional[List[str]] = Query(default=None)` (the only
  repeatable/multi-value param), `lifecycle`, `q`, `sort: str = "date_desc"`.
  `response_model=List[TicketSummary]`.
- `GET /api/runs` (`main.py:52-60`) — `limit: int = Query(default=50, ge=1, le=100)`,
  `offset: int = Query(default=0, ge=0)`, `status`, `workflow`, `since` (ISO string, compared as a
  plain string, never parsed to `datetime`). `response_model=List[RunSummary]`.
- `GET /api/runs/{run_id}` (`main.py:63-68`) — `response_model=RunDetail`; 404 via
  `HTTPException(status_code=404, ...)` when `_cache.get_run` returns `None`.
- `GET /api/runs/{run_id}/timeline` (`main.py:71-76`) — `response_model=RunTimeline`; same 404
  pattern.
- `GET /api/health` (`main.py:79-81`) — `response_model=HealthStatus`.

**Response models — `src/api/agent_ops_dashboard/models.py`** (97 lines): `RunMatchSummary`
(`:17-21`), `TicketSummary` (`:24-36`, `status` = frontmatter doc-lifecycle field, always present;
`workflow_status` = body `## Status` section, nullable — two distinct fields, never conflated),
`RawToolCall` (`:39-44`, **no `phase`/`agent` field at all** — not nullable, simply absent from the
type), `FileTouch` (`:47-50`), `TimelineEntry` (`:53-63`), `RunSummary` (`:66-76`), `RunDetail(RunSummary)`
(`:79-81`, adds `ticket_title`, `ticket_lifecycle_state`), `RunTimeline` (`:84-89`), `HealthStatus`
(`:92-96`, `status` field is hardcoded `"ok"` always — never derived from parse-error counts).

**Ingest/cache — `src/api/agent_ops_dashboard/ingest.py`** (586 lines): reuses (never
reimplements) `tools/validate_frontmatter.py::extract_frontmatter` (`ingest.py:32`),
`tools/generate_registry.py`'s `parse_body_section`/`parse_h1_title`/`_strip_frontmatter`
(`ingest.py:33`), and `tools/agent-monitoring/validate.py`'s tolerant `load_jsonl` + legacy
allowlists (`ingest.py:34,59`). `DashboardCache` class (`ingest.py:348-586`) — single
`threading.RLock()` (`ingest.py:361`) guarding every public method
(`get_tickets` `:448-485`, `get_runs` `:487-513`, `get_run` `:515-528`, `get_timeline` `:530-575`,
`get_health` `:577-585`); `_maybe_rebuild`/`_rebuild` (`:386-446`) re-run the full parse+join+
inference pipeline under the same lock on any source `mtime` change (never the swap-based
build-outside-lock alternative). `build_matching_runs` (`:178-199`) returns **all** matching
`runs.jsonl` rows per `ticket_id`, sorted `start_ts` descending, rows without `start_ts` sorted
last — never collapsed to one. `compute_inferred_active` (`:234-256`) implements the
`ACTIVE_WINDOW_MINUTES = 10` (`:48`) heuristic: a `run_id` present in `tools.jsonl` but absent from
`runs_by_id`, whose most recent tool-call `ts` is within the window, is `is_inferred_active=True`;
recomputed fresh every rebuild (never carried over), so a completing run atomically flips out of
the set. `extract_files_touched` (`:264-284`) dedups by path keeping first `ts`+`tool` seen,
restricted to `_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}` (`:49`). `get_tickets`'s
filter is AND-across-`tier`/`layer`/`status`(=`workflow_status`)/`priority`, OR-within-`tags`
(set intersection, `:476`); sort is **date-only** (`:484`, `date_asc`/`date_desc`) — there is no
server-side support for sorting by tier/layer/status/priority/tag despite `UI_INTERACTION_SPEC.md`
language to the contrary; the shipped `TicketsView.tsx` compensates with a client-side re-order
layer (see below).

**Serve module — `src/api/agent_ops_dashboard/serve.py`** (64 lines): `DEFAULT_HOST = "127.0.0.1"`,
`DEFAULT_PORT = 8420` (`:24-25`), `DEFAULT_DIST_DIR` = `dashboard-frontend/dist` relative to repo
root (`:26`). `build_app(dist_dir)` (`:29-42`) validates `dist_dir/index.html` exists (else
`RuntimeError` naming `make dashboard-build`), builds a **separate** `FastAPI()` instance
(`serve_app`, `:39`), copies `main.app`'s routes via `serve_app.include_router(main_app.router)`
(`:40`, a read-only copy — never mutates `main.app`), then mounts
`StaticFiles(directory=str(dist_dir), html=True)` at `"/"` (`:41`) — **after** `include_router`, so
`/api/*` is matched before the catch-all static mount. `_build_parser` (`:45-50`) declares
`--host`/`--port`/`--dist-dir`. `main()` (`:53-59`) imports `uvicorn` locally (inside the function,
not top-of-module) so importing `serve.py` never starts a server or touches the filesystem.

**Makefile — four new targets** (`Makefile:1` `.PHONY` list includes all four;
`Makefile:53-68`, under a `# ── Agent Ops Dashboard ──` heading):
- `dashboard-install` (`:53-54`) — `cd dashboard-frontend && npm install`
- `dashboard-build` (`:56-57`) — `cd dashboard-frontend && npm run build`
- `dashboard-dev` (`:59-65`) — backend `uvicorn src.api.agent_ops_dashboard.main:app --host
  127.0.0.1 --port 8471 --reload` concurrently with `(cd dashboard-frontend && npm run dev)`, via
  `trap 'kill 0' INT ... & ... & wait` (mirrors the existing `dev:` target's shape, `Makefile:29-35`)
- `dashboard-serve` (`:67-68`) — `dashboard-build` prerequisite (mirrors the existing `serve: build`
  edge), recipe body is exactly `python3 -m src.api.agent_ops_dashboard.serve` (no npm/node in this
  recipe)

**Frontend dev port — `dashboard-frontend/vite.config.ts:19`**: `server.port: 5174`. This is the
**real, confirmed** dashboard-frontend dev port, distinct from `frontend/vite.config.ts`'s `5173`
(the unrelated main game-UI app's dev port) and from `dashboard-dev`'s **backend** half's port
`8471` (`vite.config.ts:9`'s `VITE_DASHBOARD_API_TARGET` proxy-target default, which
`dashboard-dev`'s Makefile recipe now binds live — no `vite.config.ts` edit was ever needed). The
ticket's own Assumptions section already corrects an inbound "5173" framing to 5174 — confirmed
correct here by direct read, not to be second-guessed.

**Full port table** (five distinct values, no collisions confirmed live at
`TCK-20260716-AGENTOPS-BUILD-SERVE`'s own Completion Summary): `8000` (`make serve`, main
simulation API), `8420` (`dashboard-serve`, production dashboard, `--port`-configurable), `8471`
(`dashboard-dev`'s backend half, `--reload`), `5174` (`dashboard-frontend`'s Vite dev server,
`vite.config.ts:19`), `3000` (`docs-serve`, Docusaurus). `5173` is `frontend/`'s (the main game-UI
app's) unrelated dev port, listed only to distinguish it from `5174`.

**Frontend SPA structure** (`dashboard-frontend/src/`):
- `App.tsx` (59 lines) — `useState<PageView>('activity' | 'tickets' | 'replay')` (`:6,15`), no
  router library; `selectedRunId` state + `handleSelectRun` (`:16-21`) wired to all three views'
  `onSelectRun`/navigation; `NAV_ITEMS` (`:8-12`) drives the header nav; default landing view is
  `'activity'` (`RecentActivityGantt`, `:44`).
- `api.ts` (221 lines) — TypeScript interfaces mirroring `models.py` field-for-field (`RunSummary`
  `:6-17`, `RunDetail` `:19-22`, `RawToolCall` `:24-30` — no `phase`/`agent`, matching the backend
  — `FileTouch` `:32-36`, `TimelineEntry` `:38-49`, `RunTimeline` `:51-57`, `HealthStatus` `:59-64`,
  `TicketSummary`/`RunMatchSummary` `:74-94`); `fetchTickets` (`:107-123`), `fetchRunTimeline`
  (`:125-131`), `fetchRuns` (`:133-146`); `fetchAllRunsSince` (`:153-167`) offset-loops while a page
  returns exactly `RUNS_PAGE_LIMIT = 100` (`:151`) rows (guards `GET /api/runs`'s lack of a
  total-count field); `useRunsPolling` (`:187-220`) polls every `intervalMs` (default 5000) via
  `fetchAllRunsSince` + `mergeAndSortRuns` (`:169-179`, dedups by `run_id`, sorts by
  `start_ts ?? inferred_start_ts` descending).
- `views/RecentActivityGantt.tsx` (99 lines) — default landing view; `SINCE_WINDOW_MS` = 24h
  (`:7`), composes `useRunsPolling` + `GanttBar` + `Legend`; tracks settle-transition state
  (`previousActiveByRunIdRef`, `justSettledIds`, `:37-65`) so an active→completed flip renders a
  ≤300ms transition (`SETTLE_TRANSITION_MS = 300`, `:9`) instead of an instant cut; row `onClick`
  calls `onSelectRun(run.run_id)` (`:77`).
- `views/ReplayTimelineView.tsx` (152 lines) — one-shot `fetchRunTimeline` per `runId` change
  (`useEffect` keyed on `[runId]`, `:29-56`); `PlaybackScrubber` (scrub/play/speed, never fetches);
  phase-timeline segments from `entries` in array order (no client-side re-sort, `:84-98`);
  tool-call detail area gated by `scrubIndex` (`entries.slice(0, scrubIndex + 1)`, `:68,101-116`);
  files-touched panel renders `RunTimeline.files_touched` verbatim, grouped by `.tool` only
  (`:70-75,118-132`); `live_tail` renders the unconditional caption
  `"(phase unknown — run still in progress)"` (`PHASE_UNKNOWN_CAPTION`, `:17`) for every item when
  `is_live && live_tail.length > 0` — never derived from a field check (there is no `phase`/`agent`
  field on `RawToolCall` to check).
- `views/TicketsView.tsx` (337 lines) — fetch-and-render table over `GET /api/tickets`; filter bar
  (single-select `tier`/`layer`/`status`/`priority`, multi-select `tag`, `:208-258`) delegates
  filtering entirely to backend query params via `applyFilters`/`fetchTickets`
  (`:152-161,69-78`) — never re-filters client-side; column-header clicks on
  tier/layer/status/priority/tag trigger a **client-side** re-order (`sortRows`, `:57-67`,
  `toggleColumnSort` `:175-182`) over the already-fetched array, since the backend `sort` param is
  date-only — the date column's own sort stays server-side (`toggleDateSort`, `:163-173`), and no
  non-date `sort` value is ever sent to `fetchTickets`; `matching_runs` renders as one link per
  entry (`:313-329`), trusting the backend's `start_ts`-descending order; null
  `tier`/`priority`/`ticket_type` render as empty cells (React renders `null` as nothing, `:298-309`
  — no `??` fallback string).
- `components/GanttBar.tsx` (102 lines) — `classifyFinalStatus` (`:8-16`, `DONE`→green,
  `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`→red, else neutral gray); inferred-active
  (`gantt-bar--inferred`, `:56-74`) and authoritative-completed (`gantt-bar--authoritative`,
  `:76-101`) branches share **zero** CSS class tokens — fully separate class branches, not a shared
  base class plus a modifier.
- `components/Legend.tsx` (33 lines) — reuses `GanttBar`'s `STATUS_BUCKET_CLASS` so the legend and
  bars never visually diverge.
- `components/PlaybackScrubber.tsx` (84 lines) — deliberately imports **no** types from `api.ts`
  and has no knowledge of `RunTimeline`/`TimelineEntry` (`:14-16`); a `maxIndex <= 0` guard
  (`:45,59-64`) renders an inert placeholder track instead of Radix `Slider.Root` (avoids a jsdom
  `NaN%` style-setter crash on a single-entry/empty timeline).

**No `phase`/`agent` labeling on live tool-call rows** (`MONITORING_INSTRUMENTATION_GAP`, tracked
by a separate, independent idea doc) is a real, confirmed, still-open limitation — `RawToolCall`
has no such fields at all, and `ReplayTimelineView.tsx` renders the honest caption unconditionally.
The new guide/reference should describe this as a known limitation, per the ticket's own Out of
Scope — not attempt to fix or paper over it.

## Mechanics / Engine Constraints

Confirmed **none apply**, consistent with every one of the five source tickets' own investigations
reaching the same conclusion independently. This is presentation/observability tooling over
`tickets/**` and `agent-monitoring/*.jsonl` — it never touches `AuthoritativeState`, the tick loop,
or any `docs/mechanics/`-governed formula, and this ticket adds no code at all (docs only). The one
repo-wide rule that is *relevant to cite accurately* (not enforced by this ticket, since no code
changes) is the API-boundary rule ("do not expose raw domain models from APIs") — already satisfied
by `models.py`'s typed Pydantic responses, which the new technical reference doc should describe as
a design constraint of the already-shipped backend, not something this ticket verifies or tests.

## Parity Ledger Overlap

- **`INFRA-275`** (`docs/parity_ledger/infrastructure.yaml:4478-4528`) — `status: verified`,
  `priority: P2`. Covers the Agent Ops Dashboard backend: all 5 typed routes, `ingest.py`'s
  reuse-not-reimplement pattern, the `RLock`-per-method cache, the all-matches ticket-run join, and
  the `is_inferred_active` heuristic. `test_path` cites `test_agent_ops_dashboard_ingest.py`,
  `test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_concurrency.py`,
  `test_agent_ops_dashboard_api_boundary.py` (32/32 passing per its own evidence text). Its
  `support_boundary` explicitly **excludes** frontend, build/serve tooling, the `live_tail`
  phase/agent gap, and agent-monitoring retention/rotation.
- **`INFRA-276`** (`docs/parity_ledger/infrastructure.yaml:4529-4573`) — `status: verified`,
  `priority: P2`. Covers `serve.py`'s separate-`FastAPI()`-instance + `include_router` +
  `StaticFiles`-mount design, the argparse CLI, and the four Makefile targets. `test_path` cites
  `test_agent_ops_dashboard_serve.py` (6 named tests) and `test_dashboard_makefile_targets.py`
  (9/9 passing per its own evidence text). Its `support_boundary` explicitly notes it does not
  duplicate `INFRA-275` and excludes `dashboard-dev`'s process orchestration / CI-deploy automation.
- **No P0 entries** in either — this ticket's AC requirement to "cite by ID, not restate
  `v2_evidence` text" is satisfiable with a short `see INFRA-275` / `see INFRA-276` reference in
  both new docs; no test_path gate is inherited since neither entry is P0. **Do not edit either
  entry** — confirmed out of scope by the ticket itself and by both entries' own text.
- No other parity ledger entry overlaps this scope (confirmed by the five source tickets'
  own investigations, each of which searched `docs/parity_ledger/` directly and found only these
  two IDs plus an unrelated false-positive on the *simulation engine's* own Replay system, already
  recorded in `TCK-20260716-AGENTOPS-REPLAY-TIMELINE`'s investigation.md as a dead end not to
  re-chase).

## Prior Work

All five source tickets are DONE; their `stored_artifacts/*/investigation.md` and `plan.md` are the
authoritative design-decision record this ticket must synthesize accurately, not re-derive:

- **`TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`** — built the standalone FastAPI backend. Key
  decisions: `validate.py`'s tolerant `load_jsonl` (not `query.py`'s crashing one); ticket-directory
  walk filters to `TCK-*.md` before parsing (skips `SEQUENCE.md`); real `threading`-based
  concurrency tests, not single-threaded proxies; `matching_runs` never collapsed to one row;
  `status` vs `workflow_status` kept as two distinct fields; `GET /api/health`'s `status` field
  hardcoded `"ok"`. **Deviations** (discovered during implementation, not anticipated by the plan):
  `_coerce_ts` for legacy int/float timestamps, `_resolve_final_status`'s fallback to
  `validate._record_is_complete` for two more legacy generations, and the `_LIFECYCLE_PRIORITY`
  tie-break (`inprogress > done > todos`) for a ticket_id appearing under more than one lifecycle
  directory in the same rebuild.
- **`TCK-20260716-AGENTOPS-ACTIVITY-GANTT`** — first frontend ticket; also built the shared
  `dashboard-frontend/` scaffold (no ticket explicitly claimed scaffold ownership, this one did by
  virtue of being first in `SEQUENCE.md`). Key decisions: separate top-level SPA, not nested in
  `frontend/`; no router library; offset-loop pagination in `useRunsPolling` (guards `GET
  /api/runs`'s truncation on busy windows); `GanttBar`'s two style variants share zero CSS tokens.
  Had a `DOD_BLOCKED` fix-pass — the first Implement pass skipped two of its own `test_plan.md`'s
  Anti-Drift Test Guards (API-surface guard, no-client-side-`is_inferred_active`-derivation guard);
  both were added in a follow-up pass. This is the origin of the "guards must land in the same pass
  as feature code" lesson every subsequent sibling ticket explicitly carried forward.
- **`TCK-20260716-AGENTOPS-REPLAY-TIMELINE`** — built the Replay view + wired Gantt-row
  click-through navigation (not a formal AC bullet, but confirmed real scope from the stub
  comment already left in `RecentActivityGantt.tsx`). Key decisions: `RawToolCall` genuinely has
  no `phase`/`agent` field (not merely nullable) — the honest caption is unconditional, never a
  field check; scrub/playback never fetches (structural, via a data-agnostic `PlaybackScrubber`);
  no independent live-refresh polling cycle — one fetch per run selection is sufficient.
- **`TCK-20260716-AGENTOPS-TICKETS-VIEW`** — built the Tickets table. Key decisions: single-select
  per dimension for tier/layer/status/priority (matches the backend's actual `Optional[str]` param
  shape), multi-select only for `tag` (matches `Optional[List[str]]`) — deliberately diverging from
  `UI_INTERACTION_SPEC.md`'s stale "multi-select pills for all four" language; column sorting for
  the four non-date dimensions implemented as a client-side re-order over the already-fetched array
  (the backend `sort` param is date-only); one additive backend test closing a pre-existing
  `get_tickets` filter-coverage gap.
- **`TCK-20260716-AGENTOPS-BUILD-SERVE`** — packaged the already-built frontend+backend into one
  process. Key decision, the single hardest constraint in the whole batch:
  `test_main_mounts_no_static_files` forbids any `StaticFiles(`/`.mount(` substring inside
  `main.py` itself — the mount lives exclusively in a new sibling module (`serve.py`) building a
  *separate* `FastAPI()` instance. `dashboard-dev`'s backend binds to `8471` (matching
  `vite.config.ts`'s pre-existing placeholder default, making it live instead of dead). AC #5 (no
  port collision) was **partially** live-verified — `8000`/`8420`/`5174` tested live; `5173`
  (`frontend/`) and `3000` (`docs-serve`) confirmed only by static config read, not live-run,
  because neither toolchain's `node_modules` was installed in that environment. This partial-verify
  disclosure is itself worth citing accurately in the new docs rather than glossed over.

## Risks and Open Questions

- **Exact target file paths/names are not fully pinned by the ticket text** for the technical
  reference doc — the Scope says "a detailed technical/architecture reference in
  `docs/observability/`" without naming the file. Existing convention in that directory
  (`read_model_service_contract.md`, `hard_law_monitor.md`, `decision_trace_contract.md`,
  `prometheus_metrics.md`) is `<subsystem>_contract.md` or a descriptive `<topic>.md` — recommend
  `docs/observability/agent_ops_dashboard_contract.md` to mirror `read_model_service_contract.md`'s
  own naming exactly (both are single-subsystem API/service contracts). This is a naming
  recommendation for the plan to confirm explicitly, not an assumption to silently bake in.
- **`docs/guides/README.md`'s table needs a new row** — confirmed required by the ticket's own
  Scope and AC. The table is a flat `| Guide | What it covers |` list with 9 existing rows; no
  category grouping exists, so the new row can be appended without restructuring. No other
  index/table-of-contents references `docs/guides/` guides elsewhere in the repo that this
  investigation found (docs/README.md's own "Developer Guides" section, `docs/README.md:19` in the
  file read directly, mirrors `docs/guides/README.md`'s table verbatim and would need the identical
  new row too for consistency — **not explicitly required by this ticket's AC**, which only names
  `docs/guides/README.md`'s table; flagging as a possible but unconfirmed second edit site for the
  plan to decide on, not silently do or silently skip).
- **`docs/REGISTRY.yaml` regeneration is confirmed automatic** — CLAUDE.md states it is regenerated
  unconditionally at Finalize's post-migration self-check; no manual step is required beyond
  staging the regenerated file. `generate_registry.py`'s `_SKIP_DOC_SUBDIRS` (`generate_registry.py`
  ~line 40) excludes `archive`/`parity_ledger`/`scenarios`/`entity` — neither `docs/guides/` nor
  `docs/observability/` is in that skip set, so both new docs will be indexed automatically once
  they carry valid frontmatter (`type: doc` inferred from path, per
  `validate_frontmatter.py::detect_content_type`).
- **Frontend line-number citations in the new technical reference will drift** if any of the five
  source tickets' code changes again — this ticket's own Out of Scope forbids touching
  `src/`/`dashboard-frontend/src/`/`Makefile`, so the citations captured now are accurate as of this
  investigation's direct reads (line numbers given above for every cited file), but they are a
  point-in-time snapshot, not a live-generated reference. See Anti-Drift Hazards for how to phrase
  this so the doc doesn't read as more durable than it is.
- **No open question blocks implementation.** Every risk above is either a naming recommendation
  (file path) or an accurately-disclosed limitation (partial port-collision verification,
  `live_tail` phase/agent gap) that the new docs should describe honestly rather than something
  requiring a new decision before writing begins.

## Anti-Drift Hazards

- **Do not restate or duplicate `INFRA-275`/`INFRA-276`'s `v2_evidence` text** — the ticket's own AC
  requires citing by ID (`"see INFRA-275"`) instead. Reproducing their evidence paragraphs verbatim
  in the new docs creates two sources of truth that will drift independently the next time either
  parity entry is updated.
- **Do not edit `INFRA-275` or `INFRA-276`** — both explicitly exclude this ticket's scope in their
  own text, and this ticket's own Out of Scope forbids it; this is documentation-only work with no
  behavior change, so no parity-ledger status/`v2_evidence` update is due per the Authoritative
  Mechanics Rule's own trigger condition ("if logic changes").
- **Do not present the port table, route list, or file:line citations as self-maintaining.** They
  are accurate as of this investigation's direct reads of the current `main`-branch code but will
  silently go stale the next time any of the five source modules changes (none of which is
  frozen — they are DONE tickets, not immutable ones). The new docs should be written in a way that
  is easy to spot-check against source (cite file paths, avoid over-precise claims that don't
  survive a refactor) rather than embedding a false promise of permanence. This is a documentation
  authoring judgment call, not a technical guard this ticket can encode as a test — flag it in the
  doc's own text (e.g. "as of TCK-20260717-AGENTOPS-DASHBOARD-DOCS") rather than silently.
  Concretely: this is exactly why `docs/observability/read_model_service_contract.md` cites methods
  and files, not exact line numbers, in its own Contract table — the plan should follow that
  precedent for the technical reference's stable long-term content, while file:line citations (as
  captured in this investigation) are appropriate for this investigation.md itself, not necessarily
  for the durable doc.
- **Do not attempt to fix, work around, or silently soften the `live_tail` phase/agent
  null-labeling gap** while describing it — the new docs should state the honest current behavior
  (`RawToolCall` has no `phase`/`agent` field; the caption is unconditional) exactly as shipped, per
  the ticket's own Out of Scope. Do not word it as a bug needing a doc-side workaround.
- **Do not silently expand scope into `docs/guides/README.md`'s parent `docs/README.md`** (which
  has a duplicate guide table) without an explicit plan-phase decision — see Risks above. Editing
  it is a small, same-topic, low-risk consistency fix, but it is not named by this ticket's AC.
- **Do not place the technical reference under `docs/architecture/`** — the ticket's own Out of
  Scope is explicit that `docs/observability/<name>_contract.md` is the correct convention here,
  matching `read_model_service_contract.md` and all five source tickets' `layer: observability`.
- **Do not invent new documentation-generation tooling** (auto-extracted OpenAPI, etc.) — both new
  docs must be hand-authored markdown, per the ticket's own Out of Scope, consistent with every
  other file in `docs/guides/` and `docs/observability/`.
- **`git diff --stat` for this ticket must touch only `docs/`, `docs/REGISTRY.yaml`, and
  ticket/staging-artifact/monitoring paths** — no file under `src/`, `dashboard-frontend/src/`, or
  `Makefile` may be modified, per the ticket's own explicit AC. This investigation confirms no
  drift toward touching those paths is needed to satisfy any AC.
