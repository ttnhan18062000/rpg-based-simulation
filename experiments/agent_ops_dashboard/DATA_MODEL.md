# Data Model — API contract, internal structures, concurrency design

**Status:** technical design detail, not yet implemented — companion to `PROPOSAL.md` §5
**Scope:** exact field-level schemas for every endpoint named in `PROPOSAL.md` §5, `ingest.py`'s
internal in-memory representation, the join algorithm made concrete, and a concurrency/locking
design that no other document in this folder addresses.
**Date:** 2026-07-16

---

## 1. API contract

All response bodies are `models.py` Pydantic schemas (never raw parsed dicts), per `PROPOSAL.md`
§5's citation of this repo's "don't expose raw domain models" rule. Endpoint list is fixed at the
five named in `PROPOSAL.md` §5 — this document does not add or remove endpoints, only specifies
their shape.

### `GET /api/tickets`

| Query param | Type | Notes |
|---|---|---|
| `tier` | `str?` | `hotfix`/`standard`/`epic` |
| `layer` | `str?` | one of CLAUDE.md's `layer` enum |
| `status` | `str?` | `OPEN`/`INPROGRESS`/`BLOCKED`/`DONE` — from the ticket body's `## Status`, not frontmatter (frontmatter's `status` field means something different — see below) |
| `priority` | `str?` | `P0`/`P1`/`P2` |
| `tag` | `str?`, repeatable | matches if any requested tag is present |
| `lifecycle` | `str?` | `inprogress`/`done`/`todos`/`all` (default `all`) — which of the three ticket directories to include |
| `q` | `str?` | free-text match against title + `ticket_id` |
| `sort` | `str` | `date_desc` (default) / `date_asc` |

**Response:** `List[TicketSummary]`

| Field | Type | Nullable | Source |
|---|---|---|---|
| `ticket_id` | `str` | No | frontmatter |
| `title` | `str` | No | `## Title` body section (`extract_frontmatter` covers frontmatter only — the H1/`## Title` body parse reuses `generate_registry.py::parse_h1_title()`/`parse_body_section()`, per `IMPLEMENTATION_CONTEXT.md` §1) |
| `tier` | `str` | No | `## Tier` body section — **not frontmatter**, confirmed absent from CLAUDE.md's required-frontmatter-fields list (`status, layer, authority, audience, ticket_id, phase, date, tags` only) |
| `ticket_type` | `str` | Yes | `## Type` body section — same correction: not frontmatter, despite `docs/REGISTRY.yaml`'s ticket entries exposing a `ticket_type` field (that field is itself derived from this same body section by `generate_registry.py`, not read from frontmatter) |
| `priority` | `str` | Yes | `## Priority` body section — same correction, not frontmatter |
| `layer` | `str` | No | frontmatter |
| `status` | `str` | No | frontmatter's `status` field (`active`/`historical`/etc. — the doc-lifecycle status) — **distinct from** the body's `## Status` field (`OPEN`/`INPROGRESS`/`BLOCKED`/`DONE`, the workflow status). Both are surfaced as separate fields (`status` and `workflow_status`) to avoid collapsing two genuinely different concepts into one name — a mistake worth naming explicitly since both are called "status" in the source ticket file. |
| `workflow_status` | `str` | Yes | `## Status` body section |
| `tags` | `List[str]` | No | frontmatter |
| `date` | `str` (ISO date) | No | frontmatter |
| `lifecycle_state` | `str` | No | `inprogress`/`done`/`todos` — derived from which directory the file was read from, not a file field |
| `run_id_match` | `str?` | Yes | set when `ticket_id` matches a `run_id` in the runs cache (§2) — lets the frontend link a ticket row to its run detail |

**Note on frontmatter vs. body fields:** per `IMPLEMENTATION_CONTEXT.md` §2's confirmed
`docs/REGISTRY.yaml` gap, `tier`, `ticket_type`, `priority`, and the workflow `## Status` are all
**body-section fields**, not frontmatter — `extract_frontmatter()` alone does not surface any of
them. `ingest.py` needs a second, lightweight body-section parser for these four fields
specifically (reusing `generate_registry.py::parse_body_section()`, per `IMPLEMENTATION_CONTEXT.md`
§1's reuse table), applied on top of `extract_frontmatter()`'s output, not instead of it. This is a
sharper version of `IMPLEMENTATION_CONTEXT.md` §2's finding: it isn't only that `REGISTRY.yaml`
lacks these fields for its own reasons — `tier`/`ticket_type`/`priority`/workflow-status were never
frontmatter fields to begin with, for any ticket, at any time. Reaching for frontmatter alone for
any of these four would be a real bug, not a missed optimization.

### `GET /api/runs`

| Query param | Type | Notes |
|---|---|---|
| `limit` | `int` | default 50, `1 <= limit <= 100` — mirrors `HistoricalRunQueryService.list_historical_runs`'s exact `Query(default=50, ge=1, le=100)` convention (`PROPOSAL.md` §5a) |
| `offset` | `int` | default 0 |
| `status` | `str?` | `final_status` filter |
| `workflow` | `str?` | `implement-ticket`/`implement-epic`/`create-tickets` |
| `since` | `str? (ISO ts)` | only runs with `start_ts >= since` — backs the Recent Activity view's time-window selector (`UI_INTERACTION_SPEC.md` §2) |

**Response:** `List[RunSummary]`

| Field | Type | Nullable | Source |
|---|---|---|---|
| `run_id` | `str` | No | `runs.jsonl` |
| `workflow` | `str` | No | `runs.jsonl` |
| `tier` | `str` | No | `runs.jsonl` (`n/a` for `create-tickets`, per `schema.md`) |
| `final_status` | `str` | No | `runs.jsonl`, normalized through `validate.py`'s legacy-status allowlist |
| `start_ts` | `str (ISO)` | Yes | `null` only for the one documented legacy shape with no timestamp fields at all (`TCK-20260623-TYPE-CHECKER`, per `schema.md`'s "Known Limitations") |
| `end_ts` | `str (ISO)` | Yes | `null` for a genuinely crashed/incomplete run |
| `duration_s` | `int` | Yes | `runs.jsonl`, or computed from `start_ts`/`end_ts` if the file's own value is absent |
| `agent_count` | `int` | No | `runs.jsonl` |
| `is_inferred_active` | `bool` | No | **computed, not stored** — `true` when `run_id` has a `tools.jsonl` row within the active-run window (§2) and no matching `runs.jsonl` record yet (`PROPOSAL.md` §7b) |
| `inferred_start_ts` | `str (ISO)` | Yes | only set when `is_inferred_active` is `true` — the first `tools.jsonl` timestamp seen for this `run_id`, explicitly an estimate per §7b |

### `GET /api/runs/{run_id}`

**Response:** `RunDetail` — all `RunSummary` fields plus:

| Field | Type | Nullable | Source |
|---|---|---|---|
| `ticket_title` | `str` | Yes | cross-referenced from the tickets cache if `run_id` matches a `ticket_id` |
| `ticket_lifecycle_state` | `str` | Yes | same cross-reference |

404 if `run_id` matches nothing in either the runs cache or the inferred-active set (mirrors
`HistoricalRunQueryService.get_run_manifest`'s `FileNotFoundError` → `HTTPException(404)` pattern,
`PROPOSAL.md` §5a).

### `GET /api/runs/{run_id}/timeline`

**Response:** `RunTimeline`

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `run_id` | `str` | No | |
| `is_live` | `bool` | No | mirrors `RunSummary.is_inferred_active` for this specific run |
| `entries` | `List[TimelineEntry]` | No | ordered by `seq` ascending — the events ⋈ tools join, §3 |
| `live_tail` | `List[RawToolCall]` | No (empty list if none) | only populated when `is_live` — raw `tools.jsonl` rows for this `run_id` that have no matching `events.jsonl` entry yet (because none exists — §7a). **`phase`/`agent` are `null` on every item here** until `MONITORING_INSTRUMENTATION_GAP.md`'s fix lands — the frontend must render this as "activity, phase unknown" rather than guessing |
| `files_touched` | `List[FileTouch]` | No (empty list if none) | derived, not stored — deduplicated `{path, tool, ts}` extracted from every `tool_calls[].input_summary` across `entries` (+ `live_tail`) where `tool` is `Read`/`Edit`/`Write`/`MultiEdit`, per `post_tool_hook.py`'s `_input_summary()` convention (`PROPOSAL.md` §7b) |

`TimelineEntry`:

| Field | Type | Nullable |
|---|---|---|
| `seq` | `int` | No |
| `phase` | `str` | No (always present for a completed entry — only `live_tail` items can lack it) |
| `agent` | `str` | No (same caveat) |
| `status` | `str` | No |
| `summary` | `str` | No (empty string is a valid value, per `schema.md`) |
| `ts` | `str (ISO)` | No |
| `tool_call_count` | `int` | Yes |
| `cost_proxy_score` | `float` | Yes |
| `reason_code` | `str` | Yes |
| `tool_calls` | `List[RawToolCall]` | No (empty list if none) | the joined `tools.jsonl` rows for this `(run_id, seq)` |

`RawToolCall`: `tool: str`, `input_summary: str`, `status: str`, `duration_ms: int?`, `ts: str (ISO)`
— a direct pass-through of `tools.jsonl`'s own fields (§1 of `docs/agent-monitoring/schema.md`),
not renamed.

### `GET /api/health`

| Field | Type | Notes |
|---|---|---|
| `status` | `str` | `ok` always (this endpoint itself never fails — mirrors `validate.py`'s tolerant posture, `PROPOSAL.md` §6) |
| `cache_last_rebuilt_ts` | `str (ISO)` | when the in-memory cache last actually reparsed (not every request — only on `mtime` change) |
| `cache_source_mtimes` | `Dict[str, float]` | the four watched paths (`runs.jsonl`, `events.jsonl`, `tools.jsonl`, a hash/count over `tickets/**`) and their last-seen `mtime` |
| `unparsed_lines` | `Dict[str, int]` | count of skipped malformed/unrecognized lines per source file since last rebuild, per `PROPOSAL.md` §6 |

---

## 2. `ingest.py`'s internal data model

In-memory structures, rebuilt in full on any watched-file `mtime` change (`PROPOSAL.md` §3's
in-memory-cache decision):

```python
runs_by_id: dict[str, RunRecord]                      # keyed by run_id, from runs.jsonl
events_by_run: defaultdict[str, list[EventRecord]]    # from events.jsonl, one list per run_id
tools_by_seq: defaultdict[tuple[str, int], list[ToolCallRecord]]  # keyed by (run_id, seq)
tools_by_run_recent: defaultdict[str, list[ToolCallRecord]]        # ALL tool rows for a run_id,
                                                                    # unfiltered by seq — needed for
                                                                    # live_tail (§1) since a live
                                                                    # run's tool rows may have no
                                                                    # matching events entry at all
tickets_by_id: dict[str, TicketRecord]                # keyed by ticket_id, from frontmatter+body parse
```

This mirrors `docs/agent-monitoring/schema.md`'s own join example almost exactly
(`events_by_run`/`tools_by_event` naming, `IMPLEMENTATION_CONTEXT.md` §1), with one addition:
`tools_by_run_recent` is new here, not in the schema doc's example, because that example only ever
joins *completed* data — it never needed to represent "tool calls that exist for a run with no
`events.jsonl` entries yet," which is exactly the live-run case this dashboard has to render.

**Active-run inference** (`RunSummary.is_inferred_active`, §1): a `run_id` present in
`tools_by_run_recent` with a max `ts` within the last `ACTIVE_WINDOW_MINUTES` (proposed default: 10
— generous enough to survive a slow tool call, short enough that a genuinely abandoned/crashed run
stops showing as "LIVE" within a reasonable time) **and** absent from `runs_by_id` is inferred
active. This is a heuristic, not a fact — stated as such in every response field name
(`is_inferred_active`, `inferred_start_ts`), matching `PROPOSAL.md` §7b's own honesty about this.

---

## 3. Join algorithm — concrete pseudocode

```python
def build_timeline(run_id: str) -> RunTimeline:
    events = sorted(events_by_run.get(run_id, []), key=lambda e: e.seq)
    entries = []
    for e in events:
        tool_calls = tools_by_seq.get((run_id, e.seq), [])
        entries.append(TimelineEntry(**e.__dict__, tool_calls=tool_calls))

    is_live = run_id in inferred_active_run_ids  # computed once per rebuild, not per request
    live_tail = []
    if is_live:
        known_seqs = {e.seq for e in events}
        live_tail = [
            t for t in tools_by_run_recent.get(run_id, [])
            if t.seq is None or t.seq not in known_seqs
        ]

    files_touched = extract_files_touched(entries, live_tail)  # dedupe by path, keep first ts+tool
    return RunTimeline(
        run_id=run_id, is_live=is_live,
        entries=entries, live_tail=live_tail, files_touched=files_touched,
    )
```

This is a direct extension of `schema.md`'s own join example (`IMPLEMENTATION_CONTEXT.md` §1) — the
`events_by_run`/`tools_by_seq` lookup pattern is unchanged; the only new logic is the `live_tail`
computation, which has no precedent anywhere else in this codebase (nothing today needs to
represent "tool activity with no corresponding event record").

---

## 4. Concurrency & locking — a real gap, not addressed anywhere else in this folder

**The gap:** `PROPOSAL.md` §3 chose an in-memory cache rebuilt on `mtime` change, but never
specified what happens to a request that arrives *while* a rebuild is in progress. A naive
"reassign the module-level dict in place" implementation risks a concurrent request reading a
half-rebuilt structure (e.g. `runs_by_id` updated but `events_by_run` not yet, if the rebuild
mutates each structure one at a time) — a real correctness bug under FastAPI's async
concurrency model, not a hypothetical one.

**Existing precedent in this exact codebase, found and reusable:** `src/api/read_model_cache.py`'s
`ReadModelCache` (cited in `IMPLEMENTATION_CONTEXT.md`'s reuse table only in passing — expanded
here) guards every read and write with a single `threading.RLock()`. That's the simplest available
option: wrap `ingest.py`'s rebuild-and-swap in the same lock every read acquires.

**A slightly better option for this specific access pattern, recommended:** build the *entire* new
set of structures (§2) into a fresh, private object first — outside any lock, so slow parse/join
work never blocks concurrent readers — then swap a single module-level reference to that new object
under a lock held only for the swap itself (microseconds, not the whole rebuild duration):

```python
_cache_lock = threading.Lock()
_current_snapshot: IngestSnapshot = IngestSnapshot.empty()

def get_snapshot() -> IngestSnapshot:
    return _current_snapshot  # single reference read — safe without a lock in CPython

def maybe_rebuild():
    if not sources_changed():
        return
    new_snapshot = build_snapshot()          # slow work, no lock held
    global _current_snapshot
    with _cache_lock:
        _current_snapshot = new_snapshot     # atomic pointer swap
```

This is a real design decision worth stating explicitly rather than leaving implicit: **reuse
`ReadModelCache`'s `RLock`-per-method pattern if simplicity is preferred** (it's already proven in
this codebase and easier to reason about for a first version); **use the swap-based approach above
if rebuild time ever becomes noticeable** (it never blocks readers during the slow part). Given
§3's own measured "sub-second" rebuild time at current data volume (`PROPOSAL.md` §4), either choice
is safe today — this is flagged so the choice is made deliberately, not defaulted into.

---

## Related

- `PROPOSAL.md` §3 (data layer decision), §5 (endpoint list, architecture) — this document specifies what those sections name
- `IMPLEMENTATION_CONTEXT.md` §1 (reuse inventory), §2 (the `REGISTRY.yaml`/frontmatter schema gap this document's `priority`/`workflow_status` fields resolve)
- `docs/agent-monitoring/schema.md` — the join example this document's §3 extends
- `src/api/read_model_cache.py` — the `threading.RLock()` precedent for §4
- `UI_INTERACTION_SPEC.md` — consumes every field defined here
- `TEST_PLAN.md` — tests the join logic and concurrency behavior defined here
