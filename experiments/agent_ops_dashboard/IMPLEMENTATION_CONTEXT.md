# Implementation Context — reuse inventory, exact schemas, open verification items

**Status:** research reference, not a design or a ticket — companion to `PROPOSAL.md` and
`MONITORING_INSTRUMENTATION_GAP.md`
**Purpose:** everything a follow-on agent needs to write an implementation plan and file tickets
without re-deriving what this investigation already found.
**Date:** 2026-07-16

---

## 1. Reusable code — confirmed by direct read, ranked by relevance

| Code | What it does | How this dashboard should use it |
|---|---|---|
| `tools/validate_frontmatter.py::extract_frontmatter(text)` (L64) | The canonical, already-battle-tested ticket/doc frontmatter parser — a hand-rolled YAML-subset parser (not a full YAML library), returns a dict or raises `ValueError` on bad syntax. | **Reuse directly, don't reimplement.** Every ticket `.md` file's frontmatter (`status`, `layer`, `tier`, `tags`, etc.) should be parsed with this exact function so the dashboard's notion of "valid frontmatter" never silently diverges from what `validate_frontmatter.py`'s own CI-enforced rules consider valid. |
| `tools/agent-monitoring/query.py::load_jsonl(path)` | Trivial but exact-pattern `Path.read_text().splitlines()` → `json.loads` per line, skipping blanks. Used as the base for all of `query.py`'s filters. | Mirror this exact loader in `ingest.py` (or import it) — it's already the established convention for reading these specific JSONL files, and matches `validate.py`'s own reading style. |
| `tools/agent-monitoring/validate.py` | Legacy-schema tolerance: `LEGACY_COMPLETION_FIELDS`, `LEGACY_TERMINAL_STATUS_VALUES` allowlists for the 5-6 documented historical `runs.jsonl` generations (see `docs/agent-monitoring/schema.md`'s "Known Limitations"). | **Import/reuse these allowlists**, don't re-derive the legacy-schema tolerance rules from scratch — this was already audited exhaustively (`TCK-20260705-MONITORING-RUNID-JOIN`, 107/107 residual "incomplete" runs confirmed genuinely complete). |
| `docs/agent-monitoring/schema.md`'s own join example (in the "Join Example" section) | Shows the exact `events_by_run` / `tools_by_event` dict-of-lists join pattern by `run_id` and `(run_id, seq)`. | This is the reference join `ingest.py`'s `/api/runs/{run_id}/timeline` endpoint should implement — already demonstrated correct, not a new algorithm to invent. |
| `src/observability/reporting/history_query.py::HistoricalRunQueryService` (`list_historical_runs(limit, offset)`, `get_run_manifest(run_id)`) + `src/api/routes/history.py` | A live, working precedent for exactly this dashboard's `/api/runs` (list, paginated) and `/api/runs/{run_id}` (detail) shape: `Query(default=50, ge=1, le=100)` pagination, `response_model=List[dict]`/`response_model=dict`, `HTTPException(400/404/500)` handling. | Mirror this structure for the Agent Ops Dashboard's own endpoints — same param names, same error-handling shape, same repo convention. |
| `tools/generate_registry.py::collect_tickets()` (L246) | The function that walks `tickets/done/` (only) and produces the `type: ticket` entries in `docs/REGISTRY.yaml`, using `parse_body_section()`/`parse_h1_title()`/`_strip_frontmatter()` helpers. | **Do not depend on this for the Tickets view** — see §2's schema-gap finding below. Worth reading for its body-section-parsing helpers (`parse_related_code_areas()` etc.) if the dashboard ever wants to surface `Related Code Areas` per ticket, but the primary ticket data source should be direct frontmatter parsing (via `extract_frontmatter`), not `REGISTRY.yaml`. |
| `src/api/server.py`'s embedded dashboard (~L272-2364), esp. `loadEntityTimeline()` (L2297) and `startPollingLoops()`/`pollTelemetryAndHealth()` (L1636) | See `PROPOSAL.md` §5a — a full working precedent for tab navigation, a vertical timeline renderer, polling-loop wiring, and (in `src/api/ws/stream.py`) a WebSocket streaming pattern with backpressure/heartbeat/reconnect handling. | Read in full before starting frontend implementation, regardless of which stack option (§5a's vanilla-HTML vs. React/Vite) is chosen — the interaction patterns (tab switching, filter pills, JSON detail drawers, timeline rendering) are proven UI/UX decisions worth mirroring even in a React rebuild. |

---

## 2. Exact schemas confirmed — and one real gap found

### `tickets/working_log.csv`

Columns, confirmed by header + sample row: `timestamp, ticket_id, title, status, summary,
artifacts_path`. Plain CSV, parseable with Python's stdlib `csv` module — no custom parser needed.
This is the source for ticket completion timestamps/summaries the Tickets view and any
velocity-style rollup would use.

### `docs/REGISTRY.yaml` — confirmed real gap for this dashboard's needs

Doc-type entries (`type: doc`) carry: `path, title, status, layer, authority, audience, tags,
last_verified`.

Ticket-type entries (`type: ticket`) carry a **different, narrower field set**, confirmed by
reading a full real entry (not a truncated sample): `path, ticket_id, title, tier, ticket_type,
date, related_code_areas, artifact_files, tags`. **Notably absent: `status`, `layer`, `priority`.**
These are exactly three of the four filter dimensions `PROPOSAL.md`'s Tickets view design calls for
(tier/layer/status/priority) — `tier` and `tags` are present, `layer`/`status`/`priority` are not.

**Also confirmed: `REGISTRY.yaml` only ever contains `tickets/done/` tickets** (regenerated
unconditionally at ticket close, per this repo's Finalize workflow step) — `tickets/inprogress/`
and `tickets/todos/` tickets never appear here at all, at any time.

**Conclusion, so the next agent doesn't reach for `REGISTRY.yaml` as the ticket data source and hit
this gap mid-implementation:** `ingest.py` should parse ticket frontmatter **directly** from every
`.md` file under `tickets/inprogress/`, `tickets/done/`, and `tickets/todos/` using
`extract_frontmatter()` (§1), uniformly, regardless of lifecycle state. `REGISTRY.yaml` is not a
viable single source of truth for this dashboard's Tickets view — it was designed for a different
purpose (a flat index of closed, tagged work for later semantic search), not as a live
multi-dimensional filter source over ticket lifecycle state.

### `agent-monitoring/{runs,events,tools}.jsonl`

Already fully documented in `docs/agent-monitoring/schema.md` — see `PROPOSAL.md`'s citations. Not
repeated here; that doc is the authoritative reference and should be read directly, not
paraphrased twice.

---

## 3. Scale, as of this investigation (2026-07-16)

- `agent-monitoring/runs.jsonl`: 617 lines
- `agent-monitoring/events.jsonl`: 2,981 lines
- `agent-monitoring/tools.jsonl`: 54,876 lines
- `tickets/done/`: ~1,046 `.md` files (per `docs/guides/ticket_reporting.md`'s own live snapshot)

These numbers will keep growing. Re-confirm scale before finalizing the in-memory-cache-vs-SQLite
decision (`PROPOSAL.md` §3) if a large gap in time has passed since this document was written —
the recommendation was made against these specific numbers, not as a timeless conclusion.

---

## 4. Tooling, ports, and CI — quick reference (full evidence in `PROPOSAL.md` §5b)

| Item | Value | Notes |
|---|---|---|
| Ports in use | `8000` (sim backend), `5173` (sim frontend dev/Vite), `3000` (Docusaurus) | Dashboard needs a distinct port, e.g. `8420`, configurable via `--port` matching `python3 -m src serve --port`'s existing flag style |
| `frontend/` stack (if SPA option chosen) | React `^19.2.0`, Vite `^7.2.4`, TypeScript `~5.9.3`, Tailwind CSS `^4.1.18`, Radix UI primitives, `lucide-react` icons, Vitest `^4.0.18` + Testing Library | Confirmed via `frontend/package.json` — match these versions/libraries for consistency rather than picking different ones |
| Makefile pattern to mirror | `install`→`build`→`dev`→`serve`, e.g. `dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve` | Use distinct target names — `install`/`build`/`dev`/`serve` already mean the sim engine's own frontend |
| Process management | Plain foreground process (`make dashboard-serve`, Ctrl-C to stop) | Not Docker Compose — that stack exists for genuine multi-service coordination (Redis/RabbitMQ/Kafka) the dashboard doesn't need |
| Backend test location (once past `experiments/`) | `tests/tools/` | Confirmed real + CI-gated: `.github/workflows/test.yml`'s "API / tools / logging" job runs `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability` |
| Frontend CI coverage | **None exists today** for `frontend/` (lint/typecheck/vitest all defined as npm scripts, none wired into `.github/workflows/test.yml`) | Do not assume the SPA option comes with free CI enforcement — it would need new CI steps |
| `experiments/` CI exposure | None — confirmed by reading `test.yml` in full; it only runs `tests/` paths and `make lane-*`/`gate-expansion` | The current prototype/proposal work is correctly untested by CI as-is |

---

## 5. Open verification items for the next agent — not resolved here

- **Confirm the §5a/§5b three-way stack decision** (vanilla embedded HTML/CSS/JS; a new standalone
  FastAPI + React/Vite SPA; or a new view inside the existing `frontend/` app) with the user before
  writing any frontend code — this reopens a decision already made once in this investigation, on
  new evidence, twice, and deserves explicit re-confirmation, not a silent default in any direction.
- **Full read of `tools/generate_registry.py`'s `parse_related_code_areas()` and related helpers**
  if the dashboard ever wants a "Related Code Areas" column — not required for v1 scope, not
  investigated in depth here.
- **Whether `agent-monitoring/*.jsonl` files are ever subject to retention/rotation** — confirmed
  `data/runs/`'s chunked simulation artifacts have a `RetentionPolicy`/`RetentionManager`
  (`src/observability/reporting/retention.py`, cited in the sibling `placement_integrity`
  proposal), but whether the same or a different retention rule applies to
  `agent-monitoring/*.jsonl` itself was **not checked** in this investigation — worth confirming
  before assuming these files grow unbounded forever (relevant to the in-memory cache's long-term
  memory footprint).
- **Whether `MONITORING_INSTRUMENTATION_GAP.md`'s proposed fix should land before, after, or
  independent of the dashboard's own implementation** — `PROPOSAL.md` §8 states the dashboard does
  not depend on it, but the actual sequencing (does the dashboard ticket block on it, or can they
  run as sibling tickets) is a planning decision, not made here.

---

## Related

- `experiments/agent_ops_dashboard/PROPOSAL.md` — the main design document this context supports
- `experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md` — the companion instrumentation-gap investigation
- `experiments/agent_ops_dashboard/DATA_MODEL.md` — builds directly on this document's §1 reuse table and §2 schema-gap finding (sharpened further there: `tier`/`ticket_type`/`priority`/workflow-status are body-section fields, never frontmatter, for any ticket)
- `experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md`, `TEST_PLAN.md` — consume this document's reuse inventory and scale figures
- `docs/agent-monitoring/schema.md` — authoritative schema reference, not duplicated here
- `docs/guides/ticket_reporting.md` — confirms the ~1,046-file `tickets/done/` scale figure used in §3
