---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND
artifact_type: investigation
tags: [agent-monitoring, api-design, observability]
---

# Investigation — TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Current Behavior

This is genuinely new code — `src/api/agent_ops_dashboard/` does not exist yet (confirmed:
`find src/api -name agent_ops_dashboard` returns nothing). There is no "current behavior" for
the module itself; the relevant current behavior is in the modules this ticket must reuse or
mirror.

**`tools/validate_frontmatter.py::extract_frontmatter(text)`** (`tools/validate_frontmatter.py:64-104`)
— hand-rolled YAML-subset frontmatter parser. Returns `dict | None` (None = no frontmatter
block), raises `ValueError` on unparseable lines. Only parses the frontmatter block itself — it
does **not** parse body sections (`## Tier`, `## Type`, `## Priority`, `## Status`). This is the
function `ingest.py` must import for every ticket file's frontmatter (`status`, `layer`, `tags`,
`ticket_id`, `date`, etc. — all frontmatter fields per `CLAUDE.md`'s ticket format).

**`tools/generate_registry.py::parse_body_section(body, section)`** (`tools/generate_registry.py:54-66`)
and **`parse_h1_title(body)`** (`:82-88`) — regex-based extraction of `## <section>` text up to
the next `## ` heading, and the first `# ` H1 line respectively. `_strip_frontmatter(text)`
(`:91-97`) strips the frontmatter block to produce `body` for these two functions to operate on.
These three functions are exactly what `DATA_MODEL.md` §1 specifies `ingest.py` must reuse for
`title`, `tier`, `ticket_type`, `priority`, and `workflow_status` (all confirmed body-section
fields, never frontmatter — verified directly against `CLAUDE.md`'s required-frontmatter-fields
list: `status, layer, authority, audience, ticket_id, phase, date, tags` only).
`parse_related_code_areas(section_text)` (`:69-79`) exists but is explicitly out of scope for v1
per `IMPLEMENTATION_CONTEXT.md` §5.

**`tools/generate_registry.py::collect_tickets(root)`** (`:246-311`) only walks
`tickets/done/*.md` (flat, non-recursive into subfolders) and is the source for
`docs/REGISTRY.yaml`'s ticket entries. Confirmed gap (also independently re-confirmed by direct
read of `docs/REGISTRY.yaml` structure): ticket-type registry entries carry
`path, ticket_id, title, tier, ticket_type, date, related_code_areas, artifact_files, tags` —
**no `status`, `layer`, or `priority`**, and no `tickets/inprogress/`/`tickets/todos/` coverage
at all. This confirms the ticket's own "Assumptions" section — `docs/REGISTRY.yaml` is not a
viable ticket data source for this dashboard.

**`tools/agent-monitoring/query.py::load_jsonl(path)`** (`tools/agent-monitoring/query.py:24-27`)
— `Path.read_text().splitlines()` → `json.loads` per line, skipping blanks (no try/except — a
malformed line raises `json.JSONDecodeError` uncaught). This is the "exact loader" the ticket AC
requires `ingest.py` to reuse. Note: this loader is **not** tolerant of malformed JSON lines by
itself — `tools/agent-monitoring/validate.py::load_jsonl` (`tools/agent-monitoring/validate.py:170-182`)
is a second, different implementation of the same idea that *does* catch
`json.JSONDecodeError` per line and warns instead of crashing. These are two distinct functions
with the same name in different modules, not one shared function — `ingest.py` needs the
tolerant one (`validate.py`'s) for its `/api/health` `unparsed_lines` diagnostic (`PROPOSAL.md`
§6, `DATA_MODEL.md` §1's `GET /api/health` table) to work at all; `query.py`'s version would
crash the whole cache rebuild on one bad line, which is worse than the "never crash the API"
principle the ticket's own precedent (`PROPOSAL.md` §6) states as a governing principle. This
needs an explicit implementation decision — see Risks.

**`tools/agent-monitoring/validate.py`** (`tools/agent-monitoring/validate.py:31-51`) —
`LEGACY_COMPLETION_FIELDS = ("end_ts", "finished_at", "completed_at", "ts_end")` and
`LEGACY_TERMINAL_STATUS_VALUES = {...}` (11 values) plus `_record_is_complete(rec)` (`:44-51`).
These are the "legacy allowlists" the ticket AC requires `ingest.py` to import and call — they
live in `validate.py` itself (not a separate `vocabulary.py` constants module, though
`validate.py` does import `CANONICAL_TIERS`/`WORKFLOW_PHASES`/`infer_workflow`/`is_known_agent`
from `tools/agent-monitoring/vocabulary.py` for its own drift-report logic — not part of this
ticket's required-reuse set per the AC's exact wording).

**`src/api/read_model_cache.py::ReadModelCache`** (`src/api/read_model_cache.py:31-166`) — single
`threading.RLock()` (`self._lock`, line 40) guarding every read and write method
(`update`, `get_minimal_summary`, `get_entity_dto`, `get_entities_paged`, `clear`,
`evict_expired`, `get_metrics`). This is the exact "RLock-per-method" pattern the ticket AC
requires `ingest.py`'s cache to match — confirmed by direct read, every public method opens
`with self._lock:` as its first statement, never releases early, never holds the lock across an
I/O call (all I/O — `StatePresenter.present_entity` etc. — happens with the lock held, but that
work is in-memory dict construction, not file I/O, so it's fast). `ingest.py`'s rebuild-from-disk
work is comparatively slower (file reads across `tickets/**` + 3 growing JSONL files), so a
literal RLock-around-the-whole-rebuild will block concurrent readers for the rebuild's duration —
`DATA_MODEL.md` §4 names this trade-off explicitly and the user confirmed accepting it given
today's sub-second rebuild time. This is a real design constraint the plan phase must carry
forward unchanged, not re-litigate.

**`src/observability/reporting/history_query.py::HistoricalRunQueryService`**
(`src/observability/reporting/history_query.py:23-30, 151-159`) — `list_historical_runs(limit,
offset)` sorts by `x.started_at` descending then slices `[offset:offset+limit]`;
`get_run_manifest(run_id)` calls `sanitize_id(run_id)` (regex `^[a-zA-Z0-9_\-]+$`, line 10) then
`self.repo.read_manifest(run_id)`, which raises `FileNotFoundError` on a missing run — caught by
`src/api/routes/history.py:51` (`except FileNotFoundError: raise HTTPException(404, ...)`). This
confirms the exact list+detail shape `DATA_MODEL.md` §1 says `/api/runs` and
`/api/runs/{run_id}` should mirror: `Query(default=50, ge=1, le=100)` pagination
(`src/api/routes/history.py:28`), 404 via caught exception, 400 via `ValueError` →
`HTTPException(400, ...)` (`:49-50`).

**`src/api/routes/history.py`** (171 lines, confirmed by full read) — the ticket AC explicitly
says NOT to mirror this file's `response_model=List[dict]` + `.model_dump()` pattern
(`history.py:23, 33`; `:40, 48`). Every route here returns `response_model=List[dict]` or
`response_model=dict` and manually calls `.model_dump()` on typed Pydantic objects
(`RunManifest`, `SweepSummary`) before returning — which throws away the typed-response
enforcement FastAPI would otherwise give for free. This ticket's `models.py` must declare real
typed response models (`response_model=List[TicketSummary]` etc.) and return typed instances
directly, letting FastAPI serialize them — not manually dump to dict first.

**`src/api/routes/health.py`** — confirmed **0 bytes / empty file** by direct read (matches the
ticket's own Assumptions section). No existing `/api/health` pattern exists anywhere in this
codebase to mirror for shape; `DATA_MODEL.md` §1's `GET /api/health` table (four fields:
`status`, `cache_last_rebuilt_ts`, `cache_source_mtimes`, `unparsed_lines`) is the only concrete
spec and should be treated as authoritative.

**`src/api/server.py`** (`:67-111`) — `FastAPI(title=..., ...)` + `CORSMiddleware` +
`app.include_router(x.router, prefix="/api/v1")` per domain router. This dashboard's `main.py`
is a **separate FastAPI app**, not a router mounted onto this one (different port — 8420 vs
8000, per `PROPOSAL.md` §5b — and a hard product-boundary decision already made: this dashboard
reads only `tickets/` + `agent-monitoring/`, never `AuthoritativeState`). The router-mounting
pattern is not directly applicable, but the five routes could still be organized as one
`APIRouter` for consistency with repo convention — a plan-phase decision, not fixed by any AC.

**`tests/architecture/test_api_read_model_guard.py`** (`:11-16`) — the "no raw domain model
exposure" architecture guard scans only `src/api/routes/`, `src/api/ws/`, and `src/api/server.py`
for forbidden `AuthoritativeState`/`EntityState` imports. **`src/api/agent_ops_dashboard/` is not
in this guard's scanned path set.** Since this dashboard never touches `AuthoritativeState` at
all (it only reads ticket markdown + `agent-monitoring/*.jsonl`), this is not a live risk, but it
means the "typed response only" AC for this ticket is enforced by nothing but the review/test
process — there is no existing static architecture guard that would catch a raw-dict leak in
`src/api/agent_ops_dashboard/main.py` the way there is for `src/api/routes/`.

## Mechanics / Engine Constraints

None. This ticket touches no simulation mechanics — it is a read-only observability/tooling
surface over `tickets/**` and `agent-monitoring/*.jsonl`, not `AuthoritativeState` or any
Mechanics Bible chapter. No `docs/mechanics/` chapter or `docs/engine/` contract governs ticket
or agent-monitoring data shape; the closest analog is `docs/observability/read_model_service_contract.md`
(`OBS-READ-MODEL-001`), whose **architecture law** — "No raw state exposure: returned dicts are
shaped projections; internal state objects are never returned" — is the general API-boundary
principle this ticket's own AC #1 restates for a different data domain (tickets/runs, not
`AuthoritativeState`). That contract's specific `ReadModelService` facade and violation guard do
not apply here (different subsystem entirely), but the underlying repo-wide rule ("API/routes
present shaped read models through presenters/schemas, not raw domain objects" — `CLAUDE.md`
Architecture Rule) is directly binding and is exactly what AC #1 and AC #3 test for.

## Parity Ledger Overlap

**No existing parity ledger entry covers this ticket's scope.** Searched
`docs/parity_ledger/infrastructure.yaml` (the "Replay, telemetry, observability, workers"
subsystem file — the correct file for this domain) directly: no entry references
`agent_ops_dashboard`, `ingest.py`, or an agent-monitoring dashboard backend. The closest
existing entries are:

- **`INFRA-210`** (`docs/parity_ledger/infrastructure.yaml:2387-2391`) — the `ReadModelService`
  facade / no-raw-state-exposure guard for the *simulation* read model
  (`src/api/read_model_service.py` + `src/api/read_model_cache.py` +
  `src/api/presenters/state_presenter.py`, `status: verified`,
  `test_path: tests/architecture/test_api_read_model_guard.py::test_no_api_route_directly_imports_authoritative_state`).
  Related by pattern (RLock-per-method reuse, "no raw domain exposure" principle) but a
  **different subsystem** — this ticket's `ingest.py` does not touch `AuthoritativeState` and is
  not covered by INFRA-210's guard or test.
- **`INFRA-274`** (highest existing ID, `docs/parity_ledger/infrastructure.yaml:4430+`) —
  unrelated (Plan-phase gate false-positive fix), noted only to confirm the next available ID.

**This ticket should add a new entry** (next ID: `INFRA-275`) to `infrastructure.yaml` once
implemented, documenting: the new `src/api/agent_ops_dashboard/` module, its typed-response
contract, the RLock-reuse decision, and a `test_path` pointing at the new
`tests/tools/test_agent_ops_dashboard_*.py` (or `tests/api/`) suite this ticket's test plan
defines. No entry is `P0`, so none is a merge-blocking gate for this ticket, but the parity
ledger's own rule ("if logic changes, update the corresponding doc AND the parity ledger entry
... If no entry exists, add one") applies since this is new, real, testable backend behavior.

## Prior Work

- **`stored_artifacts/TCK-20260518-READ-MODEL-CACHE/`** (investigation.md + plan.md, both read in
  full) — the ticket that built `ReadModelCache` itself. Confirms `ReadModelCache` was purpose-built
  for the simulation's `AuthoritativeState`/`DirtySet` invalidation model (tick-driven, dirty-set
  scoped invalidation) — a materially different trigger (`DirtySet` diff) than this ticket's
  trigger (file `mtime` change, no diff granularity, always a full rebuild). Only the **locking
  pattern** (`RLock`-per-method) is the reusable part, not the invalidation logic itself — the
  `ReadModelInvalidationPolicy` class and dirty-entity-ID machinery has no analog needed here.
- **`stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/`** — the exhaustive audit (107/107)
  behind `validate.py`'s legacy-schema tolerance allowlists this ticket must reuse. Confirms the
  allowlists are trustworthy/complete as of that audit, not a to-be-revisited draft.
- **`stored_artifacts/TCK-20260706-MONITORING-REASON-CODE/`** — unrelated feature
  (`reason_code` field on events.jsonl) but confirms the `events.jsonl` schema fields this
  ticket's `TimelineEntry.reason_code` (per `DATA_MODEL.md` §1) must pass through.
- **`tickets/done/TCK-20260607-MON-DASHBOARD.md`, `TCK-20260614-RESOURCE-DASHBOARD.md`,
  `TCK-20260529-OBS-PHASE27-API-DASHBOARD.md`** — three prior "dashboard" tickets, already
  confirmed non-overlapping by the idea doc's own investigation (`PROPOSAL.md` §2). Re-confirmed
  here: none of the three touch `tickets/**` frontmatter parsing or `agent-monitoring/*.jsonl`
  ingestion as a web API.
- The full `experiments/agent_ops_dashboard/` design trail (`PROPOSAL.md`, `DATA_MODEL.md`,
  `IMPLEMENTATION_CONTEXT.md`) is itself the direct precursor to this ticket — already
  investigated exhaustively before this ticket was filed, per its own frontmatter/content. This
  investigation treats those documents as authoritative design input, not something to
  re-derive independently.

## Risks and Open Questions

- **`load_jsonl` name collision, needs an explicit decision (blocks nothing structurally, but
  the AC's wording is ambiguous):** the ticket's Scope line says "load agent-monitoring
  runs.jsonl/tools.jsonl/events.jsonl reusing validate.py's legacy allowlists" and AC #3 says
  "ingest.py imports and calls extract_frontmatter(), load_jsonl(), and validate.py's legacy
  allowlists." There are **two different `load_jsonl` implementations** — `query.py`'s (crashes
  on malformed JSON) and `validate.py`'s (catches `JSONDecodeError`, warns, continues). Given
  AC #3 also names `validate.py`'s allowlists in the same breath, and `DATA_MODEL.md`/`PROPOSAL.md`
  §6's "never crash the API on a malformed/legacy line" principle, the tolerant one
  (`validate.py::load_jsonl`) is very likely the intended one — but `IMPLEMENTATION_CONTEXT.md`
  §1's reuse table explicitly cites `query.py::load_jsonl` by name as "mirror this exact loader."
  **This is a real ambiguity the plan phase must resolve explicitly** (reuse `validate.py`'s via
  import, or mirror `query.py`'s pattern but add the try/except tolerance validate.py has) — not
  a blocking unknown, but silently picking one without stating the reasoning would be a drift
  risk given the AC references both by name.
- **Concurrency test AC is specific about mechanism, not just outcome:** AC #4 requires "a
  concurrency test using an RLock-per-method pattern matching ReadModelCache's exact locking
  approach" — this needs a real multi-threaded test (e.g. one thread mutating source files +
  triggering rebuild while another thread reads), not just a single-threaded assertion that the
  lock object exists. `ReadModelCache` itself has no existing concurrency test to copy the shape
  from (confirmed: no `test_read_model_cache_concurrency.py` exists under `tests/`) — this
  will be new test-writing, not adaptation of an existing pattern.
- **`is_inferred_active` flip-to-false timing (AC #8) is a state-transition property, not a
  single-request assertion** — "no request ever observes a completed run still flagged active"
  requires the rebuild to atomically move a run from the inferred-active set to `runs_by_id` in
  one pass, never leaving a window where both `tools.jsonl` recency and absence from
  `runs_by_id` are simultaneously true post-completion. Given the RLock-around-full-rebuild
  design, this should hold naturally (the whole rebuild is one critical section), but it is
  worth an explicit test rather than an assumption.
- **`docs/REGISTRY.yaml` still needs to be scanned for ticket entries at all?** No — per
  `IMPLEMENTATION_CONTEXT.md` §2 and the ticket's own Scope, direct frontmatter parsing across
  the three lifecycle directories is authoritative; `REGISTRY.yaml` is confirmed not used as a
  source at all for this ticket. Restated here only to make explicit that the investigator found
  no reason to revisit that decision.
- **`tickets/todos/` contains nested subfolders with `SEQUENCE.md`-style non-ticket files**
  (per `CLAUDE.md`'s Workflow Rule, e.g. `tickets/todos/simq/`) — `ingest.py`'s directory walk
  must only parse files matching the `TCK-YYYYMMDD-*.md` ticket naming convention, skipping
  `SEQUENCE.md` and any other folder-level metadata files, or frontmatter parsing will throw on
  non-ticket markdown. Not called out explicitly in any of the three design docs — a real gap the
  plan phase should account for.
- **`runs.jsonl`'s six documented legacy schema generations lack `run_id` uniformity in some
  variants** (`docs/agent-monitoring/schema.md` "Known Limitations") — `FOLDER-*`/`EPIC-*` batch
  wrapper records use a bare `status` field, not `final_status`. `TicketSummary.matching_runs`
  joins on `run_id == ticket_id`; a `FOLDER-*`/`EPIC-*` run_id will never match any single
  ticket_id (expected, not a bug), but `RunSummary.final_status` must resolve from either field
  per `validate.py`'s own `_record_is_complete` pattern — this is a NOT-optional detail already
  implied by AC #7/#8's `runs.jsonl` normalization language but easy to under-implement if only
  the current schema's `final_status` field is read.

## Anti-Drift Hazards

- **Do not implement the swap-based (build-outside-lock, atomic-pointer-swap) concurrency design**
  from `DATA_MODEL.md` §4's "slightly better option" — that was explicitly **rejected** in favor
  of the simpler RLock-per-method reuse. It reads as the more sophisticated/correct choice on
  its own merits, which makes it a real temptation to "improve" toward during implementation;
  the decision is final and dated 2026-07-16, not left open.
- **Do not build the frontend, build/serve tooling, or Makefile targets** — explicitly Out of
  Scope, owned by three sibling tickets (`AGENTOPS-TICKETS-VIEW`, `AGENTOPS-ACTIVITY-GANTT`,
  `AGENTOPS-REPLAY-TIMELINE`) and `AGENTOPS-BUILD-SERVE`. `main.py` needs no `StaticFiles` mount
  in this ticket even though `PROPOSAL.md`'s architecture diagram shows one — that belongs to the
  build/serve ticket.
- **Do not touch `.claude/workflows/implement-ticket.js` or add a `phase`/`agent` field to
  `tools.jsonl`'s live rows** — the instrumentation gap (`live_tail` items having `phase: null`,
  `agent: null`) is a confirmed, deliberate, independent sibling ticket
  (`idea_agent_monitoring_live_phase_label.md`), explicitly Out of Scope here per both the idea
  doc and this ticket's own Out of Scope section.
- **Do not add retention/rotation logic for `agent-monitoring/*.jsonl`** — confirmed unbounded
  growth is a named, accepted risk for this ticket specifically (Out of Scope line + Assumptions
  section), not something to "fix while I'm in here." `src/observability/reporting/retention.py`'s
  `RetentionPolicy`/`RetentionManager` govern only `data/runs/` (simulation artifacts) — do not
  extend or repurpose that class for `agent-monitoring/`.
- **Do not collapse `matching_runs` to one row.** This was the single most heavily-investigated
  decision in the source material (43/618 real collision rate) — any implementation shortcut
  that picks "most recent" or "first" and drops the rest directly violates AC #2 and reverses a
  decision already confirmed with the user.
- **Do not conflate `status` (frontmatter doc-lifecycle field) with `workflow_status` (`##
  Status` body field).** `DATA_MODEL.md` §1 names this exact collapsing mistake explicitly as a
  hazard — both are called "status" in the source ticket file, and a careless single-field
  mapping would silently merge two different concepts.
- **`GET /api/health`'s `status` field must always be `"ok"`** (per `DATA_MODEL.md` §1 and
  `PROPOSAL.md` §6's "this endpoint itself never fails" principle) — do not make it reflect
  parse-error counts or degrade to a non-`"ok"` value; that information belongs in
  `unparsed_lines`, not `status`.
