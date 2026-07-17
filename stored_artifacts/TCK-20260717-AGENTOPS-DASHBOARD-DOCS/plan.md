---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-AGENTOPS-DASHBOARD-DOCS
artifact_type: plan
tags: [documentation, observability, api-design]
---

# Implementation Plan — TCK-20260717-AGENTOPS-DASHBOARD-DOCS

## Summary

This is a documentation-only ticket: write two hand-authored markdown docs describing the
already-shipped, already-parity-verified agent-ops dashboard (backend + three frontend views +
build/serve tooling), wire them into the two guide-table indexes, and regenerate
`docs/REGISTRY.yaml`. No source file under `src/`, `dashboard-frontend/src/`, or `Makefile` is
touched, and neither `INFRA-275` nor `INFRA-276` is edited — both are cited by ID only. The plan
resolves the investigation's three open questions as concrete decisions (technical reference
filename, whether to update `docs/README.md`'s duplicate table, and file:line vs.
method/file-name citation style) and adds an explicit, first-class anti-drift verification step
so this ticket does not repeat the sibling-ticket pattern of a `DOD_BLOCKED` Verify result for
skipping guard work.

**Decisions locked in (from the ticket's own Acceptance Criteria text and the investigation's
recommendations):**

1. Technical reference file: `docs/observability/agent_ops_dashboard_contract.md` — mirrors
   `read_model_service_contract.md`'s naming exactly.
2. `docs/README.md` has its own copy of the guide table at `docs/README.md:198-211` (section
   "Developer Guides — `guides/`"), confirmed by direct read to already differ in format
   (link paths prefixed `guides/`, and it is currently missing three rows present in
   `docs/guides/README.md` — `ticket_tagging.md`, `ticket_reporting.md`, `diagram_index.md` —
   i.e. it has already drifted once). The ticket's AC text names only
   `docs/guides/README.md`'s table as required. Decision: update **both** tables in the same
   step, for consistency and to avoid adding a second, fresher instance of the exact staleness
   this investigation already caught — this is a small, same-topic, low-risk addition, not a
   scope expansion, and each table keeps its own existing row-format convention (bare filename
   link in `docs/guides/README.md`, `guides/`-prefixed link in `docs/README.md`).
3. The technical reference's durable "Contract"-style tables (routes, cache/ingest methods,
   frontend file structure, constraints) cite **method and file names only**, never `file:line`
   — matching `read_model_service_contract.md`'s own Contract table precedent. `file:line`
   citations are appropriate only in this ticket's own `investigation.md` (already written, not
   re-touched by this plan), not in the durable doc.

## Steps

### Step 1 — Draft the user/developer guide
**Files:** `docs/guides/agent_ops_dashboard.md` (new)
**Change:** Write a new guide with frontmatter `layer: observability`, `audience: developer`,
`authority: P1` (matching the other rows' typical authority in `docs/guides/`), `status: active`,
`tags: [documentation, observability, api-design]` (all three already registered in
`docs/guidelines/tag_registry.jsonl` — confirmed, no new tag registration needed). Content
sections, in order:
- **What it is** — a read-only visual viewer over `tickets/` and `agent-monitoring/*.jsonl`
  data; not a source of truth, purely presentational (no `AuthoritativeState`, no mutation).
- **Build / run / serve** — a table or list of the four `make dashboard-*` targets with their
  **confirmed-live** ports (re-verified by direct read in this session, not carried forward
  from investigation.md unverified):
  - `make dashboard-install` — `cd dashboard-frontend && npm install` (`Makefile:53-54`)
  - `make dashboard-build` — `cd dashboard-frontend && npm run build` (`Makefile:56-57`)
  - `make dashboard-dev` — backend `uvicorn src.api.agent_ops_dashboard.main:app --host
    127.0.0.1 --port 8471 --reload` concurrent with the Vite dev server on port `5174`
    (`Makefile:59-65`; Vite port confirmed at `dashboard-frontend/vite.config.ts` — `server.port:
    5174`, not the `frontend/` main-app's unrelated `5173`)
  - `make dashboard-serve` — depends on `dashboard-build`; single foreground process,
    `python3 -m src.api.agent_ops_dashboard.serve`, on port `8420` (`Makefile:67-68`,
    `serve.py`'s `DEFAULT_PORT = 8420`)
  - State explicitly that the main simulation API's own `make serve` runs on a separate port,
    `8000` (`Makefile:38,46,49,85`), and Docusaurus `make docs-serve` runs on `3000`
    (`Makefile:246`) — both listed only to disambiguate, not because this guide covers them.
- **Using the three views** — one subsection each:
  - Recent Activity Gantt (default landing view; solid bars = authoritative `runs.jsonl` rows,
    a visually distinct fill = inferred-live rows still in progress; row click navigates to
    Replay Timeline for that run)
  - Replay Timeline (scrubbable phase/tool-call playback for one run, files-touched panel;
    honestly caption unfinished/live runs as "phase unknown — run still in progress" rather than
    guessing — this is the known, described-not-fixed `live_tail` limitation, see below)
  - Tickets view (filterable/sortable table; single-select filters for tier/layer/status/priority,
    multi-select for tags; AND across dimensions, OR within tag selections; links each row's
    matching runs to Replay Timeline)
- **Known limitation** — one short paragraph stating that live (in-progress) tool-call rows have
  no `phase`/`agent` label yet (tracked separately as `MONITORING_INSTRUMENTATION_GAP`); state
  this as accurate current behavior, not as something this doc fixes or works around.
- **See also** — link to `docs/observability/agent_ops_dashboard_contract.md` for the technical
  reference, and cite `INFRA-275`/`INFRA-276` (e.g. "see INFRA-275, INFRA-276 in
  `docs/parity_ledger/infrastructure.yaml`") for the verified evidence trail — do not reproduce
  either entry's `v2_evidence` text.
**Do NOT touch:** any file under `src/api/agent_ops_dashboard/`, `dashboard-frontend/src/`,
`vite.config.ts`, or `Makefile` — read-only references only. Do not add a `phase`/`agent` field
description implying it exists on `RawToolCall` (it does not).
**Verify:** `python3 tools/validate_frontmatter.py docs/guides/agent_ops_dashboard.md`; manual
content check against test_plan.md's "All four `make dashboard-*` commands documented with
correct ports" and "Usage walkthrough for each of the three views present" items.

### Step 2 — Draft the technical/architecture reference
**Files:** `docs/observability/agent_ops_dashboard_contract.md` (new)
**Change:** Write a new contract-style doc matching `read_model_service_contract.md`'s shape
(`doc_id`, `title`, `layer: observability`, `authority: P1`, `audience: agent`, `status: active`,
`date`, `tags: [documentation, observability, api-design]`, then `## Purpose` / `## Contract` /
`## Architecture Law` / `## Violation Guard` / `## Related` sections). Content, by
method/file-name citation (never `file:line`):
- **Purpose** — one paragraph: standalone FastAPI backend (`src/api/agent_ops_dashboard/main.py`)
  serving read-only projections over `tickets/` and `agent-monitoring/` for the dashboard SPA;
  never touches `AuthoritativeState` or the tick loop.
- **Contract table (backend routes)** — one row per route, matching a `Method | Returns |
  Params | Backing` shape like `read_model_service_contract.md`'s own table:
  `GET /api/tickets` (`TicketSummary` list; params `tier`, `layer`, `status`, `priority`,
  repeatable `tag`, `lifecycle`, `q`, `sort`), `GET /api/runs` (`RunSummary` list; `limit`,
  `offset`, `status`, `workflow`, `since`), `GET /api/runs/{run_id}` (`RunDetail`, 404 on miss),
  `GET /api/runs/{run_id}/timeline` (`RunTimeline`, 404 on miss), `GET /api/health`
  (`HealthStatus`). Cite `main.py` and `models.py` by name only.
- **Ingest / cache section** — describe (by method name, not line number): `DashboardCache`'s
  single `threading.RLock` guarding every public method; `_maybe_rebuild`/`_rebuild` re-running
  the full parse+join+inference pipeline under that lock on any source `mtime` change;
  `build_matching_runs` returning **all** matching `runs.jsonl` rows per ticket (never
  first-match, sorted `start_ts` descending); `compute_inferred_active`'s
  `ACTIVE_WINDOW_MINUTES = 10` heuristic (a `tools.jsonl`-present, `runs.jsonl`-absent run whose
  latest tool-call timestamp is within the window is `is_inferred_active`, recomputed fresh every
  rebuild); the `status` (frontmatter lifecycle) vs. `workflow_status` (body `## Status`)
  distinction as two separate, never-conflated fields.
- **Frontend SPA structure** — list `App.tsx` (view-switch state, no router library),
  `api.ts` (typed fetch helpers + `useRunsPolling`), `views/` (`RecentActivityGantt.tsx`,
  `ReplayTimelineView.tsx`, `TicketsView.tsx`), `components/` (`GanttBar.tsx`, `Legend.tsx`,
  `PlaybackScrubber.tsx`), one line each on role and how it consumes the API — by file name only.
- **Architecture Law / hard constraints section** — the three constraints the ticket calls out,
  each tied to its real regression-test name (not a line number):
  - `serve.py` builds a *separate* `FastAPI()` instance and mounts `StaticFiles` there — the
    mount must never appear inside `main.py`'s own `app` object, guarded by
    `test_main_mounts_no_static_files` (`tests/tools/test_agent_ops_dashboard_api_boundary.py`).
  - Full port allocation table (re-verified live in this session): `8000` main app `make serve`,
    `8420` `dashboard-serve` production (`serve.py`'s `DEFAULT_PORT`), `8471` `dashboard-dev`'s
    backend half (`--reload`), `5174` `dashboard-frontend`'s Vite dev server
    (`vite.config.ts`'s `server.port`), `3000` Docusaurus `docs-serve`. State `5173` only as a
    disambiguating contrast (`frontend/`'s unrelated main-app dev port), never as the dashboard's
    own port.
  - `dashboard-serve` never invokes Node/npm at runtime — guarded by
    `test_serve_module_has_no_node_npm_invocation`
    (`tests/tools/test_agent_ops_dashboard_serve.py`) and
    `test_dashboard_serve_recipe_has_no_npm_or_node`
    (`tests/tools/test_dashboard_makefile_targets.py`); only `dashboard-install`,
    `dashboard-build`, and `dashboard-dev` invoke `npm`.
- **Known limitation** — same honest `live_tail` phase/agent gap statement as Step 1's guide
  (`RawToolCall` has no `phase`/`agent` field at all, not merely nullable); do not propose a fix.
- **Related** — cite `INFRA-275` (backend: routes, ingest, cache, join, inferred-active
  heuristic) and `INFRA-276` (serve.py design, Makefile targets) by ID only, one line each,
  pointing at `docs/parity_ledger/infrastructure.yaml`; do not quote either entry's
  `v2_evidence` paragraph.
**Do NOT touch:** `docs/parity_ledger/infrastructure.yaml` itself (cite, never edit); do not
place this file under `docs/architecture/`; do not invent an OpenAPI-extraction tool — hand-author
only, matching every other file in `docs/observability/`.
**Verify:** `python3 tools/validate_frontmatter.py docs/observability/agent_ops_dashboard_contract.md`;
manual content check against test_plan.md's "All 5 backend routes...", "`ingest.py`'s
cache/join/inferred-active logic documented", "Frontend SPA structure documented", and "Hard
design constraints documented" items.

### Step 3 — Add guide-table rows
**Files:** `docs/guides/README.md`, `docs/README.md`
**Change:**
- In `docs/guides/README.md`, append one row to the existing 9-row table (after the
  `diagram_index.md` row, `docs/guides/README.md:23`), matching its exact format
  (`| [agent_ops_dashboard.md](agent_ops_dashboard.md) | <one-line summary: "Agent ops
  dashboard: build/serve, Gantt/Replay/Tickets views, API + design constraints"> |`).
- In `docs/README.md`'s own "Developer Guides — `guides/`" table (`docs/README.md:202-211`),
  append the matching row in *that* table's own format (link prefixed `guides/`:
  `| [guides/agent_ops_dashboard.md](guides/agent_ops_dashboard.md) | <same one-line summary> |`),
  per Decision 2 above. Do not otherwise reconcile the two tables' pre-existing drift (the three
  rows `docs/README.md` is already missing relative to `docs/guides/README.md`) — that is a
  separate, pre-existing gap out of this ticket's scope; only add this ticket's own new row to
  both.
**Do NOT touch:** any other row in either table; do not restructure either table into categories;
do not touch `docs/README.md`'s other sections (Docs/Tickets/Artifacts/Archive site description,
etc.).
**Verify:** `grep -n "agent_ops_dashboard" docs/guides/README.md docs/README.md` shows one new
row in each, each matching its table's existing format exactly (test_plan.md's "`docs/guides/README.md`
table row added" item, extended per Decision 2 to also cover `docs/README.md`).

### Step 4 — Regenerate the doc registry
**Files:** `docs/REGISTRY.yaml`
**Change:** Run `make docs-registry` (or `python3 tools/generate_registry.py`) after Steps 1–3
land, so both new docs are indexed as `type: doc` entries. This step must run *after* Steps 1 and
2 so both new files already carry valid, final frontmatter when the registry is built — running
it earlier would index incomplete drafts or fail if frontmatter isn't yet valid.
**Do NOT touch:** Any other entry in `docs/REGISTRY.yaml`; do not hand-edit the YAML — regenerate
only, per the "regeneration is automatic/mechanical" note in CLAUDE.md and investigation.md.
**Verify:** `python3 tools/generate_registry.py --check` exits 0 (no drift between checked-in
file and a fresh run); `grep -n "agent_ops_dashboard" docs/REGISTRY.yaml` shows both new doc
paths present as `type: doc` entries (test_plan.md's "`docs/REGISTRY.yaml` indexing guard").

### Step 5 — Anti-drift verification pass
**Files:** none changed; read-only verification against Steps 1–4's output and current source
**Change:** This is a first-class, mandatory verification step — not optional cleanup — run
after Steps 1–4 and before this ticket is handed to Verify. Perform each check and fix any
failure by revising the relevant doc from Steps 1–3 (do not silently skip a failing check):
1. **No `file:line` citations in durable content.** Grep both new docs for a `:<digits>` pattern
   immediately following a filename (e.g. `main.py:29`) in prose outside a fenced code block; none
   should appear — method/file names only, per Decision 3. (`investigation.md`'s own citations are
   exempt; this check targets only the two new docs.)
2. **Port numbers re-confirmed against live source, not copied blindly from investigation.md.**
   Re-verify in this step (do not just trust the earlier investigation): `8000` —
   `Makefile:38,46,49,85` (`python3 -m src serve --port 8000`); `8420` — `serve.py`'s
   `DEFAULT_PORT = 8420`; `8471` — `Makefile:63` (`uvicorn ... --port 8471 --reload`); `5174` —
   `dashboard-frontend/vite.config.ts`'s `server.port: 5174`; `3000` — `Makefile:246`
   (`docs-serve: ... Docusaurus dev server (http://localhost:3000)`); `5173` appears only as
   `frontend/`'s unrelated main-app dev port (`Makefile:30`), never as the dashboard's own port,
   in both new docs.
3. **Named make targets and routes actually exist.** Grep `Makefile` for `dashboard-install:`,
   `dashboard-build:`, `dashboard-dev:`, `dashboard-serve:` (all four present, confirmed
   `Makefile:53,56,59,67`); grep `src/api/agent_ops_dashboard/main.py` for the five `@app.get(`
   route decorators cited in Step 2 (confirmed present at `main.py:29,52,63,71,79`); grep
   `serve.py` for `DEFAULT_PORT` and the `StaticFiles`/`include_router` pattern.
4. **Test names cited actually exist.** Confirm `test_main_mounts_no_static_files`,
   `test_serve_module_has_no_node_npm_invocation`, `test_dashboard_serve_recipe_has_no_npm_or_node`
   are real `def test_...` functions in the files Step 2 cites (already confirmed present at
   `tests/tools/test_agent_ops_dashboard_api_boundary.py:61`,
   `tests/tools/test_agent_ops_dashboard_serve.py:75`,
   `tests/tools/test_dashboard_makefile_targets.py:91` — re-grep to confirm no drift since).
5. **`INFRA-275`/`INFRA-276` cited, not reproduced.** `grep -c "INFRA-275\|INFRA-276"` on both
   new docs returns > 0 for at least one ID per doc; confirm no 3+ consecutive lines matching
   either entry's `v2_evidence` text appear in either new doc.
6. **Parity ledger byte-unmodified.** `git diff docs/parity_ledger/infrastructure.yaml` is empty.
7. **Diff scope guard.** `git diff --stat` for this ticket touches only `docs/`,
   `docs/REGISTRY.yaml`, and ticket/staging-artifact/monitoring paths — no `src/`,
   `dashboard-frontend/src/`, or `Makefile` path appears.
8. **Technical reference location guard.** Confirm the new file path is
   `docs/observability/agent_ops_dashboard_contract.md`, not under `docs/architecture/`.
**Do NOT touch:** no source file is edited by this step; if a check fails, the fix is a doc-text
revision in Steps 1–3's files, not a source-code change.
**Verify:** all 8 checks above pass; this step's own completion *is* the test_plan.md's Anti-Drift
Test Guards section (git diff scope guard, INFRA byte-unmodified guard, no-stale-port guard,
technical reference location guard, no-parity-evidence-duplication guard, REGISTRY.yaml indexing
guard) run explicitly rather than left implicit.

## Scope Guards

- Do not edit `docs/parity_ledger/infrastructure.yaml` (`INFRA-275`, `INFRA-276`) — cite by ID
  only, in both new docs.
- Do not edit any of the five source tickets' `stored_artifacts/TCK-20260716-AGENTOPS-*/` files.
- Do not touch `src/api/agent_ops_dashboard/*` (any of `main.py`, `ingest.py`, `models.py`,
  `serve.py`).
- Do not touch `dashboard-frontend/src/*` (any `.tsx`/`.ts` file) or `dashboard-frontend/vite.config.ts`.
- Do not touch `Makefile`'s `dashboard-*` targets (read-only reference for documentation content
  only).
- Do not place the technical reference under `docs/architecture/`.
- Do not attempt to fix, soften, or work around the `live_tail` phase/agent null-labeling gap —
  describe it as-is.
- Do not add any documentation-generation tooling (OpenAPI auto-extraction, etc.) — both docs are
  hand-authored markdown.
- Do not reconcile `docs/README.md`'s pre-existing missing rows (`ticket_tagging.md`,
  `ticket_reporting.md`, `diagram_index.md`) — out of this ticket's scope; only this ticket's own
  new row is added to both tables.
- Do not register new tags — `documentation`, `observability`, `api-design` are already present
  in `docs/guidelines/tag_registry.jsonl`.

## Dependency Map

- Step 1 and Step 2 are independent of each other (different files, different content) and can be
  done in either order.
- Step 3 depends on Step 1 (needs the guide's final filename/summary to link to) but not on
  Step 2.
- Step 4 depends on Steps 1, 2, and 3 all being complete with valid frontmatter — registry
  regeneration must run after the docs exist and their content (including the guide-table rows)
  is final.
- Step 5 depends on Steps 1–4 all being complete — it is a verification pass over their combined
  output plus a live re-check against current source, and is the last step before handoff to
  Verify.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `docs/guides/agent_ops_dashboard.md` exists with correct frontmatter and covers what the dashboard is, all four `make dashboard-*` commands with correct ports, and a usage walkthrough for each view | Step 1 | `validate_frontmatter.py docs/guides/agent_ops_dashboard.md`; Step 5 checks 2–3 |
| `docs/guides/README.md`'s table includes a new row | Step 3 | `grep` check in Step 3 |
| Technical reference exists under `docs/observability/` with correct frontmatter, documenting all 5 routes + response models, `ingest.py`'s cache/join/inferred-active logic, frontend SPA structure, and the three hard constraints | Step 2 | `validate_frontmatter.py docs/observability/agent_ops_dashboard_contract.md`; Step 5 checks 3–4, 8 |
| Both new docs cite `INFRA-275`/`INFRA-276` by ID, not reproduced evidence text | Steps 1, 2 | Step 5 check 5 |
| `validate_frontmatter.py` passes on both new files | Steps 1, 2 | Direct tool run, Step 1/2 Verify lines |
| `git diff --stat` touches only `docs/`, `docs/REGISTRY.yaml`, and ticket/staging-artifact/monitoring paths | Steps 1–4 (no source touched at any step) | Step 5 check 7 |
| `docs/REGISTRY.yaml` reflects both new docs after regeneration | Step 4 | `generate_registry.py --check`; Step 4 Verify grep |

## Anti-Drift Notes

- The port table and file/route citations are accurate as of this session's direct re-verification
  (Step 5, check 2–4) — not merely carried forward from `investigation.md`. Both new docs should
  read as a snapshot ("as of TCK-20260717-AGENTOPS-DASHBOARD-DOCS") rather than implying
  self-maintaining permanence, per the investigation's Anti-Drift Hazards section.
- Every prior sibling ticket in this batch (`AGENTOPS-ACTIVITY-GANTT` most notably) hit a
  `DOD_BLOCKED` Verify result specifically from skipping anti-drift guard work in the same pass as
  the main content. Step 5 exists precisely to prevent that recurrence here — it is not optional
  and must not be deferred to a follow-up pass.
- `RawToolCall` genuinely has no `phase`/`agent` field (confirmed by the source ticket's own
  investigation, not merely nullable) — both new docs must describe the `live_tail` caption as
  unconditional honest behavior, never as a bug this ticket's docs paper over or half-fix in
  wording.
- `status`/`workflow_status` on `TicketSummary` are two distinct, never-conflated fields — do not
  collapse this distinction when describing the ticket-filter semantics in Step 2.
- The Tickets view's column sort for non-date dimensions is a **client-side** re-order over an
  already-fetched array (the backend `sort` param is date-only) — Step 1's usage walkthrough and
  Step 2's route documentation must both reflect this accurately, not describe sorting as fully
  server-side.
