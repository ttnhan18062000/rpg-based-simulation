---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
artifact_type: plan
tags: [agent-monitoring, api-design, observability]
---

# Implementation Plan — TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Summary

Build a new, standalone FastAPI backend (`src/api/agent_ops_dashboard/`) that reads
`tickets/{inprogress,done,todos}/**/*.md` and `agent-monitoring/{runs,events,tools}.jsonl` into an
in-memory, `RLock`-per-method-guarded cache, and exposes it through five typed REST endpoints
(`/api/tickets`, `/api/runs`, `/api/runs/{run_id}`, `/api/runs/{run_id}/timeline`, `/api/health`).
The approach is bottom-up: define the Pydantic response contract first (`models.py`), then build
`ingest.py`'s parsing/join/inference logic in narrow, independently-testable slices reusing
`extract_frontmatter()`, `generate_registry.py`'s body-section parsers, and `validate.py`'s
tolerant `load_jsonl` + legacy allowlists (never reimplementing them), then wrap the assembled
snapshot in an `RLock`-per-method cache class mirroring `ReadModelCache` exactly, and finally wire
`main.py`'s routes on top, returning only typed instances. A parity ledger entry (`INFRA-275`) is
added last, once the implementation is real and tested. Three ambiguities the investigation flagged
are resolved directly in the relevant steps below (not left open): `ingest.py` uses `validate.py`'s
tolerant `load_jsonl` (not `query.py`'s crashing one), the ticket-directory walk filters to
`TCK-*.md` before parsing, and the concurrency/state-transition ACs get real
`threading`-based tests, not single-threaded proxies.

## Steps

### Step 1 — Module skeleton + typed response models
**Files:** `src/api/agent_ops_dashboard/__init__.py` (new, empty), `src/api/agent_ops_dashboard/models.py` (new)
**Change:** Create the package directory. In `models.py`, define every Pydantic response model
needed by `DATA_MODEL.md` §1, as real `BaseModel` subclasses (never `dict`):
- `RunMatchSummary`: `run_id: str`, `start_ts: Optional[str]`, `end_ts: Optional[str]`, `final_status: str`
- `TicketSummary`: `ticket_id: str`, `title: str`, `tier: Optional[str]`, `ticket_type: Optional[str]`,
  `priority: Optional[str]`, `layer: str`, `status: str` (frontmatter doc-lifecycle status —
  `active`/`historical`/etc.), `workflow_status: Optional[str]` (`## Status` body field — kept as a
  **separate field name from `status`**, never collapsed), `tags: List[str]`, `date: str`,
  `lifecycle_state: str`, `matching_runs: List[RunMatchSummary]` (default `[]`)
- `RawToolCall`: `tool: str`, `input_summary: str`, `status: str`, `duration_ms: Optional[int]`, `ts: str`
- `FileTouch`: `path: str`, `tool: str`, `ts: str`
- `TimelineEntry`: `seq: int`, `phase: Optional[str]`, `agent: Optional[str]`, `status: str`,
  `summary: str`, `ts: str`, `tool_call_count: Optional[int]`, `cost_proxy_score: Optional[float]`,
  `reason_code: Optional[str]`, `tool_calls: List[RawToolCall]` (default `[]`)
- `RunSummary`: `run_id: str`, `workflow: str`, `tier: str`, `final_status: str`,
  `start_ts: Optional[str]`, `end_ts: Optional[str]`, `duration_s: Optional[int]`,
  `agent_count: int`, `is_inferred_active: bool`, `inferred_start_ts: Optional[str]`
- `RunDetail(RunSummary)`: adds `ticket_title: Optional[str]`, `ticket_lifecycle_state: Optional[str]`
- `RunTimeline`: `run_id: str`, `is_live: bool`, `entries: List[TimelineEntry]`,
  `live_tail: List[RawToolCall]` (default `[]`), `files_touched: List[FileTouch]` (default `[]`)
- `HealthStatus`: `status: str`, `cache_last_rebuilt_ts: Optional[str]`,
  `cache_source_mtimes: Dict[str, float]`, `unparsed_lines: Dict[str, int]`

These are the *only* shapes `main.py` will ever return. Internal parsing structures built in later
steps (raw dicts / lightweight dataclasses from `runs.jsonl`/`events.jsonl`/ticket parsing) are
**not** these classes and must be converted before crossing the route boundary — do not let
`main.py` return an internal record type or `.model_dump()`'d dict (the explicitly-rejected
`history.py` pattern).
**Do NOT touch:** `src/api/routes/history.py`, `src/api/server.py`, `src/api/read_model_cache.py`,
`src/api/routes/health.py` (unrelated empty file on the main simulation API, not this dashboard's
`/api/health`).
**Verify:** No dedicated test yet — exercised indirectly by every later test that imports
`models.py` and by Step 8's `test_typed_response_models_not_dict`. Confirm `python3 -c "from src.api.agent_ops_dashboard import models"` imports cleanly with no side effects.

### Step 2 — ingest.py: ticket frontmatter + body-section parsing
**Files:** `src/api/agent_ops_dashboard/ingest.py` (new)
**Change:** Add the sys.path wiring this repo's own established pattern uses for importing from
non-package `tools/` directories (mirrors `tools/generate_registry.py:33-35` and
`tests/tools/test_validate_agent_monitoring.py:9-14` exactly — do not invent a different import
mechanism):
```python
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _REPO_ROOT / "tools"
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _p in (_TOOLS_DIR, _MONITORING_TOOLS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from validate_frontmatter import extract_frontmatter  # noqa: E402
from generate_registry import parse_body_section, parse_h1_title, _strip_frontmatter  # noqa: E402
```
Implement `parse_ticket_file(path: Path, lifecycle_state: str) -> dict | None`:
1. Read text, call `extract_frontmatter(text)`. If it returns `None` (no frontmatter block), skip
   the file (return `None`) — do not raise.
2. `body = _strip_frontmatter(text)`; `title = parse_h1_title(body)`.
3. Pull `tier`, `ticket_type`, `priority`, `workflow_status` via
   `parse_body_section(body, "Tier")`, `parse_body_section(body, "Type")`,
   `parse_body_section(body, "Priority")`, `parse_body_section(body, "Status")` respectively —
   **convert empty string (`""`, the function's not-found sentinel) to `None`**, never to a
   placeholder string. This is the exact behavior AC #6 tests.
4. Build the internal ticket record dict combining frontmatter fields (`ticket_id`, `layer`,
   `status`, `tags`, `date`) with the four body fields, `title`, and `lifecycle_state`.
5. Implement `walk_ticket_dirs(root: Path) -> list[Path]`: glob `tickets/inprogress/*.md`,
   `tickets/done/*.md` (recursive, since `tickets/done/{folder}/` epics exist per CLAUDE.md), and
   `tickets/todos/**/*.md` (recursive, since `tickets/todos/{folder}/SEQUENCE.md` siblings exist)
   — but filter every candidate to files matching the ticket naming convention
   (`re.match(r"TCK-\d{8}-", path.stem)`) **before** calling `parse_ticket_file` on it. This is the
   resolved decision for the `SEQUENCE.md`/non-ticket-file hazard: filter by filename pattern, do
   not try/except around `extract_frontmatter` as the primary defense (though `parse_ticket_file`
   returning `None` on no-frontmatter is still a reasonable secondary guard for a stray `TCK-*.md`
   with no frontmatter block).
**Do NOT touch:** `docs/REGISTRY.yaml`, `tools/generate_registry.py`, `tools/validate_frontmatter.py`
(import only, never modify or fork their logic).
**Verify:** `tests/tools/test_agent_ops_dashboard_ingest.py::test_ticket_missing_body_sections_surfaces_null_not_error`,
`tests/tools/test_agent_ops_dashboard_ingest.py::test_non_ticket_markdown_in_tickets_dirs_does_not_crash_ingest`

### Step 3 — ingest.py: tolerant JSONL loading + legacy allowlist reuse
**Files:** `src/api/agent_ops_dashboard/ingest.py`
**Change:** Import from the already-path-wired `tools/agent-monitoring/validate.py` (Step 2's
`sys.path.insert` already covers this):
```python
import validate  # noqa: E402  (tools/agent-monitoring/validate.py)
```
**Resolved decision:** use `validate.load_jsonl` (the tolerant one — catches
`json.JSONDecodeError` per line, warns, continues), **not** `tools/agent-monitoring/query.py`'s
crash-on-malformed version. `query.py`'s loader is for a stricter CLI-tool use case and would
violate `PROPOSAL.md` §6's "never crash the API" principle and AC #6's `unparsed_lines`
diagnostic requirement. Do not import from `query.py` at all in this ticket.

Wrap `validate.load_jsonl` in a thin `load_jsonl_counted(path: Path) -> tuple[list[dict], int]`
that also returns the count of skipped/unparseable lines (re-derive the count locally by counting
stderr warnings is fragile — instead, duplicate `validate.load_jsonl`'s try/except *loop shape*
only enough to also increment a counter, OR patch `validate.load_jsonl` to optionally accept a
counter callback if that's cleaner — implementer's call, but the underlying per-line JSON parse
call must still be `validate.load_jsonl`'s own line-parsing behavior, not a hand-rolled
reimplementation, to satisfy AC #3's "same function object" reuse test). Reference
`LEGACY_COMPLETION_FIELDS`, `LEGACY_TERMINAL_STATUS_VALUES`, and `_record_is_complete` directly
from the imported `validate` module (`validate.LEGACY_COMPLETION_FIELDS`, etc.) for `final_status`
normalization (§ Step 4) — do not copy these tuples/sets into `ingest.py`.
**Do NOT touch:** `tools/agent-monitoring/validate.py`, `tools/agent-monitoring/query.py` (import
only).
**Verify:** `tests/tools/test_agent_ops_dashboard_ingest.py::test_legacy_runs_jsonl_schema_generations_do_not_crash_ingest`,
`tests/tools/test_agent_ops_dashboard_ingest.py::test_ingest_reuses_extract_frontmatter_and_validate_allowlists`
(assert `ingest.extract_frontmatter is validate_frontmatter.extract_frontmatter` and
`ingest.load_jsonl is validate.load_jsonl` — or equivalent object-identity check on whatever
wrapper is used, per the test plan's exact wording)

### Step 4 — ingest.py: ticket-to-run join (all matches, sorted descending)
**Files:** `src/api/agent_ops_dashboard/ingest.py`
**Change:** Implement `build_matching_runs(ticket_id: str, runs_by_id: dict) -> list[RunMatchSummary]`
(or the internal-record equivalent, converted to `RunMatchSummary` at the boundary): iterate every
row loaded from `runs.jsonl`, collect **all** rows where `row["run_id"] == ticket_id` (not just the
first), resolve each row's `final_status` via `validate._record_is_complete`-consistent logic
(prefer `final_status`, fall back to `status` for `FOLDER-*`/`EPIC-*` legacy shapes per
`validate.LEGACY_TERMINAL_STATUS_VALUES`), then sort the collected list by `start_ts` descending
(`None`/missing `start_ts` sorts last, not first — use a sort key that pushes `None` to the end
regardless of Python's default `None`-comparison behavior). Wire this into `parse_ticket_file`'s
caller so every `TicketSummary.matching_runs` is populated from the full `runs_by_id` dict, not a
per-ticket single lookup.
**Do NOT touch:** Any logic that collapses to "most recent" or "first" — this is the single
heaviest anti-drift hazard in the investigation (43/618 real collision rate).
**Verify:** `tests/tools/test_agent_ops_dashboard_ingest.py::test_ticket_run_join_returns_all_matches_sorted_desc`

### Step 5 — ingest.py: inferred-active computation + completion transition
**Files:** `src/api/agent_ops_dashboard/ingest.py`
**Change:** Add module constant `ACTIVE_WINDOW_MINUTES = 10`. Implement
`compute_inferred_active(tools_by_run_recent: dict, runs_by_id: dict, now: datetime) -> dict[str, RunSummary-fields]`:
for every `run_id` present in `tools_by_run_recent` (built from `tools.jsonl`) **and absent from
`runs_by_id`**, if the max `ts` across that run's tool rows is within `ACTIVE_WINDOW_MINUTES` of
`now`, mark `is_inferred_active=True` with `inferred_start_ts` = the *first* (minimum `ts`)
`tools.jsonl` row's timestamp for that `run_id`. Runs past the window, or present in `runs_by_id`,
are never inferred-active — a `run_id` that completes (gets a `runs.jsonl` row) during a later
rebuild must fall out of this set entirely on that same rebuild pass (this set is recomputed fresh
from `runs_by_id`'s current contents every rebuild, never carried over/merged from the previous
snapshot), which is what makes the True→False flip atomic together with Step 7's single-pass
rebuild. Accept `now` as a parameter (not `datetime.now()` called internally) so tests can inject a
fixed clock for the boundary case.
**Do NOT touch:** Step 7's locking mechanism (this step only produces the data the lock will
guard).
**Verify:** `tests/tools/test_agent_ops_dashboard_ingest.py::test_inferred_active_run_from_tools_jsonl_tail`
(including its just-past-boundary companion case),
`tests/tools/test_agent_ops_dashboard_ingest.py::test_active_run_completion_flips_inferred_flag_and_timestamps`

### Step 6 — ingest.py: files_touched derivation
**Files:** `src/api/agent_ops_dashboard/ingest.py`
**Change:** Implement `extract_files_touched(entries: list, live_tail: list) -> list[FileTouch]`
per `DATA_MODEL.md` §3's pseudocode: iterate every `tool_calls[]` item across `entries` (and
`live_tail`'s raw tool rows), restrict to `tool in {"Read", "Edit", "Write", "MultiEdit"}`, extract
the file path from `input_summary` (mirroring `post_tool_hook.py`'s `_input_summary()` convention —
read that function first to confirm the exact path-extraction format before parsing it), and
deduplicate by path keeping the **first** `ts`+`tool` seen per path (not the last).
**Do NOT touch:** `tools/agent-monitoring/post_tool_hook.py` (read for reference only, do not
modify its `_input_summary()` format).
**Verify:** `tests/tools/test_agent_ops_dashboard_ingest.py::test_files_touched_dedup_by_path_restricted_to_edit_tools`

### Step 7 — ingest.py: RLock-per-method cache wrapping the full rebuild
**Files:** `src/api/agent_ops_dashboard/ingest.py`
**Change:** Implement a `DashboardCache` class matching `src/api/read_model_cache.py`'s
`ReadModelCache` locking pattern exactly (`src/api/read_model_cache.py:31-166` is the reference —
re-read it before writing this class): a single `self._lock = threading.RLock()` in `__init__`,
and **every** public method (`get_tickets`, `get_runs`, `get_run`, `get_timeline`, `get_health`,
and an internal `_maybe_rebuild`) opens `with self._lock:` as its first statement. `_maybe_rebuild`
checks `mtime` on the four watched sources (`runs.jsonl`, `events.jsonl`, `tools.jsonl`, and a
combined hash/count over `tickets/**`); on any change, it re-runs Steps 2-6's full parse+join+
inference pipeline into fresh local structures, then reassigns every instance attribute
(`self._runs_by_id`, `self._tickets_by_id`, `self._tools_by_seq`, `self._tools_by_run_recent`,
`self._events_by_run`, `self._inferred_active`, `self._last_rebuilt_ts`, `self._unparsed_lines`,
`self._source_mtimes`) **while still holding the same lock the whole rebuild acquired** — this is
the explicit anti-drift decision from the investigation: **do not** implement the swap-based
build-outside-lock design from `DATA_MODEL.md` §4's "slightly better option" (that was evaluated
and explicitly rejected in favor of the simpler `RLock`-around-the-whole-rebuild reuse of
`ReadModelCache`'s exact pattern — it reads as more sophisticated, which is exactly why it's a
temptation to avoid). Every public getter method calls `self._maybe_rebuild()` first (still inside
its own `with self._lock:` block — `RLock` is reentrant, so `_maybe_rebuild` calling into the same
lock from within a locked method is safe) before reading instance state.
**Do NOT touch:** `src/api/read_model_cache.py` itself (read-only reference; do not import or
subclass it — this is a parallel, independent implementation of the same *pattern*, not a shared
base class, since `DATA_MODEL.md` confirms the invalidation trigger — `mtime` vs. `DirtySet` — is
materially different).
**Verify:** `tests/tools/test_agent_ops_dashboard_concurrency.py::test_concurrent_requests_never_observe_partial_rebuild`
— must spawn real `threading.Thread`s (one triggering a rebuild via a touched fixture file mtime,
several reading concurrently), with an injected delay in one parse step to deterministically widen
the race window rather than relying on timing luck, and must assert no reader ever observes a
structure where some attributes reflect the new rebuild and others reflect the old one. Also
exercises `test_active_run_completion_flips_inferred_flag_and_timestamps` under concurrent reads
per the test plan's pairing note.

### Step 8 — main.py: FastAPI app + 5 typed routes
**Files:** `src/api/agent_ops_dashboard/main.py` (new)
**Change:** Create a standalone `FastAPI()` app (not mounted on `src/api/server.py` — confirmed
separate product/port per the investigation) instantiating one module-level `DashboardCache()`
from Step 7. Declare all 5 routes with explicit `response_model=` from `models.py`, returning
constructed typed instances (never `.model_dump()`, never raw dict) — the exact opposite of
`src/api/routes/history.py`'s pattern:
- `GET /api/tickets` → `response_model=List[TicketSummary]`, query params per `DATA_MODEL.md` §1
  (`tier`, `layer`, `status`, `priority`, `tag` repeatable, `lifecycle`, `q`, `sort`)
- `GET /api/runs` → `response_model=List[RunSummary]`, `Query(default=50, ge=1, le=100)` for
  `limit` (mirroring `history.py:28`'s exact convention per AC's own citation), `offset`, `status`,
  `workflow`, `since`
- `GET /api/runs/{run_id}` → `response_model=RunDetail`; if `run_id` is in neither `runs_by_id` nor
  the inferred-active set, `raise HTTPException(status_code=404, ...)` — mirroring
  `history.py:51`'s `FileNotFoundError` → 404 pattern, adapted to a direct membership check here
  since there's no file-read exception to catch
- `GET /api/runs/{run_id}/timeline` → `response_model=RunTimeline`, implementing
  `DATA_MODEL.md` §3's join pseudocode against `events_by_run`/`tools_by_seq`/`tools_by_run_recent`
- `GET /api/health` → `response_model=HealthStatus`; `status` is **hardcoded `"ok"`** always (per
  the anti-drift hazard — never derive it from parse-error counts), `unparsed_lines` and
  `cache_source_mtimes`/`cache_last_rebuilt_ts` read from the cache's Step 7 state
No `StaticFiles` mount anywhere in this file (owned by `AGENTOPS-BUILD-SERVE`).
**Do NOT touch:** `src/api/server.py`, `src/api/routes/health.py`, any Makefile target, any
frontend code.
**Verify:** `tests/tools/test_agent_ops_dashboard_api.py::test_run_detail_404_for_unknown_run_id`,
`tests/tools/test_agent_ops_dashboard_api_boundary.py::test_typed_response_models_not_dict`,
`tests/tools/test_agent_ops_dashboard_api.py::test_malformed_jsonl_line_skipped_and_counted_in_health`

### Step 9 — Parity ledger entry INFRA-275
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry after `INFRA-274` (the current highest ID, confirmed by the
investigation), following the exact YAML shape of neighboring entries (`id`, `text`, `status`,
`priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`,
`support_boundary`):
```yaml
- id: INFRA-275
  text: >
    Agent Ops Dashboard backend (TCK-20260716-AGENTOPS-DASHBOARD-BACKEND): a standalone FastAPI
    app (src/api/agent_ops_dashboard/) exposing GET /api/tickets, /api/runs, /api/runs/{run_id},
    /api/runs/{run_id}/timeline, /api/health as typed Pydantic response models only (never raw
    dict/domain payloads). ingest.py owns all file reads over tickets/{inprogress,done,todos}/
    and agent-monitoring/{runs,events,tools}.jsonl, reusing tools/validate_frontmatter.py's
    extract_frontmatter(), tools/generate_registry.py's body-section parsers, and
    tools/agent-monitoring/validate.py's tolerant load_jsonl + legacy allowlists rather than
    reimplementing them. In-memory cache rebuilt on source mtime change, guarded by a single
    threading.RLock() per method matching src/api/read_model_cache.py::ReadModelCache's exact
    pattern (not the swap-based alternative). Ticket-to-run join returns all matching runs.jsonl
    rows per ticket_id (not first-match-wins). is_inferred_active heuristic covers runs visible
    in tools.jsonl but absent from runs_by_id within a 10-minute window.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: src/api/agent_ops_dashboard/main.py + ingest.py + models.py
  proof_type: feature
  test_path: >
    tests/tools/test_agent_ops_dashboard_ingest.py, tests/tools/test_agent_ops_dashboard_api.py,
    tests/tools/test_agent_ops_dashboard_concurrency.py,
    tests/tools/test_agent_ops_dashboard_api_boundary.py
  divergence_note: null
  support_boundary: >
    Read-only over tickets/** and agent-monitoring/*.jsonl; never touches AuthoritativeState.
    Excludes frontend, build/serve tooling (AGENTOPS-BUILD-SERVE), the live phase/agent
    null-labeling gap (independent sibling ticket), and agent-monitoring retention/rotation
    (out of scope, unbounded growth accepted).
```
Set `status: verified` and finalize `test_path`/`v2_evidence` only once Steps 1-8 are implemented
and their tests pass — do not add this entry with fabricated evidence before the code exists.
**Do NOT touch:** Any other `infrastructure.yaml` entry, `INFRA-210`, or any other parity ledger
file.
**Verify:** No dedicated test; verified by `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` parsing cleanly (schema validation) and manual cross-check against `docs/parity_ledger/schema.json`.

## Scope Guards

- No frontend code of any kind (React components, `frontend/` changes, `UI_INTERACTION_SPEC.md`
  implementation) — owned by `AGENTOPS-TICKETS-VIEW`, `AGENTOPS-ACTIVITY-GANTT`,
  `AGENTOPS-REPLAY-TIMELINE`.
- No `Makefile` changes, no `dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve`
  targets, no `StaticFiles` mount in `main.py` — owned by `AGENTOPS-BUILD-SERVE`.
- No changes to `.claude/workflows/implement-ticket.js`, no `phase`/`agent` field added to
  `tools.jsonl`'s live rows — the instrumentation gap is a confirmed independent sibling ticket.
- No retention/rotation logic for `agent-monitoring/*.jsonl` — do not extend or repurpose
  `src/observability/reporting/retention.py`'s `RetentionPolicy`/`RetentionManager` (that class
  governs only `data/runs/`, an unrelated domain).
- No write path anywhere in `src/api/agent_ops_dashboard/` — never write to
  `tools.jsonl`/`events.jsonl`/`runs.jsonl`, never write ticket files. This is a read-only viewer.
- Do not collapse `TicketSummary.matching_runs` to a single row under any circumstance.
- Do not conflate `TicketSummary.status` (frontmatter doc-lifecycle field) with
  `TicketSummary.workflow_status` (`## Status` body field) — keep them as two distinct fields.
- Do not implement the swap-based (build-outside-lock, atomic-pointer-swap) concurrency design
  from `DATA_MODEL.md` §4 — the `RLock`-around-the-whole-rebuild decision is final.
- Do not read or reuse `docs/REGISTRY.yaml` as a ticket data source — confirmed non-viable
  (missing `status`/`layer`/`priority`, no `inprogress`/`todos` coverage).
- Do not modify `tools/validate_frontmatter.py`, `tools/generate_registry.py`,
  `tools/agent-monitoring/validate.py`, or `tools/agent-monitoring/query.py` — import/reuse only.
- Do not touch `src/api/routes/health.py` (unrelated empty file on the main simulation API) or any
  other file under `src/api/routes/`, `src/api/server.py`, `src/api/read_model_cache.py`,
  `src/api/ws/`.
- Do not extend `tests/architecture/test_api_read_model_guard.py`'s scanned path set to include
  `src/api/agent_ops_dashboard/` — noted by the investigation as a real gap but not this ticket's
  scope to close (no AC requires it).
- Do not add `GET /api/v1/observability/...`-style versioned prefixes or otherwise mimic
  `src/api/server.py`'s router-mounting convention — this is confirmed to be a genuinely separate
  app/product boundary, not a router on the existing app.

## Dependency Map

- Step 1 (models.py) has no dependencies — build first.
- Step 2 (ticket parsing) depends only on Step 1 existing (imports nothing from later steps).
- Step 3 (JSONL loading) is independent of Step 2 (different data source) but both live in the
  same `ingest.py` file — implement Step 2 first, then Step 3, to keep diffs small and reviewable.
- Step 4 (ticket-run join) depends on Steps 2 and 3 (needs both `tickets_by_id` and `runs_by_id`
  populated).
- Step 5 (inferred-active) depends on Step 3 (`tools_by_run_recent`, `runs_by_id`).
- Step 6 (files_touched) depends on Step 3 (`tool_calls` data) and is otherwise independent of
  Steps 4-5.
- Step 7 (RLock cache) depends on Steps 2-6 all being complete — it wraps the full pipeline.
- Step 8 (main.py routes) depends on Step 1 (models) and Step 7 (cache) — cannot be built or
  meaningfully tested before both exist.
- Step 9 (parity ledger) depends on Steps 1-8 being implemented and their tests passing — do not
  write this entry first.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: All 5 routes declare typed Pydantic response models, never raw dict — `history.py`'s `List[dict]`+`.model_dump()` pattern not mirrored | Steps 1, 8 | `test_typed_response_models_not_dict` |
| AC2: `matching_runs` contains all N rows sorted `start_ts` descending, not collapsed to one | Step 4 | `test_ticket_run_join_returns_all_matches_sorted_desc` |
| AC3: `ingest.py` imports and calls `extract_frontmatter()`, `load_jsonl()`, and `validate.py`'s legacy allowlists rather than reimplementing | Steps 2, 3 | `test_ingest_reuses_extract_frontmatter_and_validate_allowlists` |
| AC4: Concurrent requests during a rebuild never observe a partially-rebuilt structure, via `RLock`-per-method matching `ReadModelCache` | Step 7 | `test_concurrent_requests_never_observe_partial_rebuild` |
| AC5: `GET /api/runs/{run_id}` returns 404 (not 500/empty 200) for unknown `run_id` | Step 8 | `test_run_detail_404_for_unknown_run_id` |
| AC6: Ticket missing `## Tier`/`## Priority`/`## Type` surfaces those fields as `null`, not error/placeholder | Step 2 | `test_ticket_missing_body_sections_surfaces_null_not_error` |
| AC7: `run_id` in `tools.jsonl` within `ACTIVE_WINDOW_MINUTES=10` and absent from `runs_by_id` returns `is_inferred_active=true` with correct `inferred_start_ts` | Step 5 | `test_inferred_active_run_from_tools_jsonl_tail` |
| AC8: On completion, `is_inferred_active` flips `true→false` and timestamps switch to authoritative values atomically | Steps 5, 7 | `test_active_run_completion_flips_inferred_flag_and_timestamps` (paired with the concurrency test) |
| Scope bullet: `files_touched` derivation, deduped by path, restricted to Read/Edit/Write/MultiEdit | Step 6 | `test_files_touched_dedup_by_path_restricted_to_edit_tools` |

## Anti-Drift Notes

- **`load_jsonl` choice is settled, not a TODO**: `ingest.py` must use `validate.py`'s tolerant
  `load_jsonl` (catches `JSONDecodeError`, warns, continues), never `query.py`'s crash-on-malformed
  version. If a future reviewer sees `query.py` imported anywhere in `ingest.py`, that's a
  regression against this decision.
- **`tickets/todos/` non-ticket files**: the directory walk (Step 2) must filter to `TCK-*.md`
  filenames *before* attempting to parse — `SEQUENCE.md` and any other folder-level metadata file
  under `tickets/todos/{folder}/` must never reach `extract_frontmatter()`.
- **Concurrency and state-transition ACs require real `threading`-based tests** — a
  single-threaded assertion that a lock object exists on the class is not sufficient and does not
  satisfy AC #4 or AC #8. `ReadModelCache` itself has no existing concurrency test to copy from;
  Step 7's test is new test-writing, not adaptation.
- **`tests/architecture/test_api_read_model_guard.py` does not scan `src/api/agent_ops_dashboard/`.**
  There is no static backstop catching a raw-dict leak in this module beyond this ticket's own
  `test_typed_response_models_not_dict` (Step 8) — that test must actually assert on
  `response_model` shape (via route introspection or AST scan), not merely that the endpoint
  returns 200.
- **`RunMatchSummary`/`RunSummary.final_status` must resolve from either `final_status` or
  `status`** (the `FOLDER-*`/`EPIC-*` legacy shape uses a bare `status` field) — reading only
  `final_status` will silently produce wrong values for those legacy rows, per
  `validate._record_is_complete`'s own two-field check.
- **`GET /api/health`'s `status` field is always the literal string `"ok"`** — never make it
  reflect parse-error counts or degrade to a non-`"ok"` value; that information belongs only in
  `unparsed_lines`.
- **Sort key for `None` `start_ts`**: Python's default sort will error or misorder when comparing
  `None` to a string — use an explicit key function (e.g. sort by `(start_ts is None, start_ts)`
  reversed appropriately, or substitute a sentinel minimum value) so `None`/missing `start_ts` rows
  sort last under descending order, not first and not a crash.

## Deviations

Discovered during implementation by smoke-testing against the live `agent-monitoring/*.jsonl` +
`tickets/**` corpus (not anticipated by this plan's steps, none contradict the plan's design
decisions — additive robustness fixes only):

1. **Timestamp type coercion (`_coerce_ts`)**: a minority of real `runs.jsonl` rows (`FOLDER-*`/
   `EPIC-*` legacy batch wrappers) carry `start_ts`/`end_ts` as raw unix-epoch `int`/`float`
   rather than ISO strings. Every model field typed `str` that carries a timestamp (`RunSummary`,
   `RunMatchSummary`, `TimelineEntry`, `RawToolCall`, `FileTouch`) now passes through
   `_coerce_ts()` first — without it, `GET /api/runs` raised `pydantic.ValidationError` against
   real data. Not addressed by any of Steps 1-8's text, since none of the three design docs
   (`PROPOSAL.md`/`DATA_MODEL.md`/`IMPLEMENTATION_CONTEXT.md`) sampled this specific legacy shape.
2. **`_resolve_final_status` fallback to `validate._record_is_complete`**: for the two legacy
   generations that carry neither `final_status` nor `status` (`started_at`/`finished_at`,
   `ts_start`/`ts_end`/`result`), the join now falls back to `validate._record_is_complete(rec)`
   (checking `LEGACY_COMPLETION_FIELDS`) to resolve `DONE` instead of defaulting to a misleading
   `IN_PROGRESS`. Step 4's text names `_record_is_complete`-consistent logic but only explicitly
   covers the `FOLDER-*`/`EPIC-*` bare-`status` case — this extends the same reuse to the other
   documented legacy generations in `docs/agent-monitoring/schema.md`'s "Known Limitations".
3. **`_LIFECYCLE_PRIORITY` tie-break (`inprogress` > `done` > `todos`)**: added to
   `DashboardCache._rebuild`'s ticket-collection loop. This ticket's own file exists
   simultaneously under both `tickets/inprogress/` and `tickets/todos/agent-ops-dashboard/` during
   this very implementation session (the `todos` source is deleted only at Finalize, per
   CLAUDE.md's Workflow Rule) — without an explicit precedence order, dict-insertion order (last
   directory walked wins) non-deterministically picked the wrong lifecycle_state. Neither this
   plan nor `DATA_MODEL.md` addressed the case of a `ticket_id` appearing under more than one
   lifecycle directory in the same rebuild.

None of these required a design decision reversal — all three are narrow, additive tolerance
fixes discovered only by testing against real data volume/shape, consistent with this plan's own
"never crash the API" governing principle (Anti-Drift Notes, `load_jsonl` section).
