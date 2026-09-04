---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality, dashboard]
---

# Investigation — TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD

## Current Behavior

### `tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded` (lines 689-718)

- Signature: `check_monitoring_write_recorded(ticket_id, runs_path: Path =
  Path("agent-monitoring/runs.jsonl"), events_path: Path =
  Path("agent-monitoring/events.jsonl"))`. Both defaults point at the two now-`git rm`'d
  monolithic files from child 2's migration.
- Body calls `_jsonl_rows_for_run_id(runs_path, ticket_id)` (defined lines 64-79) — a single-file
  reader that returns `[]` immediately if `path.exists()` is false (line 67-68), otherwise
  per-line tolerant `json.loads` filtered on `row.get("run_id") == run_id`. Same call against
  `events_path`. `PASS` only if both non-empty; `FAIL` with a specific evidence string otherwise.
- **Confirmed call site**: `.claude/workflows/implement-ticket.js:1616-1623` invokes this via
  `python3 -c "..."` passing **only `sys.argv[1]` (the ticket_id) — no `runs_path`/`events_path`
  override at all**. This means the fix must live in the function's *default* behavior, not in
  what the caller passes — there is exactly one call site and it always uses the defaults.
- **Exact failure mode right now**: `Path("agent-monitoring/runs.jsonl").exists()` is `False`
  post-migration (child 2's `git rm`), so `_jsonl_rows_for_run_id` returns `[]` immediately (no
  exception — the `.exists()` guard swallows it), and `check_monitoring_write_recorded` returns
  `FAIL: "No row with run_id == {ticket_id} found in agent-monitoring/runs.jsonl"` for every ticket,
  unconditionally, regardless of whether a real run/event pair exists in the new
  `agent-monitoring/data/<week>/` shards. This is loud-but-non-blocking (per the function's own
  docstring and CLAUDE.md's Hard Rule — a monitoring-write failure never fails the workflow), so
  the live symptom is a spurious `WARNING: agent-monitoring write for {tid} could not be verified`
  logged on every ticket close, not a blocked pipeline. Confirmed via direct source read this
  session (not inferred) — the file literally does not exist in the working tree
  (`ls agent-monitoring/` shows `data/`, `retro/`, and unrelated dirs, no `runs.jsonl`/
  `events.jsonl`).
- `_jsonl_rows_for_run_id` has exactly 2 call sites, both inside `check_monitoring_write_recorded`
  (lines 705, 708) — no other function in this file reuses it, so changing its shape/contract has
  a fully bounded blast radius within this file.

### `src/api/agent_ops_dashboard/ingest.py::DashboardCache`

- `__init__` (lines 472-495): hardcodes the 3 single-file constants confirmed by the ticket —
  `self._runs_file = repo_root / "agent-monitoring" / "runs.jsonl"` (474),
  `self._events_file = repo_root / "agent-monitoring" / "events.jsonl"` (475),
  `self._tools_file = repo_root / "agent-monitoring" / "tools.jsonl"` (476). No `_runs_root`/
  `_events_root`/`_tools_root` or glob-capable field exists.
- `_current_source_state()` (497-508): computes one mtime per source key
  (`"runs.jsonl"`, `"events.jsonl"`, `"tools.jsonl"`, plus a `"tickets"` aggregate) via a local
  `_mtime(p)` helper that itself guards `p.exists()` (498-499, mirrors the same silent-degrade
  pattern as `load_jsonl_counted`) — returns `0.0` for a missing path rather than raising. Because
  `self._tools_file` already points at the retired path, `_mtime(self._tools_file)` is always
  `0.0` today, so `tools.jsonl`'s entry in `_source_mtimes` never changes across rebuilds (it's
  permanently `0.0` == `0.0`), meaning **no write to any real `tools` shard ever triggers a
  rebuild via the tools-mtime channel** — cache staleness for `tools_all` is masked, not just its
  content being empty.
- `_maybe_rebuild()` (510-515): compares `_current_source_state()` against `self._source_mtimes`
  by dict equality; calls `_rebuild()` only on a diff (or on first call, `self._last_rebuilt_ts is
  None`). Re-read pattern is **on-demand at request time** (called from within each public method,
  under the shared `RLock`), not on a timer and not eagerly cached forever — confirmed no
  background thread/scheduler in this file.
- `_rebuild()` (517-573): calls `load_jsonl_counted(self._runs_file)` /
  `(self._events_file)` / `(self._tools_file)` (519-521) — three single-file reads, each degrading
  silently to `([], 0)` if the path doesn't exist (`load_jsonl_counted`, ingest.py:111-123,
  guards `path.exists()` at line 119). **Confirmed exact silent-failure behavior**: no crash
  anywhere in this path — `runs_all`/`events_all`/`tools_all` are simply empty lists, which then
  flow into `_group_runs_by_id`, `events_by_run`, `tools_by_seq`/`tools_by_run_recent`, and
  `_tools_all` (retained since TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-
  DASHBOARD specifically so `get_agent_monitoring_stats` can feed real `tools_all` into
  `compute_retro_metrics()`'s `tools` parameter for `skill_usage`). This matches the ticket's
  claim precisely: `DashboardCache._tools_all` (and its derivatives `_tools_by_seq`/
  `_tools_by_run_recent`) is silently empty today, degrading `runs`/`events`-derived stats too
  (both those files are also gone) — not just the Skill Usage view, the ticket's own framing
  slightly understates the blast radius: `runs.jsonl`/`events.jsonl` are equally gone, so
  `get_runs`, `get_run`, `get_timeline`, and every `AgentMonitoringStats` field derived from
  `runs_all`/`events_all` (not just `skill_usage`) are silently empty/zeroed right now, in
  production, for the live dashboard process.
- `get_ticket_corpus_stats` and `get_glossary` are documented (and confirmed by reading their
  bodies) as deliberate exceptions to the mtime-cache pattern — they re-read their own sources
  fresh on every call and do not touch `_runs_file`/`_events_file`/`_tools_file` at all. Out of
  this ticket's blast radius.
- `get_agent_monitoring_stats` also calls `tools/retrieval_cache.py::read_cache_access_log()`
  fresh every request (a separate SQLite file, not one of the 3 JSONL sources) — also out of
  scope, confirmed unrelated to the 3 hardcoded paths.

## Mechanics / Engine Constraints

Not applicable in the Mechanics-Bible/engine-contract sense — this is observability/tooling
infrastructure, not simulation logic. The relevant constraint is architectural, not a game-law:
`docs/architecture/` has no ADR specifically for this dashboard; the closest governing document is
`docs/observability/agent_ops_dashboard_contract.md` (see below), which is a contract doc, not a
Mechanics Bible chapter.

## Docs Requiring Update

- `docs/observability/agent_ops_dashboard_contract.md`: two places state the physical read paths
  in a way that will become factually wrong once `DashboardCache` globs `agent-monitoring/data/*/`
  instead of 3 fixed files — line 16 ("exposing read-only, typed projections over `tickets/**` and
  `agent-monitoring/{runs,events,tools}.jsonl`") and line 157 ("All file reads over `tickets/**`
  and `agent-monitoring/*.jsonl` live in this module"). Both describe the pre-child-2 monolithic
  layout, which no longer exists on disk at all (confirmed: `git log` shows this doc untouched
  since before this epic — neither child 1 nor child 2 updated it, and child 2's own Related Docs
  section only names `docs/agent-monitoring/schema.md`, not this contract doc). This is the file
  this ticket most directly documents the internals of (`DashboardCache.__init__`,
  `_current_source_state`, `_rebuild`, the `_runs_all`/`_events_all`/`_tools_all` retention
  rationale) — it must be updated to describe the new multi-week glob read pattern once
  implemented, not left describing a layout that is already gone.
- `docs/parity_ledger/infrastructure.yaml`, entry `INFRA-275`: its `text` field states verbatim
  "ingest.py owns all file reads over `tickets/{inprogress,done,todos}/` and
  `agent-monitoring/{runs,events,tools}.jsonl`" and its `v2_evidence` cites specific `ingest.py`
  line numbers for the `DashboardCache`/`RLock`/join/heuristic behavior this ticket's diff will
  shift (constructor field names, `_rebuild()` body, line numbers throughout will move once the
  3 single-file reads become multi-week glob reads). Per CLAUDE.md's Authoritative Mechanics Rule
  ("If logic changes, update the corresponding doc AND the parity ledger entry ... in the same
  session"), this entry's `text`/`v2_evidence` must be refreshed to describe the new read pattern
  and cite the new line numbers. Confirmed (via `git log`/grep) that child 1 explicitly did **not**
  touch INFRA-275 — its own evidence note at `infrastructure.yaml` around line 5098 states "INFRA-
  275's own ingest.py/models.py claims are unaffected (dashboard reader code untouched)" because
  child 1 was write-path-only. This ticket is the first to actually change `ingest.py`'s read
  behavior since INFRA-275 was last verified, so the entry is genuinely stale once this ticket
  lands, not merely a candidate.

The ticket's own "Related Docs" section states "None beyond code-level accuracy — no doc
currently claims `DashboardCache`'s internal file-resolution shape (that's an implementation
detail, not documented API behavior)." This investigation found that claim to be incorrect on
direct source read: `docs/observability/agent_ops_dashboard_contract.md` and
`docs/parity_ledger/infrastructure.yaml`'s INFRA-275 both explicitly document the exact 3
single-file paths as part of `ingest.py`'s contract/parity evidence, not merely implying them —
both are corrected to Format 1 (must-update) bullets above rather than left as the ticket's
original "None."

`docs/agent-monitoring/schema.md` was already updated by child 2 (its own Implementation Notes,
Step 10) to describe the physical migration of `runs.jsonl`/`events.jsonl`/`tools/` into
`agent-monitoring/data/<week>/`; it documents the write-path/schema layer, not `ingest.py`'s
internal read implementation, and this ticket's scope (read-path only, in `ingest.py` and
`done_checker_static.py`) does not require further changes there — excluded deliberately, not
overlooked.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml`, `INFRA-275` (priority `P2`, status `verified`) — the
  Agent Ops Dashboard backend entry covering `ingest.py`'s `DashboardCache` read/cache behavior.
  Requires a `text`/`v2_evidence` update per above; not a P0, so no strict pre-existing
  `test_path` gate applies, but its listed `test_path` (`tests/tools/test_agent_ops_dashboard_
  ingest.py`, `test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_concurrency.py`,
  `test_agent_ops_dashboard_api_boundary.py`) all exist and are exactly the regression surface
  this ticket's diff touches — confirmed present, not a broken path.
- No `done_checker_static.py`/gate-check-specific parity ledger entry was found (this file is
  process/gate tooling, not a simulation-facing subsystem the parity ledger tracks) — searched
  `infrastructure.yaml` for `done_checker`/`check_monitoring_write_recorded` with no hits beyond
  the already-known non-parity-ledger references (SKILL.md, test files). No entry to flag or
  create for that half of this ticket's scope.

## Prior Work

- `tickets/done/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY.md` (child 1): established the
  glob-based read precedent this ticket must match —
  `sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))` in
  `tools/agent-monitoring/record_events.py::compute_tool_stats()` (line 65), reading the union of
  every ISO-week folder's `tools.jsonl`, safe against double-counting because `(run_id, seq)` is
  globally unique across weeks. This is the exact convention to mirror for both halves of this
  ticket's scope.
- `tickets/done/TCK-20260903-MONITORING-DATA-MIGRATION.md` (child 2, hard prerequisite, confirmed
  landed): produced the real on-disk layout this ticket now reads —
  `agent-monitoring/data/<YYYY-Www>/{runs,events,tools}.jsonl` for weeks `2026-W23` through
  `2026-W36`, plus a `agent-monitoring/data/unknown-week/` fallback bucket (for the rare historical
  row missing a parseable timestamp — confirmed this bucket is a real, populated directory, not
  hypothetical, and matches the same glob pattern `agent-monitoring/data/*/` trivially since it's
  just another subdirectory). Its own Implementation Notes flagged the `ingest.py` dashboard-gap
  as an explicitly-deferred, already-known item for "children 3/4" — this ticket is exactly that
  follow-through, not new discovery.
- `stored_artifacts/TCK-20260716-AGENTOPS-DASHBOARD-BACKEND/investigation.md` and
  `TCK-20260718-AGENTOPS-STATS-API` (design context for `DashboardCache`'s original single-`RLock`
  cache shape and the `AgentMonitoringStats` field mirroring) — useful background but describes
  the pre-migration monolithic-file world; not a source of new constraints for this ticket beyond
  confirming the RLock/public-API-surface pattern this ticket's AC #6 says must not change.
- `tools/agent-monitoring/migrate_tools_shards.py` (prior epic, `TCK-20260902-MONITORING-SHARD-
  MIGRATION`) — the reference the ticket's own body cites for the `_tools_file` bug class already
  fixed once, in a sibling tool (`weight_sensitivity_check.py`, child 3's territory) — confirms
  this is a recurring, well-understood bug class across this epic, not a one-off.

## Risks and Open Questions

- **Open design question (blocks Plan, not pre-answered here)**: `check_monitoring_write_recorded`
  is called with **zero path overrides** at its one real call site
  (`implement-ticket.js:1616-1623`) — it only ever runs on its defaults. Its existing tests
  (`tests/tools/test_done_checker_static.py:947-1001`, 4 tests) all pass explicit single-file
  `runs_path=`/`events_path=` `tmp_path` fixtures and assert single-file behavior. A pure "change
  the default value" fix (e.g. defaulting to a directory-glob pattern instead of a `Path`) changes
  the parameter's *meaning*, not just its value — `_jsonl_rows_for_run_id(path, run_id)` takes one
  `Path` and calls `.exists()`/`.read_text()` directly, incompatible with a glob root without a
  signature/body change. The Plan phase must decide: (a) keep `runs_path`/`events_path` as
  single-`Path` params but repoint their default to a genuinely different resolution strategy
  (e.g. a small helper that globs and concatenates, called internally, with the existing params
  repurposed or replaced), or (b) change the parameter shape entirely (e.g. `runs_root: Path =
  Path("agent-monitoring/data")`) and update all 4 existing tests' call signatures accordingly.
  Both are compatible with the AC's requirement of a non-newest-week lookup test; this is a real
  implementation-shape decision, not resolved here — do not assume either without deciding in
  Plan.
- **`_current_source_state()`'s dict-equality staleness check must stay correct under the new
  max-mtime-across-weeks computation.** The return shape (`{"runs.jsonl": float, "events.jsonl":
  float, "tools.jsonl": float, "tickets": float}`) can stay structurally identical (one float per
  source key, now computed as `max()` across a glob rather than a single `.stat().st_mtime`) —
  confirmed this preserves the existing equality-comparison invalidation logic in
  `_maybe_rebuild()` without a structural change to `_source_mtimes`. Glob-with-no-matches (e.g. a
  totally empty `agent-monitoring/data/` in a fresh test `tmp_path` before any week folder exists)
  must resolve to `0.0`, matching today's single-file "doesn't exist -> 0.0" precedent — a naive
  `max(...)` over an empty generator raises `ValueError`, so this must be guarded explicitly (e.g.
  `max((...), default=0.0)`).
- **Test fixture surface is real but bounded**: 4 test files (`test_agent_ops_dashboard_ingest.py`,
  `test_agent_ops_dashboard_stats.py`, `test_agent_ops_dashboard_concurrency.py`,
  `test_agent_ops_dashboard_api.py`) all write fixture data via small per-file helper functions
  (`_write_runs_events_tools`, `_write_runs`/`_write_events`/`_write_tools`, and inline
  `runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"` writes) that target the old flat
  single-file layout. Because each file funnels through a small number of helpers (not
  hundreds of inline writes), updating those helpers to write under
  `tmp_path / "agent-monitoring" / "data" / "<week>" / "<source>.jsonl"` is the correct,
  bounded fix — confirmed via direct grep that call-site counts are low (3-11 per file) relative
  to total test count in each file, so this is a helper-level fix, not a mass per-test rewrite.
  `test_agent_ops_dashboard_concurrency.py` additionally *appends* to `runs_file` across
  simulated concurrent writers (lines ~41-55) — this pattern must still target a single
  deterministic week folder per test (not spread across weeks) unless a test specifically wants
  to exercise the new cross-week aggregation, to avoid accidentally changing what that
  concurrency test is asserting.
- **Caching/performance (explicitly out of scope to solve, per the ticket's own framing — noting
  as a Plan-phase consideration only)**: `_current_source_state()` now does a glob + per-file
  `stat()` for 3 sources on every `_maybe_rebuild()` call (i.e. on every request, since that's
  where it's invoked from). With 15 weeks currently on disk (`2026-W23` through `2026-W36` plus
  `unknown-week`) this is cheap today; growth is unbounded over the life of the repo (one new
  folder every ISO week, forever) — not a blocker for this ticket, but worth flagging for whoever
  eventually revisits `DashboardCache`'s performance characteristics.
- **`test_done_ticket_monitoring_coverage.py`** was named in child 2's own Implementation Notes as
  one of 7 collateral test failures from the legacy-path retirement (it reads the real
  `agent-monitoring/` directory directly). Grepping this ticket's own scope (`done_checker_static
  .py::check_monitoring_write_recorded` only) confirms this test file is a *different* check
  (`tools/agent-monitoring/done_ticket_monitoring_coverage.py`, explicitly listed in this ticket's
  own "Out of Scope" as child 3's territory) — not this ticket's responsibility to fix, but if it
  is still failing when this ticket's diff lands, do not assume this ticket's own regression run
  is broken; that failure is out-of-scope and pre-existing per child 2's own documented deviation.

## Anti-Drift Hazards

- **Do not touch any other `done_checker_static.py` check.** The AC is explicit
  ("Zero unrelated functional change to any other check"); `_jsonl_rows_for_run_id` has exactly 2
  call sites, both inside `check_monitoring_write_recorded` — safe to modify its contract without
  touching sibling checks, but a diff review should confirm no other function's behavior shifted.
- **Do not change `DashboardCache`'s public method surface or its single `threading.RLock()`
  pattern** — the ticket's Out of Scope and AC both call this out explicitly; every public method
  already opens `with self._lock:` as its first statement (confirmed by direct read of
  `get_tickets`, `_maybe_rebuild`) — the fix belongs entirely inside `_current_source_state()`,
  `_rebuild()`, and `__init__`'s file-path fields, never in the lock/method-signature layer.
- **`get_ticket_corpus_stats` and `get_glossary` must not be touched** — they are the two
  documented, deliberate exceptions to the mtime-cache pattern and read entirely different source
  files (`tickets/done/` walk, `glossary_registry.jsonl`/`layer_registry.jsonl`), unrelated to
  `runs`/`events`/`tools`. Easy to accidentally scope-creep into "while I'm in here" refactoring
  these — explicitly out of scope.
- **Do not silently change `_unparsed_lines`'s semantics.** `_rebuild()` currently sets
  `self._unparsed_lines = {"runs.jsonl": runs_unparsed, "events.jsonl": events_unparsed,
  "tools.jsonl": tools_unparsed}` — one int per source, feeding `HealthStatus`/`/api/health`
  (per the contract doc, `unparsed_lines` counts are surfaced there, though `status` itself stays
  hardcoded `"ok"` regardless). Once reads are multi-week, this must become a *sum* across all
  matched week files per source, not just the last file's count or the first file's count silently
  overwriting earlier ones in a loop.
- **`compute_inferred_active`'s `ACTIVE_WINDOW_MINUTES = 10` heuristic** depends on
  `tools_by_run_recent` being correctly populated from the *real* multi-week `tools_all` — fixing
  the `_tools_file` bug will, for the first time in a while, make this heuristic actually fire in
  production; this is a correctness improvement, not a regression, but it means
  `is_inferred_active` behavior on the live dashboard will visibly change (a currently-running run
  will start correctly showing as inferred-active) — worth calling out explicitly in Implementation
  Notes when this ticket is implemented, so it isn't mistaken for an unintended side effect.
- **Do not conflate `runs_path`/`events_path` (gate-check side) with `_runs_file`/`_events_file`
  (dashboard side)** — these are two independent fixes in two unrelated modules with no shared
  helper function between them (confirmed: `done_checker_static.py` and `ingest.py` do not import
  from each other). A shared multi-week-glob *utility function* does not currently exist anywhere
  in the repo for this exact purpose — `record_events.py::compute_tool_stats()`'s glob line is
  inlined, not factored into a reusable helper. Whether to extract a shared helper (e.g. in
  `tools/agent-monitoring/` or a new small module) or duplicate the glob logic twice is a Plan-
  phase decision; either is architecturally acceptable given the current precedent is itself
  inlined per-caller, not factored out.
