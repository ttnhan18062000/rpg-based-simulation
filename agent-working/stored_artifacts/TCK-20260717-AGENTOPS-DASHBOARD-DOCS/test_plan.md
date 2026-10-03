---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-AGENTOPS-DASHBOARD-DOCS
artifact_type: test_plan
tags: [documentation, observability, api-design]
---

# Test Plan — TCK-20260717-AGENTOPS-DASHBOARD-DOCS

## Regression Surface

This ticket adds no source code (`src/`, `dashboard-frontend/src/`, `Makefile` are all explicitly
Out of Scope) — there is no application regression surface to protect. The regression surface that
*is* relevant is the tooling that validates and indexes `docs/`, plus a confirmation that the five
already-shipped source tickets' own test suites are untouched by this ticket's diff.

**Unit / doc-validation (must pass on the two new files):**
- `python3 tools/validate_frontmatter.py docs/guides/agent_ops_dashboard.md` — frontmatter schema
  check (required keys, `STATUS_VALUES`/`LAYER_VALUES`/`AUTHORITY_VALUES`/`AUDIENCE_VALUES` enum
  membership per `tools/validate_frontmatter.py:44-52`; `content_type` inferred as `doc` from the
  `docs/` path per `detect_content_type`).
- `python3 tools/validate_frontmatter.py docs/observability/<technical-reference-file>.md` — same
  check, second file.
- `python3 tools/generate_registry.py --check` — confirms the regenerated `docs/REGISTRY.yaml`
  (post-ticket) is in sync with a fresh regeneration; exits 2 if the checked-in file drifts from
  what a fresh run produces, exits 1 if any doc file is missing frontmatter (this would also catch
  a missing-frontmatter regression in either new file, redundantly with the validate_frontmatter.py
  check above).

**Integration (existing suites that must stay green, confirming this ticket did not silently touch
code):**
- `git diff --stat` — must show changes confined to `docs/`, `docs/REGISTRY.yaml`, and
  ticket/staging-artifact/monitoring paths (`tickets/`, `staging_artifacts/`→`stored_artifacts/`,
  `agent-monitoring/`) per the ticket's own AC. No file under `src/api/agent_ops_dashboard/`,
  `dashboard-frontend/src/`, or `Makefile` may appear in the diff.
- `pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"`
  — the full backend/build-serve regression suite from `INFRA-275`/`INFRA-276`'s own `test_path`
  fields, run only to *confirm* it is unaffected (a pass with zero diff to any of those source
  files is the expected, boring outcome — not evidence this ticket did anything to those suites).
- `cd dashboard-frontend && npm test` — the frontend Vitest suite, same "confirm unaffected"
  purpose.

**Arena-combat:** not applicable — this ticket has no combat/simulation-mechanics surface (per
investigation.md's Mechanics/Engine Constraints section, confirmed none apply).

## New Tests Required

There is no executable behavior for this ticket to unit-test — the "tests" here are documentation
correctness checks mapped to the ticket's Acceptance Criteria. None require new pytest/Vitest test
*functions* beyond what's listed above; they are verification steps against the two new files'
content.

- **Frontmatter validity — both new files**
  Category: doc-validation (via `tools/validate_frontmatter.py`, not a new test function)
  Verifies: `docs/guides/agent_ops_dashboard.md` has `layer: observability`, `audience: developer`;
  the technical reference doc has `layer: observability`, `audience: agent`; both pass schema
  validation with no missing required keys.
  Where: run against the two files directly, no new test file needed (the tool itself is the test).

- **`docs/guides/README.md` table row added**
  Category: doc-validation (manual/grep check, not a new pytest function)
  Verifies: a new `| [agent_ops_dashboard.md](agent_ops_dashboard.md) | ... |` row exists, matching
  the existing 9-row table's exact `| Guide | What it covers |` format (per
  `docs/guides/README.md:12-23`).
  Where: `docs/guides/README.md` itself — verified by direct read/grep at Verify, not an automated
  test (no existing test enforces this table's contents; none should be added just for this row,
  per the "hand-authored markdown, no new tooling" Out of Scope bullet).

- **All four `make dashboard-*` commands documented with correct ports**
  Category: doc-content correctness (manual cross-check against source, not a new automated test)
  Verifies: the guide states `dashboard-install`, `dashboard-build`, `dashboard-dev` (backend
  `:8471` with `--reload` + Vite dev server on `:5174`, confirmed
  `dashboard-frontend/vite.config.ts:19`), `dashboard-serve` (foreground process on `:8420`,
  `dashboard-build` prerequisite) — cross-checked against `Makefile:53-68` and `vite.config.ts:19`
  directly, not against the ticket's own inbound "5173" framing (already corrected in the ticket's
  Assumptions section).
  Where: `docs/guides/agent_ops_dashboard.md`.

- **Usage walkthrough for each of the three views present**
  Category: doc-content correctness
  Verifies: Recent Activity Gantt (default landing, solid = authoritative, distinct fill =
  inferred-active), Replay Timeline (scrub/play + files-touched panel), Tickets (filter/sort,
  AND-across-dimensions/OR-within-tag, links to Replay) are each described accurately against the
  real shipped components (`RecentActivityGantt.tsx`, `ReplayTimelineView.tsx`, `TicketsView.tsx`).
  Where: `docs/guides/agent_ops_dashboard.md`.

- **All 5 backend routes + response models documented**
  Category: doc-content correctness
  Verifies: the technical reference lists `GET /api/tickets`, `/api/runs`, `/api/runs/{run_id}`,
  `/api/runs/{run_id}/timeline`, `/api/health` with their real query params (per `main.py:29-81`)
  and response models (per `models.py:17-96`), not a stale/idealized version.
  Where: `docs/observability/<technical-reference-file>.md`.

- **`ingest.py`'s cache/join/inferred-active logic documented**
  Category: doc-content correctness
  Verifies: RLock-per-method pattern, ticket-to-run join (all matches, not first-match), and the
  `ACTIVE_WINDOW_MINUTES=10` heuristic are described matching `ingest.py:348-446` (cache),
  `ingest.py:178-199` (join), `ingest.py:234-256` (inferred-active) exactly.
  Where: `docs/observability/<technical-reference-file>.md`.

- **Frontend SPA structure documented**
  Category: doc-content correctness
  Verifies: `App.tsx`, `api.ts`, `views/` (three files), `components/` (three files) are named and
  their roles described accurately, matching the real file list under `dashboard-frontend/src/`.
  Where: `docs/observability/<technical-reference-file>.md`.

- **Hard design constraints documented**
  Category: doc-content correctness (this is the highest-value content in the technical reference —
  it is the one section future implementers are most likely to violate without a doc)
  Verifies: `serve.py`'s StaticFiles-mount-must-never-be-in-`main.py` constraint (citing
  `test_main_mounts_no_static_files` by name), the full 5-port allocation table, and the
  Node/npm-never-at-`dashboard-serve`-runtime constraint are all stated, each traceable to a real
  regression test (`test_main_mounts_no_static_files`,
  `test_serve_module_has_no_node_npm_invocation`, `test_dashboard_serve_recipe_has_no_npm_or_node`).
  Where: `docs/observability/<technical-reference-file>.md`.

- **`INFRA-275`/`INFRA-276` cited by ID, not restated**
  Category: doc-content correctness / anti-drift
  Verifies: both new docs contain a literal `INFRA-275` and/or `INFRA-276` reference string, and
  neither reproduces either entry's full `v2_evidence` paragraph verbatim.
  Where: both new files — checkable by grep at Verify (`grep -c "INFRA-275\|INFRA-276" <file>`
  returns >0 for at least one ID per file, and the file does not contain a copy-pasted multi-line
  block matching either entry's `v2_evidence` text).

## Scoped Pytest Commands

```
python3 tools/validate_frontmatter.py docs/guides/agent_ops_dashboard.md
python3 tools/validate_frontmatter.py docs/observability/<technical-reference-file>.md
python3 tools/generate_registry.py --check
```

Regression-confirmation only (expected to pass unchanged — a failure here would indicate this
ticket accidentally touched code, not docs):

```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

```
cd dashboard-frontend && npm test
```

Never `pytest tests/` — no reason exists to broaden beyond the above; this ticket's scope has no
relationship to any other test domain in the repo.

## Anti-Drift Test Guards

- **`git diff --stat` scope guard** — confirm at Verify that no path under `src/`,
  `dashboard-frontend/src/`, or `Makefile` appears in the diff. This is the single most important
  guard for a documentation-only ticket: it is the mechanical proof that "documentation-only, no
  source or mechanics behavior changes" (the ticket's own Request Summary) actually held, rather
  than trusting the ticket description alone.
- **`INFRA-275`/`INFRA-276` byte-unmodified guard** — `git diff docs/parity_ledger/infrastructure.yaml`
  must be empty. Both entries explicitly exclude this ticket's scope in their own text and this
  ticket's Out of Scope forbids editing them; a diff here would mean the ticket silently expanded
  into re-verifying parity it was told not to touch.
- **No stale port number guard** — grep both new docs for the literal string `5173` in a context
  implying it is the dashboard-frontend's own dev port (as opposed to a deliberate contrast
  sentence distinguishing it from `frontend/`'s unrelated port, which is legitimate and expected).
  The ticket's own Out of Scope explicitly calls out this exact failure mode ("Correcting or
  re-deriving the actual dashboard-frontend dev port for any purpose other than documenting it
  accurately") — the real value is `5174` (`vite.config.ts:19`), and a doc that states `5173` as
  the dashboard's own port would be the specific regression this ticket exists to prevent.
- **Technical reference location guard** — confirm the new technical/architecture reference file
  lands under `docs/observability/`, not `docs/architecture/` (grep the final `git diff --stat`
  output for the file path). The ticket's Out of Scope is explicit that `docs/architecture/` is the
  wrong location for this content.
- **No parity-evidence duplication guard** — grep both new docs for a run of 3+ consecutive lines
  matching `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275`/`INFRA-276` `v2_evidence` text
  verbatim; none should be found. Citation-by-ID only.
- **`docs/REGISTRY.yaml` indexing guard** — after regeneration, grep the regenerated file for both
  new doc paths (`docs/guides/agent_ops_dashboard.md`, `docs/observability/<technical-reference-file>.md`)
  and confirm both appear as `type: doc` entries. A missing entry would mean the new file's
  frontmatter is malformed or the file landed under a skipped subdirectory
  (`_SKIP_DOC_SUBDIRS = {"archive", "parity_ledger", "scenarios", "entity"}` in
  `tools/generate_registry.py`) — neither `docs/guides/` nor `docs/observability/` should ever hit
  that skip set, so a miss here is a real signal something is wrong, not a false positive to
  ignore.
