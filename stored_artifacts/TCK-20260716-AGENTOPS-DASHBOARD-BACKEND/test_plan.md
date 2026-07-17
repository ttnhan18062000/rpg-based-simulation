---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
artifact_type: test_plan
tags: [agent-monitoring, api-design, observability]
---

# Test Plan — TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Regression Surface

No existing test file imports or exercises anything under `src/api/agent_ops_dashboard/` (it does
not exist yet), so there is no direct regression surface for the new module itself. The
regression surface here is the **reused code** this ticket must not break or fork silently:

**Unit — reused parsing/allowlist code (must keep passing unmodified):**
- `tests/tools/test_add_frontmatter_tickets.py`, `test_add_frontmatter_live.py`,
  `test_add_frontmatter_archive.py` — exercise `extract_frontmatter()` and
  `detect_content_type()` behavior `ingest.py` depends on being stable.
- `tests/tools/test_generate_registry.py` — exercises `parse_body_section()`, `parse_h1_title()`,
  `parse_related_code_areas()`, `_strip_frontmatter()` (the exact functions `ingest.py` reuses
  for `title`/`tier`/`ticket_type`/`priority`/`workflow_status`).
- `tests/tools/test_record_run.py`, `test_record_events.py` — exercise the write side of
  `runs.jsonl`/`events.jsonl`; confirms the schema `ingest.py`'s read side must stay compatible
  with.
- `tests/tools/test_cost_proxy.py` — confirms `cost_proxy_score` field semantics `TimelineEntry`
  passes through unchanged.
- `tests/tools/test_current_run_sidecar_orchestrator.py` — confirms the `tools.jsonl`
  `run_id`/`seq` attribution mechanism `ingest.py`'s `tools_by_seq`/`tools_by_run_recent` joins
  depend on.

**Integration — sibling API surface (confirms no accidental collision/regression):**
- `tests/api/test_rest_parity.py`, `tests/api/test_paged_logic.py` — existing REST pagination
  conventions (`Query(default=50, ge=1, le=100)`) this ticket's `/api/runs` must match, not
  diverge from.
- `tests/architecture/test_api_read_model_guard.py` — must keep passing untouched; confirms this
  ticket does not accidentally import `AuthoritativeState`/`EntityState` into any file it adds
  (even though the guard's scanned path set does not currently include
  `src/api/agent_ops_dashboard/`, the new code must still not need to import them).

**Root frontmatter/registry validation (must keep passing since this ticket adds new `.md`
staging artifacts and, eventually, a ticket file under `tickets/`):**
- `tests/tools/test_generate_registry.py`, `tests/tools/test_doc_staleness_check.py` — confirm
  the new ticket file and staging artifacts don't break registry generation or staleness checks.

## New Tests Required

Per AC, one entry per required new test (backend Python tests land in `tests/tools/` per
`IMPLEMENTATION_CONTEXT.md` §4's confirmed CI-gated location — the "API / tools / logging" job in
`.github/workflows/test.yml` runs `pytest tests/api tests/cli tests/tools tests/logging
tests/engine tests/observability -m "not slow"`):

1. **`test_typed_response_models_not_dict`**
   - Category: architecture guard / unit
   - Verifies: every route in `src/api/agent_ops_dashboard/main.py` declares a `response_model`
     that is a `models.py` Pydantic class (or `List[...]` of one) — never `dict`/`List[dict]`.
     Can be implemented as a static AST/introspection check (mirroring
     `tests/architecture/test_api_read_model_guard.py`'s scan-the-file-tree style) or as a runtime
     check via `app.routes[i].response_model` introspection. Directly tests AC #1.
   - Location: `tests/tools/test_agent_ops_dashboard_api_boundary.py`

2. **`test_ticket_run_join_returns_all_matches_sorted_desc`**
   - Category: unit
   - Verifies: given a fixture `runs.jsonl` with N>1 rows sharing one `run_id`/`ticket_id`,
     `ingest.py`'s join returns all N as `matching_runs`, sorted `start_ts` descending — not
     collapsed to one. Directly tests AC #2 (the 43/618 collision case).
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

3. **`test_ingest_reuses_extract_frontmatter_and_validate_allowlists`**
   - Category: unit / reuse-verification
   - Verifies: `ingest.py` module actually imports `extract_frontmatter` from
     `tools/validate_frontmatter.py` and `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES`
     (or the tolerant `load_jsonl`) from `tools/agent-monitoring/validate.py`, rather than
     reimplementing equivalent logic inline — assert via `inspect`/import introspection that the
     same function objects are used (`ingest.extract_frontmatter is
     validate_frontmatter.extract_frontmatter`), not just behaviorally similar output. Directly
     tests AC #3.
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

4. **`test_concurrent_requests_never_observe_partial_rebuild`**
   - Category: integration / concurrency
   - Verifies: spawn N threads issuing reads against the cache while one thread triggers a
     rebuild (e.g. touch a fixture file's mtime mid-test); assert every read sees either the
     fully-old or fully-new snapshot, never a state where e.g. `runs_by_id` reflects new data but
     `tickets_by_id` still reflects old data (or vice versa). Use a fixture with an injected delay
     in one parse step to widen the race window deterministically rather than relying on real
     timing luck. Directly tests AC #4, and must exercise the exact `RLock`-per-method pattern
     (not merely assert a lock object exists).
   - Location: `tests/tools/test_agent_ops_dashboard_concurrency.py`

5. **`test_run_detail_404_for_unknown_run_id`**
   - Category: integration (FastAPI `TestClient`)
   - Verifies: `GET /api/runs/{run_id}` returns exactly 404 (not 500, not empty 200) for a
     `run_id` present in neither `runs_by_id` nor the inferred-active set. Directly tests AC #5.
   - Location: `tests/tools/test_agent_ops_dashboard_api.py`

6. **`test_ticket_missing_body_sections_surfaces_null_not_error`**
   - Category: unit
   - Verifies: a fixture ticket file with valid frontmatter but no `## Tier`/`## Priority`/
     `## Type` body sections parses to a `TicketSummary` with `tier=None`/`priority=None`/
     `ticket_type=None` (matching `DATA_MODEL.md` §1's nullability table) rather than raising or
     defaulting to a placeholder string. This is `TEST_PLAN.md` row 9's "data-quality signal,"
     explicitly flagged in the idea doc's Open Questions as worth its own assertion. Directly
     tests AC #6.
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

7. **`test_inferred_active_run_from_tools_jsonl_tail`**
   - Category: unit
   - Verifies: a fixture `tools.jsonl` with rows for a `run_id` absent from `runs_by_id`, all
     timestamped within `ACTIVE_WINDOW_MINUTES=10` of "now," produces
     `RunSummary(is_inferred_active=True, inferred_start_ts=<first tools.jsonl ts for that
     run_id>)`. Include a companion case with timestamps just past the 10-minute boundary to
     confirm the run does NOT appear inferred-active (boundary test). Directly tests AC #7.
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

8. **`test_active_run_completion_flips_inferred_flag_and_timestamps`**
   - Category: integration / state-transition
   - Verifies: starting from a fixture state where a run is inferred-active
     (`tools.jsonl` tail only), then adding a completing `runs.jsonl` row and triggering a
     rebuild, confirms `is_inferred_active` flips `True → False` and `start_ts`/`end_ts` switch
     from the inferred/absent values to the authoritative `runs.jsonl` values, atomically (no
     intermediate observed state has both `is_inferred_active=True` and a populated authoritative
     `end_ts`). Directly tests AC #8 — pair with concurrency test #4 to also assert this holds
     under concurrent reads during the transition.
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

9. **`test_files_touched_dedup_by_path_restricted_to_edit_tools`**
   - Category: unit
   - Verifies: `files_touched` derivation from a fixture with mixed `tool` values
     (`Read`, `Edit`, `Write`, `MultiEdit`, `Bash`, `Agent`) only includes the first four,
     deduplicated by path (keeping first `ts`+`tool` per path per `DATA_MODEL.md` §3's pseudocode
     comment). Directly tests the Scope bullet "Implement files_touched derivation ... restricted
     to Read/Edit/Write/MultiEdit."
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

10. **`test_legacy_runs_jsonl_schema_generations_do_not_crash_ingest`**
    - Category: unit / regression-prone-path
    - Verifies: a fixture `runs.jsonl` containing at least 2-3 of `docs/agent-monitoring/schema.md`'s
      documented legacy shapes (`started_at`/`finished_at`; `ts_start`/`ts_end`/`result`;
      `FOLDER-*` bare `status`) parses without raising and produces reasonable `RunSummary`
      values (`final_status` resolved from whichever field is present), mirroring
      `PROPOSAL.md` §9's stated testing philosophy for `ingest.py`'s join logic.
    - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

11. **`test_malformed_jsonl_line_skipped_and_counted_in_health`**
    - Category: unit / failure-mode
    - Verifies: a fixture file with one unparseable JSON line does not crash the cache rebuild;
      the line is skipped and counted in `/api/health`'s `unparsed_lines` dict for the
      corresponding source file. Resolves the `load_jsonl` ambiguity flagged in
      `investigation.md`'s Risks section by asserting the required tolerant behavior directly,
      regardless of which underlying loader implementation is chosen.
    - Location: `tests/tools/test_agent_ops_dashboard_api.py`

12. **`test_non_ticket_markdown_in_tickets_dirs_does_not_crash_ingest`**
    - Category: unit / edge case
    - Verifies: a fixture `tickets/todos/{folder}/` containing a `SEQUENCE.md`-style non-ticket
      file alongside real `TCK-*.md` ticket files does not crash frontmatter parsing — either by
      filename-pattern filtering or graceful per-file error handling. Covers the gap named in
      `investigation.md`'s Risks section (not explicit in any of the three source design docs).
    - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py -v

# Regression surface for reused code:
pytest tests/tools/test_add_frontmatter_tickets.py tests/tools/test_add_frontmatter_live.py tests/tools/test_add_frontmatter_archive.py tests/tools/test_generate_registry.py tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py -m "not slow"

# Sibling API convention + architecture guard regression:
pytest tests/api/test_rest_parity.py tests/api/test_paged_logic.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

Never run the full `pytest tests/` — scoped to `tests/tools/` (new + reused tooling tests),
`tests/api/` (REST convention regression), and `tests/architecture/` (API-boundary guard), per
`CLAUDE.md`'s Testing Rule.

## Anti-Drift Test Guards

- **`test_ticket_run_join_returns_all_matches_sorted_desc`** (test #2) is the primary guard
  against the single most heavily-negotiated decision in this ticket's design trail (43/618
  collision rate) — any future refactor that "simplifies" the join back to first-match-wins must
  fail this test immediately.
- **`test_ingest_reuses_extract_frontmatter_and_validate_allowlists`** (test #3) guards against
  silent reimplementation drift — a common failure mode where a developer copies the logic
  instead of importing it, which then silently diverges from `validate_frontmatter.py`'s
  CI-enforced rules over time. Asserting object identity (not just behavioral equivalence) makes
  this guard resistant to a "looks the same today" false pass.
- **`test_concurrent_requests_never_observe_partial_rebuild`** (test #4) guards against a
  regression toward the naive "mutate structures one at a time" implementation `DATA_MODEL.md`
  §4 explicitly warns is a real correctness bug under FastAPI's async concurrency model — this
  is the test that would catch someone "optimizing" the rebuild into a non-atomic form later.
- **`test_active_run_completion_flips_inferred_flag_and_timestamps`** (test #8) guards the
  Recent Activity view's (a sibling ticket's) core correctness assumption — if this drifts, the
  frontend Gantt view would render a completed run as still-live, a visible and confusing bug for
  the next ticket in this batch, not just an internal inconsistency.
- **A guard test asserting `main.py` mounts no `StaticFiles`/frontend-serving route** would catch
  scope creep from `AGENTOPS-BUILD-SERVE`'s territory landing early in this ticket — worth adding
  if the plan phase decides to formalize the Out-of-Scope boundary as a test rather than relying
  on review alone.
- **A guard test asserting `src/api/agent_ops_dashboard/` never imports anything from
  `.claude/workflows/` or writes to `tools.jsonl`/`events.jsonl`/`runs.jsonl`** (read-only
  contract) would catch drift toward accidentally building a write path — this ticket is
  explicitly read-only per `PROPOSAL.md` §3's "Interactivity" decision row.
