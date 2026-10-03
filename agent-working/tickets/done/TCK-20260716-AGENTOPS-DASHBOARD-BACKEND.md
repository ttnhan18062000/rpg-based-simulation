---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
phase: done
date: 2026-07-16
tags: [api-design]
---

# TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Title
Backend API + ingest layer over tickets and agent-monitoring data

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a FastAPI backend (main.py, ingest.py, models.py) exposing /api/tickets, /api/runs, /api/runs/{run_id}, /api/runs/{run_id}/timeline, and /api/health, returning only Pydantic schemas. ingest.py should own all file reads, rebuild an in-memory cache on mtime change, and reuse existing legacy-schema tolerance and frontmatter-parsing utilities rather than reimplementing them. It must correctly join tickets to runs (all matching runs.jsonl rows, not just the first) and be safely concurrent, since this is the shared foundation the three frontend views in this batch all depend on.

## Scope
- Create a new FastAPI app (main.py) exposing GET /api/tickets, GET /api/runs, GET /api/runs/{run_id}, GET /api/runs/{run_id}/timeline, GET /api/health
- Create ingest.py owning all file reads: parse frontmatter+body sections directly across tickets/inprogress/, tickets/done/, tickets/todos/ (docs/REGISTRY.yaml is not used as a source); load agent-monitoring runs.jsonl/tools.jsonl/events.jsonl reusing validate.py's legacy allowlists
- Create models.py with typed Pydantic response models for every route (e.g. TicketSummary, RunSummary, RunTimeline) — no raw dict/domain-object payloads
- Implement an in-memory cache rebuilt on file mtime change, reusing src/api/read_model_cache.py's RLock-per-method concurrency pattern
- Implement the ticket-to-run join returning all matching runs.jsonl rows for a ticket_id (not just the first), sorted start_ts descending
- Implement is_inferred_active computation (ACTIVE_WINDOW_MINUTES=10 default) for runs present in tools.jsonl but absent from runs_by_id
- Implement files_touched derivation for /api/runs/{run_id}/timeline: deduplicated-by-path from tool_calls[].input_summary restricted to Read/Edit/Write/MultiEdit

## Out of Scope
- Any frontend component or view (TicketsView, RecentActivityGantt, ReplayTimelineView — owned by AGENTOPS-TICKETS-VIEW, AGENTOPS-ACTIVITY-GANTT, AGENTOPS-REPLAY-TIMELINE)
- Build/serve tooling, Makefile targets, or static-file packaging (owned by AGENTOPS-BUILD-SERVE)
- Fixing the live phase/agent null-labeling gap (independent sibling ticket)
- Retention/rotation policy for agent-monitoring/*.jsonl

## Acceptance Criteria
- [ ] All 5 routes declare typed Pydantic response models (e.g. response_model=List[TicketSummary]) returning typed instances, never raw dict/domain-object payloads — src/api/routes/history.py's List[dict]+.model_dump() pattern is explicitly not mirrored
- [ ] For a ticket_id with N>1 matching runs.jsonl rows (43/618 confirmed in current data), /api/tickets' matching_runs field contains all N rows sorted start_ts descending, not collapsed to one
- [ ] ingest.py imports and calls extract_frontmatter(), load_jsonl(), and validate.py's legacy allowlists rather than reimplementing parsing logic
- [ ] Concurrent requests during a cache rebuild never observe a partially-rebuilt structure, verified via a concurrency test using an RLock-per-method pattern matching ReadModelCache's exact locking approach
- [ ] GET /api/runs/{run_id} returns 404 (not 500 or an empty 200) when run_id matches neither runs_by_id nor the inferred-active set
- [ ] A ticket missing '## Tier'/'## Priority'/'## Type' body sections surfaces those fields as null in the response, not an error or placeholder value
- [ ] A run_id present in tools.jsonl within ACTIVE_WINDOW_MINUTES=10 and absent from runs_by_id returns is_inferred_active=true with inferred_start_ts taken from the first tools.jsonl timestamp for that run
- [ ] On completion, is_inferred_active flips true->false and start_ts/end_ts switch to authoritative values; no request ever observes a completed run still flagged active

## Related Tickets
- TCK-20260518-READ-MODEL-CACHE
- TCK-20260705-MONITORING-RUNID-JOIN

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_ops_dashboard.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- docs/agent-monitoring/schema.md
- docs/guidelines/design_patterns.md
- docs/observability/read_model_service_contract.md
- docs/engine/architecture_reference.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/validate.py
- tools/generate_registry.py
- src/api/read_model_cache.py
- src/observability/reporting/history_query.py
- src/api/routes/history.py
- src/api/routes/health.py
- src/observability/reporting/retention.py
- docs/agent-monitoring/schema.md
- experiments/agent_ops_dashboard/PROPOSAL.md
- experiments/agent_ops_dashboard/DATA_MODEL.md
- experiments/agent_ops_dashboard/IMPLEMENTATION_CONTEXT.md
- expected: src/api/agent_ops_dashboard/main.py
- expected: src/api/agent_ops_dashboard/ingest.py
- expected: src/api/agent_ops_dashboard/models.py

## Assumptions / Open Questions
- src/api/routes/health.py exists but is currently empty (0 lines), so /api/health's shape must be derived from PROPOSAL.md §6 alone with no existing pattern to mirror
- docs/REGISTRY.yaml is confirmed not viable as the tickets data source since it only covers tickets/done/ and omits status/layer/priority; frontmatter+body must be parsed directly across all 3 lifecycle directories
- agent-monitoring/*.jsonl has no retention/rotation policy; unbounded growth is a known risk not addressed in this ticket
- live_tail phase/agent will remain null until the independent sibling fix lands; accepted as a known limitation, not a bug in this ticket's scope

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260716-AGENTOPS-DASHBOARD-BACKEND/plan.md`'s 9 steps, in order:

- **`models.py`**: all 9 typed Pydantic response models (`RunMatchSummary`, `TicketSummary`, `RawToolCall`, `FileTouch`, `TimelineEntry`, `RunSummary`, `RunDetail`, `RunTimeline`, `HealthStatus`), using `Field(default_factory=list)` for mutable list defaults (this repo's established convention — 248 existing uses vs. bare `= []`).
- **`ingest.py`** (`parse_ticket_file`, `walk_ticket_dirs`, `lifecycle_state_for_path`): reuses `extract_frontmatter`/`parse_body_section`/`parse_h1_title`/`_strip_frontmatter` verbatim via the plan's prescribed `sys.path` wiring. Empty `parse_body_section` results are converted to `None`, never a placeholder. `walk_ticket_dirs` filters every candidate to `TCK-\d{8}-*.md` before parsing, so `SEQUENCE.md`/other non-ticket files under `tickets/todos/{folder}/` never reach `extract_frontmatter`.
- **`load_jsonl_counted`**: wraps `validate.load_jsonl` (the tolerant loader, object-identity-asserted in tests, never `query.py`'s crashing one) and derives the skipped-line count by diffing total non-blank lines against the valid-record count, so the parsing behavior itself is never duplicated.
- **`build_matching_runs`**: returns every `runs.jsonl` row for a `ticket_id`, sorted `start_ts` descending with `None`/missing `start_ts` rows always sorted last (never first, never a crash).
- **`compute_inferred_active`**: `ACTIVE_WINDOW_MINUTES = 10`; a `run_id` seen in `tools.jsonl` but absent from `runs_by_id`, whose max `ts` is within the window of an injected `now`, is inferred active with `inferred_start_ts` set to the first (min) `ts`. Recomputed fresh every rebuild — never carried over — so a completing run atomically drops out of the set on the same rebuild pass.
- **`extract_files_touched`**: dedups by path across `entries[].tool_calls` + `live_tail`, restricted to `Read`/`Edit`/`Write`/`MultiEdit`, keeping the first `ts`+`tool` seen per path.
- **`DashboardCache`**: single `threading.RLock()` guarding every public method (`get_tickets`, `get_runs`, `get_run`, `get_timeline`, `get_health`) and the internal `_maybe_rebuild`/`_rebuild`, matching `ReadModelCache`'s exact per-method-lock pattern — rebuild-in-place under one lock, not the swap-based alternative. Rebuild triggers on any of the 4 watched sources' mtime change (`runs.jsonl`, `events.jsonl`, `tools.jsonl`, a count+mtime-sum over all ticket files).
- **`main.py`**: standalone `FastAPI()` app (not mounted on `src/api/server.py`), 5 routes each with an explicit `response_model=` from `models.py`, returning constructed typed instances directly — never `.model_dump()`, never `dict`. `GET /api/runs/{run_id}` and `/timeline` raise `HTTPException(404)` when the cache's `get_run`/`get_timeline` return `None`. No `StaticFiles` mount.
- **`docs/parity_ledger/infrastructure.yaml`**: added `INFRA-275` after `INFRA-274`, `status: verified`, `test_path` pointing at the 4 new test files (all passing at close).

**Real-data-driven fixes beyond the plan's explicit steps** (discovered by smoke-testing against the live `agent-monitoring/*.jsonl` + `tickets/**` corpus before writing tests — not deviations from the plan's design, but necessary robustness the plan didn't anticipate):
- A minority of `runs.jsonl` rows (`FOLDER-*`/`EPIC-*` legacy batch wrappers) carry `start_ts`/`end_ts` as raw unix-epoch `int`/`float` instead of ISO strings. Added `_coerce_ts()` to normalize every timestamp field feeding a `str`-typed model field (`RunSummary`, `RunMatchSummary`, `TimelineEntry`, `RawToolCall`, `FileTouch`) — without it, `pydantic.ValidationError` crashed `GET /api/runs` against real data.
- `_resolve_final_status()` extended to fall back to `validate._record_is_complete(rec)` (checking `LEGACY_COMPLETION_FIELDS`) when neither `final_status` nor `status` is present, so the `ts_start`/`ts_end`/`result` legacy generation resolves to `DONE` rather than a misleading default `IN_PROGRESS`.
- `_LIFECYCLE_PRIORITY` (`inprogress` > `done` > `todos`) added to `DashboardCache._rebuild`'s ticket-collection loop: this ticket's own file exists simultaneously under both `tickets/inprogress/` and `tickets/todos/agent-ops-dashboard/` right now (the `todos` source is only deleted at Finalize, per CLAUDE.md's Workflow Rule) — without an explicit precedence, insertion order silently picked whichever directory was walked last.

## Test Summary

29 new tests added across 4 files, all passing:
- `tests/tools/test_agent_ops_dashboard_ingest.py` (18 tests) — ticket parsing/null-body-sections, ticket-run join (all-matches-sorted-desc, `None` sorts last), reuse-identity assertions, inferred-active (window + boundary + exclusion), AC #8 completion flip, files_touched dedup, legacy schema tolerance, malformed-JSONL counting.
- `tests/tools/test_agent_ops_dashboard_api.py` (5 tests) — 404 for unknown `run_id`/timeline, 200 for known run, malformed-JSONL surfaced in `/api/health`'s `unparsed_lines`, `/api/health` `status` always `"ok"`.
- `tests/tools/test_agent_ops_dashboard_concurrency.py` (2 tests) — real `threading.Thread`-based: no reader observes a torn rebuild (verified via a single `get_run()` call reading ticket+run state together, with an injected `parse_ticket_file` delay to widen the race window deterministically), and AC #8's active→completed flip is atomic under concurrent reads.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` (5 tests) — every route's `response_model` is a real Pydantic class (never `dict`/`List[dict]`), all 5 routes declared, no `StaticFiles` mount, no write-path (`.write_text`/`.write_bytes`/`.open`) anywhere in the module, no import of the workflow orchestrator.

Regression suite (reused code, unmodified): `tests/tools/test_add_frontmatter_{tickets,live,archive}.py`, `test_generate_registry.py`, `test_record_run.py`, `test_record_events.py`, `test_cost_proxy.py`, `test_current_run_sidecar_orchestrator.py` — 292/292 passed. `tests/api/test_paged_logic.py` + `tests/architecture/test_api_read_model_guard.py` passed; `tests/api/test_rest_parity.py` failed on a pre-existing, unrelated `ConnectionRefusedError` against its own subprocess-spawned uvicorn server on port 8002 — confirmed unrelated to this ticket (that test only exercises `src/api/server.py`'s main simulation API, never imports `agent_ops_dashboard`).

## Files Changed

- `src/api/agent_ops_dashboard/__init__.py` (new)
- `src/api/agent_ops_dashboard/models.py` (new)
- `src/api/agent_ops_dashboard/ingest.py` (new)
- `src/api/agent_ops_dashboard/main.py` (new)
- `tests/tools/test_agent_ops_dashboard_ingest.py` (new)
- `tests/tools/test_agent_ops_dashboard_api.py` (new)
- `tests/tools/test_agent_ops_dashboard_concurrency.py` (new)
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (added `INFRA-275`)
- `graphify-out/` (regenerated via `graphify update .`)

## Completion Summary

All 9 plan steps implemented and all 8 acceptance criteria covered by passing tests. Backend is a standalone, read-only FastAPI app over `tickets/**` + `agent-monitoring/*.jsonl`, returning only typed Pydantic response models, with an `RLock`-per-method in-memory cache rebuilt on source mtime change. No frontend, build/serve tooling, or write path was added, per Out of Scope. Verified end-to-end against the live repo's real `tickets/`/`agent-monitoring/` data via manual smoke test (all 5 routes) in addition to the fixture-based test suite.
