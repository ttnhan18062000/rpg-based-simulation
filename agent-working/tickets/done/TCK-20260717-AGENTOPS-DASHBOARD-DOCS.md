---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-AGENTOPS-DASHBOARD-DOCS
phase: done
date: 2026-07-17
tags: [documentation, observability, api-design]
---

# TCK-20260717-AGENTOPS-DASHBOARD-DOCS

## Title
Agent Ops Dashboard documentation: user guide + technical reference

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Five DONE tickets (TCK-20260716-AGENTOPS-DASHBOARD-BACKEND, -ACTIVITY-GANTT, -REPLAY-TIMELINE,
-TICKETS-VIEW, -BUILD-SERVE) built the full agent-ops dashboard feature — a FastAPI backend over
tickets/ + agent-monitoring/, a React/Vite SPA with three views, and build/serve tooling — but the
only durable record of how it works lives scattered across five stored_artifacts/*/investigation.md
files and the two parity ledger entries (INFRA-275, INFRA-276). The author wants two hand-authored
docs written so future agent investigators and human developers don't have to re-derive that context:
(a) a `docs/guides/` user/developer-facing how-to guide, and (b) a detailed technical/architecture
reference covering the API contract, SPA structure, and hard design constraints (StaticFiles/main.py
isolation, port allocations, no-npm-at-runtime). This is documentation-only work — no source or
mechanics behavior changes.

## Scope
- Write `docs/guides/agent_ops_dashboard.md` (audience: developer), covering:
  - What the agent-ops dashboard is and what problem it solves (visual viewer over tickets/ +
    agent-monitoring/ data)
  - How to build/run/serve it: `make dashboard-install`, `make dashboard-build`,
    `make dashboard-dev` (backend on :8471 with `--reload` + Vite dev server, proxying `/api` to
    the backend — confirm actual Vite dev port from `dashboard-frontend/vite.config.ts` rather than
    assuming 5173, which is the unrelated main-app `dev` target's port), `make dashboard-serve`
    (single foreground process on :8420, depends on `dashboard-build`)
  - How to use each of the three views: Recent Activity Gantt (default landing view, solid bars =
    authoritative runs.jsonl, distinct fill = inferred-live), Replay Timeline (scrubbable
    phase/tool-call playback + files-touched panel for one run), Tickets view (filterable/sortable
    table, AND-across-dimensions/OR-within-tag filters, links to Replay Timeline)
  - Add a row for this guide to the table in `docs/guides/README.md`, matching the existing format
- Write a detailed technical/architecture reference in `docs/observability/` (matching the existing
  per-subsystem contract-doc convention set by `docs/observability/read_model_service_contract.md`,
  and matching the `layer: observability` value all five source tickets used), covering:
  - Backend API contract: all 5 routes in `src/api/agent_ops_dashboard/main.py` (GET /api/tickets,
    /api/runs, /api/runs/{run_id}, /api/runs/{run_id}/timeline, /api/health), their Pydantic
    response models in `models.py`, and relevant query params/filter semantics
  - `ingest.py`'s ownership of all file reads, the in-memory cache/RLock concurrency pattern, the
    ticket-to-run join (all matching rows, not first-match), and the `is_inferred_active`
    10-minute-window heuristic
  - Frontend SPA structure: `App.tsx`, `api.ts`, `views/` (RecentActivityGantt, ReplayTimelineView,
    TicketsView), `components/` (GanttBar, Legend, PlaybackScrubber) and how they consume the API
  - Hard design constraints future agents must not violate: `serve.py`'s StaticFiles mount must
    never be added to `main.py`'s own `app` object (regression-guarded by
    `test_main_mounts_no_static_files`); the full port allocation (8000 main app `serve`, 8420
    `dashboard-serve` production, 8471 `dashboard-dev` backend, the actual Vite dev port from
    `vite.config.ts`, 3000 Docusaurus `docs-serve`); `dashboard-serve` never invokes Node/npm at
    runtime (only `dashboard-install`/`dashboard-build`/`dashboard-dev` may)
  - Cite `docs/parity_ledger/infrastructure.yaml` entries INFRA-275 and INFRA-276 by ID for the
    verified evidence trail rather than restating or duplicating their `v2_evidence` text
- Regenerate `docs/REGISTRY.yaml` (`make docs-registry` or the automatic Finalize-phase regen) so
  both new docs are indexed, per CLAUDE.md's "if any files under docs/ were created or modified" rule

## Out of Scope
- Any change to `src/api/agent_ops_dashboard/*`, `dashboard-frontend/src/*`, or the `Makefile`
  `dashboard-*` targets themselves — all five source tickets are DONE and parity-verified
  (INFRA-275, INFRA-276); this ticket only documents existing, already-shipped behavior
- Modifying, re-verifying, or changing `status`/`v2_evidence` on the INFRA-275 / INFRA-276 parity
  ledger entries — cite them, do not touch them (no behavior changed, so no parity update is due)
- Fixing the known `live_tail` phase/agent null-labeling gap (MONITORING_INSTRUMENTATION_GAP),
  called out as out-of-scope in both AGENTOPS-ACTIVITY-GANTT and AGENTOPS-REPLAY-TIMELINE — the new
  docs may *describe* this as a known limitation but must not attempt to fix it
- Placing the technical reference under `docs/architecture/` — the repo's existing convention for a
  single subsystem's API/service contract doc is `docs/observability/<name>_contract.md`
  (`read_model_service_contract.md`), which this ticket follows instead
- Any new documentation-generation tooling (e.g., auto-extracted OpenAPI docs) — both docs are
  hand-authored markdown, consistent with every other file in `docs/guides/` and `docs/observability/`
- Correcting or re-deriving the actual dashboard-frontend dev port for any purpose other than
  documenting it accurately (verified as 5174 in `dashboard-frontend/vite.config.ts:18`, not 5173)

## Acceptance Criteria
- `docs/guides/agent_ops_dashboard.md` exists with frontmatter (`layer: observability`,
  `audience: developer`) and covers: what the dashboard is, all four `make dashboard-*` commands
  with correct ports, and a usage walkthrough for each of the three views
- `docs/guides/README.md`'s guide table includes a new row linking to
  `agent_ops_dashboard.md`, matching the existing row format
- A technical reference doc exists under `docs/observability/` with frontmatter
  (`layer: observability`, `audience: agent`) documenting: all 5 backend routes + their response
  models, `ingest.py`'s cache/join/inferred-active logic, the frontend SPA file structure, and the
  StaticFiles-isolation + port-allocation + no-npm-at-runtime constraints
- Both new docs explicitly cite parity ledger IDs INFRA-275 and INFRA-276 (e.g. "see INFRA-275")
  rather than reproducing their evidence text
- `python3 tools/validate_frontmatter.py` (or equivalent frontmatter check) passes on both new files
- `git diff --stat` for this ticket's changes touches only `docs/`, `docs/REGISTRY.yaml`, and
  ticket/staging-artifact/monitoring paths — no file under `src/`, `dashboard-frontend/src/`, or
  `Makefile` is modified
- `docs/REGISTRY.yaml` reflects both new docs after regeneration

## Related Tickets
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND (DONE) — backend API + ingest layer being documented
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT (DONE) — Recent Activity Gantt view being documented
- TCK-20260716-AGENTOPS-REPLAY-TIMELINE (DONE) — Replay Timeline view being documented
- TCK-20260716-AGENTOPS-TICKETS-VIEW (DONE) — Tickets view being documented
- TCK-20260716-AGENTOPS-BUILD-SERVE (DONE) — build/serve tooling being documented

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` — INFRA-275 (dashboard backend), INFRA-276 (build/serve)
- `docs/observability/read_model_service_contract.md` — convention model for the technical
  reference's format and frontmatter shape
- `docs/guides/README.md` — table this ticket adds a row to
- `docs/REGISTRY.yaml` — regenerated as part of this ticket's close

## Related Stored Artifacts
- `stored_artifacts/TCK-20260716-AGENTOPS-DASHBOARD-BACKEND/` (investigation.md, plan.md, test_plan.md)
- `stored_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/`
- `stored_artifacts/TCK-20260716-AGENTOPS-REPLAY-TIMELINE/`
- `stored_artifacts/TCK-20260716-AGENTOPS-TICKETS-VIEW/`
- `stored_artifacts/TCK-20260716-AGENTOPS-BUILD-SERVE/`

## Related Code Areas
- `src/api/agent_ops_dashboard/main.py`
- `src/api/agent_ops_dashboard/ingest.py`
- `src/api/agent_ops_dashboard/models.py`
- `src/api/agent_ops_dashboard/serve.py`
- `dashboard-frontend/src/App.tsx`
- `dashboard-frontend/src/api.ts`
- `dashboard-frontend/src/views/` (RecentActivityGantt.tsx, ReplayTimelineView.tsx, TicketsView.tsx)
- `dashboard-frontend/src/components/` (GanttBar.tsx, Legend.tsx, PlaybackScrubber.tsx)
- `dashboard-frontend/vite.config.ts`
- `Makefile` (dashboard-install/dashboard-build/dashboard-dev/dashboard-serve targets, read-only reference)

## Assumptions / Open Questions
- No conflicting or duplicate work found: `tickets/backlogs/` and `tickets/inprogress/` have no
  hits for `agent-ops-dashboard`/`agent_ops_dashboard`; this is a fresh scope, not a promotion of
  deprioritized work.
- This is pure documentation authoring, not a logic change, so the Authoritative Mechanics Rule's
  parity-ledger-update-on-behavior-change trigger does not apply — the two docs cite INFRA-275/276
  rather than editing them. If a reviewer decides prose-level doc drift itself warrants a parity
  ledger touch, that would be a scope addition.
- Assumes the technical reference belongs in `docs/observability/` (matching
  `read_model_service_contract.md`'s convention and all 5 source tickets' `layer: observability`)
  rather than `docs/architecture/`. If a reviewer prefers `docs/architecture/` instead, only the
  file's location changes, not its content or acceptance criteria.
- The request's mention of port "5173" is corrected to 5174 based on
  `dashboard-frontend/vite.config.ts:18` (`server.port: 5174`); 5173 is Vite's bare default and is
  also coincidentally close to the *main* app's unrelated `make dev` frontend port mentioned in
  `Makefile:30` — the docs must state the dashboard's actual port, not the request's number.
- Assumes `docs/guides/README.md`'s table-row-addition counts as part of this ticket's Scope (small,
  same-topic edit) rather than a separate ticket — consistent with how other guide additions in this
  repo update the README table in the same change.

## Implementation Notes
Followed `staging_artifacts/TCK-20260717-AGENTOPS-DASHBOARD-DOCS/plan.md`'s 5 steps exactly, no
deviations.

- **Step 1**: Wrote `docs/guides/agent_ops_dashboard.md` (frontmatter `layer: observability`,
  `audience: developer`, `authority: P1`, `status: active`, `tags: [documentation, observability,
  api-design]`). Covers what the dashboard is, a build/run/serve table for all four
  `make dashboard-*` targets with live-reverified ports, a usage walkthrough for each of the three
  views (Recent Activity Gantt, Replay Timeline, Tickets view), the honest `live_tail` known
  limitation, and a "See also" section citing `docs/observability/agent_ops_dashboard_contract.md`
  and INFRA-275/INFRA-276 by ID only.
- **Step 2**: Wrote `docs/observability/agent_ops_dashboard_contract.md` (frontmatter
  `layer: observability`, `audience: agent`, `authority: P1`, `status: active`, same tags),
  matching `read_model_service_contract.md`'s `## Purpose` / `## Contract` / `## Architecture Law`
  / `## Known Limitation` / `## Related` section shape. Documents all 5 backend routes + response
  models (by method/file name, never `file:line`), `ingest.py`'s cache/RLock/rebuild/join/
  inferred-active logic, the frontend SPA file structure (`App.tsx`, `api.ts`, `views/`,
  `components/`), and the three hard constraints (no StaticFiles in `main.py`, the 5-port
  allocation table, no npm/node at `dashboard-serve` runtime) tied to their real regression-test
  names. No `doc_id` field was added — sampled two other `docs/observability/` contract docs
  (`hard_law_monitor.md`, `decision_trace_contract.md`) and neither carries one; only
  `read_model_service_contract.md` does, so `doc_id` is not a hard convention across the directory
  and was omitted to avoid inventing an unused field.
- **Step 3**: Added one matching row to `docs/guides/README.md`'s table (after the
  `diagram_index.md` row) and one to `docs/README.md`'s "Developer Guides — `guides/`" table
  (after `guides/feature_flags.md`), each in that table's own existing link-format convention, per
  the plan's Decision 2. No other row in either table was touched — the two tables' pre-existing
  drift (three rows `docs/README.md` was already missing) was left alone, out of scope.
- **Step 4**: Ran `make docs-registry` (`python3 tools/generate_registry.py`) after Steps 1-3
  landed. `docs/REGISTRY.yaml` grew by 23 net insertions; both new doc paths now appear as
  `type: doc` entries. `python3 tools/generate_registry.py --check` confirms zero drift
  post-regeneration.
- **Step 5 (anti-drift verification pass)**: Ran and confirmed all 8 checks from the plan
  explicitly, not left implicit:
  1. `grep -nE '[A-Za-z_./-]+\.(py|ts|tsx|md):[0-9]+'` over both new docs — zero matches (no
     `file:line` citations in durable content).
  2. Re-verified all 5 ports live against source in this session (not carried forward from
     investigation.md): `8000` (`Makefile:33,38,46,49,85`), `8420`
     (`serve.py:25 DEFAULT_PORT`), `8471` (`Makefile:63`), `5174`
     (`dashboard-frontend/vite.config.ts:19`), `3000` (`Makefile:246`); `5173` appears in both new
     docs only as the disambiguating unrelated `frontend/` port, never as the dashboard's own.
  3. Confirmed live via grep: all four `dashboard-*` Makefile targets exist
     (`Makefile:53,56,59,67`); all 5 `@app.get(` routes exist in `main.py` (lines 29, 52, 63, 71,
     79); `serve.py` has `DEFAULT_PORT`, `StaticFiles`, and `include_router`.
  4. Confirmed live via grep: `test_main_mounts_no_static_files`
     (`tests/tools/test_agent_ops_dashboard_api_boundary.py:61`),
     `test_serve_module_has_no_node_npm_invocation`
     (`tests/tools/test_agent_ops_dashboard_serve.py:75`),
     `test_dashboard_serve_recipe_has_no_npm_or_node`
     (`tests/tools/test_dashboard_makefile_targets.py:91`) all exist as real `def test_...`
     functions and are cited by name in the contract doc.
  5. `grep -c "INFRA-275\|INFRA-276"` returns 2 for each new doc; grepped for any `v2_evidence`-only
     substrings (e.g. `L29`, `L361`, `L178`) in both new docs — zero matches, confirming no
     verbatim evidence-text reproduction.
  6. `git diff docs/parity_ledger/infrastructure.yaml` — empty, byte-unmodified.
  7. `git diff --stat` — touches only `docs/README.md`, `docs/REGISTRY.yaml`,
     `docs/guides/README.md`, and `agent-monitoring/tools.jsonl` (auto-updated monitoring log);
     plus new untracked files under `docs/guides/`, `docs/observability/`,
     `staging_artifacts/TCK-20260717-AGENTOPS-DASHBOARD-DOCS/`, and
     `tickets/inprogress/TCK-20260717-AGENTOPS-DASHBOARD-DOCS.md`. No `src/`,
     `dashboard-frontend/src/`, or `Makefile` path appears anywhere in the diff.
  8. Confirmed `docs/observability/agent_ops_dashboard_contract.md` is the actual path, not under
     `docs/architecture/`.

No conflicts or architectural issues surfaced during implementation. Both new files pass
`python3 tools/validate_frontmatter.py`.

## Test Summary
Documentation-only change; no source code or test files were touched. Verification consisted of:
- `python3 tools/validate_frontmatter.py docs/guides/agent_ops_dashboard.md` — OK, no violations.
- `python3 tools/validate_frontmatter.py docs/observability/agent_ops_dashboard_contract.md` — OK,
  no violations.
- `python3 tools/generate_registry.py --check` — in sync, zero drift.
- The 8-point anti-drift verification pass (Step 5 above) — all checks passed.
No existing test suite runs were required or applicable (no `src/` behavior changed).

## Files Changed
- `docs/guides/agent_ops_dashboard.md` (new)
- `docs/observability/agent_ops_dashboard_contract.md` (new)
- `docs/guides/README.md` (one row added)
- `docs/README.md` (one row added, matching table)
- `docs/REGISTRY.yaml` (regenerated, both new docs indexed)

## Completion Summary
Wrote a hand-authored user/developer guide (`docs/guides/agent_ops_dashboard.md`) and a
hand-authored technical/architecture reference (`docs/observability/agent_ops_dashboard_contract.md`)
documenting the already-shipped, already-parity-verified Agent Ops Dashboard (backend, three
frontend views, build/serve tooling) built by five prior DONE tickets. Both new docs cite
INFRA-275 and INFRA-276 by ID only, never reproducing their `v2_evidence` text, and use
method/file-name citations rather than `file:line` references to avoid documentation rot. Added
matching rows to both `docs/guides/README.md`'s and `docs/README.md`'s guide tables, and
regenerated `docs/REGISTRY.yaml` so both new docs are indexed. A first-class 8-point anti-drift
verification pass (ports, make targets, routes, test names, INFRA citations, parity-ledger
byte-unmodified, diff-scope guard, file-location guard) was run explicitly and all checks passed.
No source code, `Makefile`, or `docs/parity_ledger/infrastructure.yaml` content was touched;
`git diff --stat` confirms the change is scoped to `docs/` plus the expected ticket/monitoring
paths.
