---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD
artifact_type: plan
tags: [agent-monitoring, observability, data-quality, dashboard]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD

## Summary

Both `done_checker_static.py::check_monitoring_write_recorded` and
`ingest.py::DashboardCache` still read the retired flat
`agent-monitoring/{runs,events,tools}.jsonl` files (child 2's migration `git rm`'d them),
so both currently degrade silently to empty/false-FAIL results against the real
`agent-monitoring/data/<week>/{runs,events,tools}.jsonl` layout child 2 produced. The fix in
both modules is the same shape: replace single-file reads with a sorted glob over
`agent-monitoring/data/*/<filename>`, concatenating rows across every ISO-week shard —
mirroring the already-landed precedent in `record_events.py::compute_tool_stats()`
(`sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))`). Each module gets its own
small glob helper rather than a new shared cross-module utility (see Anti-Drift Notes for
rationale) — this keeps `tools/gate_checks/` and `src/api/agent_ops_dashboard/` free of a new
coupling neither currently has. `check_monitoring_write_recorded`'s parameter shape changes
from two single-`Path` params (`runs_path`, `events_path`) to one `data_root: Path` param,
since `runs.jsonl`/`events.jsonl` are physical siblings under every week folder and the
function's one real call site (`implement-ticket.js`) passes no overrides today, so there is
no external contract to preserve — only the 4 existing tests' call signatures need updating.
`DashboardCache` keeps its constructor signature (`repo_root: Path`) and its entire public
method surface untouched; only its three private file-path fields, `_current_source_state()`,
and `_rebuild()` change internally, plus a dedicated fix restoring `_tools_all` (and its
`_tools_by_seq`/`_tools_by_run_recent` derivatives) to real, non-empty content. Two docs
(`docs/observability/agent_ops_dashboard_contract.md`, `docs/parity_ledger/infrastructure.yaml`
INFRA-275) get their stale flat-path descriptions corrected in the same session, per
investigation.md's finding that the ticket's own "Related Docs: None" claim was wrong.

## Ratified Design Decision (investigation.md's open question)

**Decision: option (b) — change the parameter shape**, collapsed further to a *single*
`data_root: Path = Path("agent-monitoring/data")` parameter (not two separate
`runs_root`/`events_root` roots).

**Rationale:**
- The one real call site (`implement-ticket.js:1616-1623`) passes **zero** overrides today —
  there is no external caller contract that a "keep the param shape" approach would actually be
  preserving. Option (a)'s appeal (avoid changing a public-ish parameter) doesn't apply here.
- `runs.jsonl` and `events.jsonl` are physical siblings under the exact same
  `agent-monitoring/data/<week>/` directory (confirmed via child 2's landed migration layout,
  investigation.md "Prior Work") — a single `data_root` naturally expresses "the week-sharded
  corpus root," matching the real filesystem shape, rather than two roots that would always be
  passed identically in practice.
- All 4 existing tests already construct fixtures via explicit `tmp_path`-rooted paths and pass
  them as kwargs — they must change their fixture layout regardless of which option is chosen
  (the fixture data itself must become week-sharded to exercise the fix), so there is no
  call-signature-stability benefit left to option (a) once that's accounted for. Given that, the
  parameter shape that matches the real directory structure is strictly better.
- A single-`Path`-typed param reinterpreted internally as "a signal to glob a directory" (option
  (a) as literally read) would leave the parameter's type annotation (`Path`) lying about what
  it accepts (a file vs. a directory root) — worse for a reader than an honest rename.

## Steps

### Step 1 — Add the multi-week glob helper and rewrite `check_monitoring_write_recorded`

**Files:** `tools/gate_checks/done_checker_static.py`

**Change:**
- Read confirmed at `tools/gate_checks/done_checker_static.py:64-79` — `_jsonl_rows_for_run_id(path: Path, run_id: str) -> list[dict]` is a single-file, tolerant-per-line reader with an `.exists()` guard returning `[]` for a missing path. It has exactly 2 call sites (lines 705, 708), both inside `check_monitoring_write_recorded` (confirmed via investigation.md and direct grep) — safe to repurpose as the per-shard worker in a loop; leave its body and signature completely unchanged so its own existing behavior (tolerant skip of malformed lines) is reused, not reimplemented.
- Add a new module-level helper directly below `_jsonl_rows_for_run_id`:
  ```python
  def _jsonl_rows_for_run_id_across_weeks(data_root: Path, filename: str, run_id: str) -> list[dict]:
      """Return every parsed JSON row whose run_id == run_id, across every
      agent-monitoring/data/<week>/{filename} shard under data_root (sorted for
      determinism — mirrors record_events.py::compute_tool_stats()'s
      `sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))` precedent).
      A data_root that doesn't exist, or exists with no matching week folders,
      yields an empty glob and returns [] — matching the old single-file
      ".exists() -> []" precedent, not an error."""
      rows: list[dict] = []
      for path in sorted(data_root.glob(f"*/{filename}")):
          rows.extend(_jsonl_rows_for_run_id(path, run_id))
      return rows
  ```
- Change `check_monitoring_write_recorded`'s signature (currently at lines 689-693, read confirmed):
  ```python
  def check_monitoring_write_recorded(
      ticket_id: str,
      data_root: Path = Path("agent-monitoring/data"),
  ) -> tuple[str, str]:
  ```
  Removing `runs_path`/`events_path` entirely — confirmed the sole real call site
  (`.claude/workflows/implement-ticket.js:1616-1623`) passes no path kwargs, so this is not a
  breaking change to any live caller.
- Rewrite the body (currently lines 705-718, read confirmed) to:
  ```python
  run_rows = _jsonl_rows_for_run_id_across_weeks(data_root, "runs.jsonl", ticket_id)
  if not run_rows:
      return ("FAIL", f"No row with run_id == {ticket_id} found under {data_root}/*/runs.jsonl")
  event_rows = _jsonl_rows_for_run_id_across_weeks(data_root, "events.jsonl", ticket_id)
  if not event_rows:
      return (
          "FAIL",
          f"{data_root}/*/runs.jsonl has a row for {ticket_id} but "
          f"{data_root}/*/events.jsonl has zero matching rows",
      )
  return (
      "PASS",
      f"{data_root}/*/runs.jsonl ({len(run_rows)} row(s)) and {data_root}/*/events.jsonl "
      f"({len(event_rows)} row(s)) both have entries for {ticket_id}",
  )
  ```
- Do not add a `tier` parameter or an NA branch — the function's own docstring (lines 694-697,
  read confirmed) documents this omission as a deliberate CLAUDE.md Hard Rule decision; nothing
  in this step touches that.
- **Other writers to this shared resource**: `agent-monitoring/data/<week>/runs.jsonl` is written
  by `tools/agent-monitoring/record_run.py`, and `.../events.jsonl` by
  `tools/agent-monitoring/record_events.py` — both route their appends through
  `tools/agent-monitoring/writer.py::write_lines` (read confirmed,
  `tools/agent-monitoring/writer.py:1-40`), which uses an `O_CREAT|O_EXCL` lock-file protocol
  with bounded retry for atomic appends. `check_monitoring_write_recorded` is read-only (no
  write path in this function at all) and is invoked once, synchronously, near the end of the
  Finalize phase in `implement-ticket.js` — by that point in the pipeline the run/event rows for
  the ticket under check have already been durably appended by their respective writers in
  earlier phases, so there is no read-during-write race window this function needs to guard
  against; it only needs to read whatever week folder(s) currently exist, which the glob already
  handles correctly regardless of how many weeks are present.
- **Do NOT touch**: `_extract_section_text`, `_count_rows_for_ticket`, `check_tag_drift`, or any
  other `check_*` function in this file — none of them call `_jsonl_rows_for_run_id` or
  `_jsonl_rows_for_run_id_across_weeks`.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` (after Step 2's test updates).

### Step 2 — Update the 4 existing `check_monitoring_write_recorded` tests + add the 2 new required tests

**Files:** `tests/tools/test_done_checker_static.py`

**Change:**
- Read confirmed at `tests/tools/test_done_checker_static.py:940-1004`: `_write_jsonl(path, rows)`
  helper (940-944) plus 4 tests
  (`test_check_monitoring_write_recorded_fails_when_run_missing`,
  `test_check_monitoring_write_recorded_fails_when_events_missing`,
  `test_check_monitoring_write_recorded_passes_when_both_present`,
  `test_check_monitoring_write_recorded_applies_under_hotfix_tier`), each constructing
  `runs_path = tmp_path / "runs.jsonl"` / `events_path = tmp_path / "events.jsonl"` directly
  (flat, no week subfolder) and passing them as `runs_path=`/`events_path=` kwargs.
- For each of the 4 tests: change fixture paths to nest under one deterministic week folder,
  e.g. `tmp_path / "2026-W23" / "runs.jsonl"` and `tmp_path / "2026-W23" / "events.jsonl"`
  (`_write_jsonl`'s existing `path.parent.mkdir(parents=True, exist_ok=True)` at line 943
  already handles creating that new nested directory — no helper signature change needed), and
  change the call to `check_monitoring_write_recorded("TCK-FAKE", data_root=tmp_path)` (passing
  `tmp_path` itself as `data_root`, since the glob pattern is `data_root.glob("*/{filename}")`
  and `tmp_path/"2026-W23"/...` is exactly one level under `tmp_path`).
- Add the 2 new tests from test_plan.md, in the same block:
  ```python
  def test_check_monitoring_write_recorded_finds_pair_in_non_current_week(tmp_path):
      old_week = tmp_path / "2026-W23"
      _write_jsonl(old_week / "runs.jsonl", [{"run_id": "TCK-OLD-WEEK"}])
      _write_jsonl(old_week / "events.jsonl", [{"run_id": "TCK-OLD-WEEK"}])
      # A newer, unrelated week folder must not be required or interfered with.
      new_week = tmp_path / "2026-W36"
      _write_jsonl(new_week / "runs.jsonl", [{"run_id": "TCK-OTHER"}])
      _write_jsonl(new_week / "events.jsonl", [{"run_id": "TCK-OTHER"}])

      status, evidence = check_monitoring_write_recorded("TCK-OLD-WEEK", data_root=tmp_path)
      assert status == "PASS"
      assert "TCK-OLD-WEEK" in evidence

  def test_check_monitoring_write_recorded_still_fails_when_absent_from_all_weeks(tmp_path):
      _write_jsonl(tmp_path / "2026-W23" / "runs.jsonl", [{"run_id": "TCK-OTHER-1"}])
      _write_jsonl(tmp_path / "2026-W36" / "runs.jsonl", [{"run_id": "TCK-OTHER-2"}])

      status, evidence = check_monitoring_write_recorded("TCK-NOWHERE", data_root=tmp_path)
      assert status == "FAIL"
      assert "No row with run_id == TCK-NOWHERE" in evidence
  ```
**Do NOT touch:** any other test block in this file (e.g. `run_static_precheck`/
`run_finalize_selfcheck` tests above line 935) — confirmed unrelated to
`check_monitoring_write_recorded`.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — all 6
`check_monitoring_write_recorded` tests pass; `pytest tests/tools/test_finalize_tag_drift_wiring.py -v`
stays green (asserts ordering/adjacency in workflow source text only, untouched by this step).

### Step 3 — Add glob helpers and fix `DashboardCache.__init__` / `_current_source_state` / `_rebuild`

**Files:** `src/api/agent_ops_dashboard/ingest.py`

**Change:**
- Read confirmed at `src/api/agent_ops_dashboard/ingest.py:111-123`:
  `load_jsonl_counted(path: Path) -> tuple[list[dict], int]` already does tolerant per-file
  JSONL loading with an unparsed-line count, via `validate.load_jsonl` (imported at line 42,
  aliased `load_jsonl = validate.load_jsonl` at line 103) — reused unchanged as the per-shard
  worker, matching this module's own stated "reuse, never reimplement" rule (module docstring,
  lines 8-16).
- Add two new module-level helpers directly below `load_jsonl_counted` (after line 123):
  ```python
  def _week_shard_paths(data_root: Path, filename: str) -> list[Path]:
      """Every agent-monitoring/data/<week>/{filename} shard under data_root, sorted for
      determinism — mirrors record_events.py::compute_tool_stats()'s
      `sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))` precedent. A
      data_root with no matching week folders yields an empty list (not an error)."""
      return sorted(data_root.glob(f"*/{filename}"))

  def _max_mtime(paths: list[Path]) -> float:
      """max() mtime across paths, defaulting to 0.0 for an empty list — guards the
      empty-glob ValueError footgun (max() over an empty sequence raises without
      `default=`), matching the old single-file "doesn't exist -> 0.0" precedent."""
      return max((p.stat().st_mtime for p in paths if p.exists()), default=0.0)

  def _load_jsonl_counted_multi(data_root: Path, filename: str) -> tuple[list[dict], int]:
      """Read + concatenate every agent-monitoring/data/<week>/{filename} shard (sorted,
      ISO-week order) via load_jsonl_counted per file, summing unparsed-line counts
      across all shards. Safe against double-counting: (run_id, seq) is globally unique
      across weeks (see record_events.py::compute_tool_stats's docstring) and each shard
      is read exactly once here."""
      all_records: list[dict] = []
      total_unparsed = 0
      for path in _week_shard_paths(data_root, filename):
          records, unparsed = load_jsonl_counted(path)
          all_records.extend(records)
          total_unparsed += unparsed
      return all_records, total_unparsed
  ```
- In `DashboardCache.__init__` (read confirmed, lines 472-478): replace lines 474-476
  (`self._runs_file` / `self._events_file` / `self._tools_file`, each a single hardcoded `Path`)
  with one field:
  ```python
  self._data_root = repo_root / "agent-monitoring" / "data"
  ```
  Grep-confirmed (`grep -n "_runs_file\|_events_file\|_tools_file" src/api/agent_ops_dashboard/ingest.py`
  and across `tests/tools/*.py`, `src/api/agent_ops_dashboard/*.py`) that these 3 fields are read
  only inside `_current_source_state()` (lines 504-506) and `_rebuild()` (lines 519-521) — no
  other method, no test, and no other module reads them directly, so this rename has a fully
  bounded blast radius.
- In `_current_source_state()` (read confirmed, lines 497-508): replace the 3 `_mtime(self.*_file)`
  calls with the new glob-aware helper, keeping the inline `_mtime` closure only for the
  `tickets` computation (unchanged, still walks `self._tickets_root` via `walk_ticket_dirs`):
  ```python
  def _current_source_state(self) -> dict[str, float]:
      def _mtime(p: Path) -> float:
          return p.stat().st_mtime if p.exists() else 0.0

      ticket_files = walk_ticket_dirs(self._tickets_root)
      tickets_state = float(len(ticket_files)) + sum(_mtime(p) for p in ticket_files)
      return {
          "runs.jsonl": _max_mtime(_week_shard_paths(self._data_root, "runs.jsonl")),
          "events.jsonl": _max_mtime(_week_shard_paths(self._data_root, "events.jsonl")),
          "tools.jsonl": _max_mtime(_week_shard_paths(self._data_root, "tools.jsonl")),
          "tickets": tickets_state,
      }
  ```
  The return shape (`{"runs.jsonl": float, "events.jsonl": float, "tools.jsonl": float,
  "tickets": float}`) is unchanged — `_maybe_rebuild()`'s dict-equality staleness check (line 513,
  read confirmed) needs no change.
- In `_rebuild()` (read confirmed, lines 517-573): replace lines 519-521
  (`load_jsonl_counted(self._runs_file)` etc.) with:
  ```python
  runs_all, runs_unparsed = _load_jsonl_counted_multi(self._data_root, "runs.jsonl")
  events_all, events_unparsed = _load_jsonl_counted_multi(self._data_root, "events.jsonl")
  tools_all, tools_unparsed = _load_jsonl_counted_multi(self._data_root, "tools.jsonl")
  ```
  Every downstream line in `_rebuild()` (grouping, joins, `self._runs_all = runs_all`, etc.,
  lines 523-573) is otherwise unchanged — it already consumes `runs_all`/`events_all`/`tools_all`
  as plain lists, agnostic to whether they came from one file or several. The
  `self._unparsed_lines = {...}` assignment at lines 568-572 keeps its exact 3-key shape,
  now holding summed counts across shards instead of one file's count — this is the fix for
  the Anti-Drift Hazard about `_unparsed_lines` semantics flagged in investigation.md.
- This directly fixes the `_tools_file` bug named in the ticket's title and AC #5: `tools_all` is
  now built from `_load_jsonl_counted_multi(self._data_root, "tools.jsonl")` against the real
  on-disk shards, no longer permanently `[]`.
- **Other writers to this shared resource**: same 3 writers as Step 1
  (`record_run.py`/`record_events.py`/a `post_tool_hook.py` tools-writer — all routed through
  `tools/agent-monitoring/writer.py::write_lines`'s atomic lock-file append, confirmed via
  `tools/agent-monitoring/writer.py:1-16`'s module docstring). `DashboardCache` is documented
  read-only (module docstring, `ingest.py:4-6`, "this module never writes") and already handled
  the single-file version of this same race via its existing on-demand `_maybe_rebuild()`
  pattern (re-reads only when `_current_source_state()` differs from the last-cached state,
  called under `self._lock` at the top of every public method) — this step does not change that
  pattern, only widens what each source-state computation reads from one file to N week shards.
  No new race is introduced: a write mid-glob at worst means the glob either includes or excludes
  that week's very newest write depending on timing, exactly the same class of staleness window
  the single-file version already had (resolved on the *next* request via `_maybe_rebuild()`).
**Do NOT touch:** `DashboardCache`'s constructor signature (`repo_root: Path = _REPO_ROOT`
stays exactly as-is), `self._lock = threading.RLock()`, any public method
(`get_tickets`/`get_runs`/`get_run`/`get_timeline`/`get_health`/
`get_agent_monitoring_stats`/`get_ticket_corpus_stats`/`get_glossary`), or
`get_ticket_corpus_stats`/`get_glossary`'s own independent fresh-read logic (neither touches
`_runs_file`/`_events_file`/`_tools_file`/`_data_root` at all, confirmed by investigation.md).
**Verify:** `pytest tests/tools/test_agent_ops_dashboard_ingest.py -v` (after Step 4's fixture
updates and Step 5's new tests).

### Step 4 — Repoint the 4 dashboard test files' fixture helpers to the week-sharded layout

**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py`,
`tests/tools/test_agent_ops_dashboard_stats.py`,
`tests/tools/test_agent_ops_dashboard_concurrency.py`,
`tests/tools/test_agent_ops_dashboard_api.py`

**Change:** Introduce one shared constant per file, `_FIXTURE_WEEK = "2026-W23"`, and route every
fixture write through it, so the write path becomes
`tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK / "<source>.jsonl"` instead of
`tmp_path / "agent-monitoring" / "<source>.jsonl"`. Per-file detail (all call sites read
confirmed via grep this session):

- `test_agent_ops_dashboard_ingest.py`: update `_write_runs_events_tools` (lines 77-91) — its 3
  internal `tmp_path / "agent-monitoring" / "{runs,events,tools}.jsonl"` constructions (84, 87,
  90) each gain `/ "data" / _FIXTURE_WEEK` before the filename. Also update the 8 inline
  single-file constructions outside that helper (confirmed at lines 290, 312, 382, 407, 432, 447,
  483, and 957 — `tools_file`/`runs_file` direct writes in
  `test_active_run_completion_flips_inferred_flag_and_timestamps`,
  `test_legacy_runs_jsonl_schema_generations_do_not_crash_ingest`,
  `test_run_summary_carries_provider_execution_id_ticket_id_when_present`,
  `test_run_summary_labels_legacy_record_as_legacy_not_none_silently`,
  `test_get_runs_filters_by_provider_and_execution_id`,
  `test_provider_claude_code_legacy_value_tolerated_not_normalized_as_new_write`, and one more
  near line 957) the same way. `_bump_mtime` (lines 70-74) is unchanged — it already operates on
  whatever `Path` it's given, so it works identically on a week-nested file.
- `test_agent_ops_dashboard_stats.py`: update the 3 helpers `_write_runs`/`_write_events`/
  `_write_tools` (lines 24-36) — every test in this file constructs fixtures exclusively through
  these 3 helpers (confirmed via grep — no other direct path reference), so this is a
  helper-only fix for the whole file.
- `test_agent_ops_dashboard_concurrency.py`: update `_write_ticket` (lines 31-55, appends to
  `runs_file` across simulated concurrent writers) and the inline `tools_file`/`runs_file`
  direct-write pair (~lines 135-173) to the same nested path. Keep every write in this file
  targeting the *same single* `_FIXTURE_WEEK` folder — this file specifically exercises the
  `RLock`/rebuild-under-concurrency contract, and spreading its writes across multiple weeks
  would silently change what it asserts (per investigation.md's explicit warning on this file).
- `test_agent_ops_dashboard_api.py`: update the 8 direct single-file writes (confirmed at lines
  46-47, 157-158, 178-180, 195-196, 206-207, 250-251, 274-275, 279-280) the same way, including
  the malformed-content fixture at line 179 (`events_file.write_text("garbage\ngarbage\ngarbage\n")`)
  — its content stays byte-for-byte identical, only its path gains the `data/<week>/` nesting, so
  the tolerant-skip-and-count assertion it backs continues to exercise the same malformed-line
  behavior, now read through `_load_jsonl_counted_multi`'s per-shard `load_jsonl_counted` call.
- `test_agent_ops_dashboard_api_boundary.py`, `test_agent_ops_dashboard_glossary.py`,
  `test_agent_ops_dashboard_frontend_api_surface.py`, `test_agent_ops_dashboard_serve.py`:
  confirmed via this session's grep (no `_runs_file`/`_events_file`/`_tools_file`/`runs.jsonl`/
  `events.jsonl`/`tools.jsonl` hits) to construct no fixtures under the 3 sources — leave
  completely untouched.
**Do NOT touch:** any fixture helper or inline write unrelated to `runs`/`events`/`tools` sources
in these 4 files (ticket fixtures via `_write_ticket_raw`/`_init_repo_skeleton`, tag-registry
fixtures via `_write_tag_registry_fixture`, glossary/layer-registry fixtures) — none of these
read through `_data_root`/`_current_source_state`/`_rebuild`.
**Verify:** `pytest tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_concurrency.py
tests/tools/test_agent_ops_dashboard_api.py -v` — every pre-existing test in these 4 files passes
unmodified in outcome (only fixture *paths* moved, not fixture *content* or assertions).

### Step 5 — Add the new required `DashboardCache` tests

**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py`

**Change:** Add, in the same file, using the `_FIXTURE_WEEK` constant and `_bump_mtime` helper
from Step 4:
- `test_dashboard_cache_rebuild_aggregates_across_multiple_weeks` (AC #3): write distinct
  `runs`/`events`/`tools` rows under two different week folders (e.g. `2026-W23` and
  `2026-W36`) directly under `tmp_path / "agent-monitoring" / "data"`, construct
  `ingest.DashboardCache(repo_root=tmp_path)`, and assert `cache.get_runs(limit=100)` /
  `cache._events_all` (or its public-surface equivalent via `get_timeline`) / `cache._tools_all`
  each contain rows from *both* weeks, not just one.
- `test_dashboard_cache_maybe_rebuild_detects_staleness_from_non_newest_week_write` (AC #4): seed
  two week folders, call a public method once to force an initial rebuild, then use `_bump_mtime`
  on the *older* week's file for each of `runs.jsonl`/`events.jsonl`/`tools.jsonl` in turn (3
  sub-cases or 3 separate tests), and assert the next public-method call reflects the new content
  — proving `_current_source_state()`'s `_max_mtime` over the glob, not just the newest week's
  mtime, drives invalidation.
- `test_dashboard_cache_tools_all_nonempty_against_real_sharded_layout` (AC #5, the dedicated
  named regression): write `tools.jsonl` rows only under
  `tmp_path / "agent-monitoring" / "data" / _FIXTURE_WEEK / "tools.jsonl"` (the real
  post-migration shape, never the old flat path), construct the cache, and assert
  `cache._tools_all` is non-empty and its derived `cache._tools_by_seq` /
  `cache._tools_by_run_recent` are populated and content-correct (matching `run_id`/`seq` keys
  from the fixture rows). This test must fail against the pre-fix code (i.e., it must not
  accidentally also populate the old flat `agent-monitoring/tools.jsonl` location as a
  belt-and-suspenders fixture that would mask the bug).
- `test_current_source_state_empty_data_dir_returns_zero_not_crash`: construct
  `ingest.DashboardCache(repo_root=tmp_path)` against a completely fresh `tmp_path` (no
  `agent-monitoring/data/` directory created at all), call `cache._current_source_state()`
  directly, and assert it returns `0.0` for `"runs.jsonl"`/`"events.jsonl"`/`"tools.jsonl"`
  without raising — guards the `max()`-over-empty-glob `ValueError` footgun `_max_mtime` guards
  against.
- `test_dashboard_public_api_surface_and_lock_unchanged` (AC #6): mirror the existing
  `test_ingest_never_imports_query_module`'s `inspect.getsource`-based pattern in this same file
  — assert `DashboardCache`'s public method names are exactly
  `{"get_tickets", "get_runs", "get_run", "get_timeline", "get_health",
  "get_agent_monitoring_stats", "get_ticket_corpus_stats", "get_glossary"}` (plus dunder/private
  methods excluded), and that `inspect.getsource(DashboardCache.__init__)` contains exactly one
  `threading.RLock()` construction.
**Do NOT touch:** `test_ingest_reuses_extract_frontmatter_and_validate_allowlists` or
`test_ingest_never_imports_query_module` — run them as part of the regression pass but do not
modify their bodies; they guard an unrelated architecture rule this ticket must not weaken.
**Verify:** `pytest tests/tools/test_agent_ops_dashboard_ingest.py -v -k "multiple_weeks or
staleness or tools_all_nonempty or empty_data_dir or public_api_surface"`.

### Step 6 — Update `docs/observability/agent_ops_dashboard_contract.md`

**Files:** `docs/observability/agent_ops_dashboard_contract.md`

**Change:**
- Line 16 (read confirmed): change "`agent-monitoring/{runs,events,tools}.jsonl`" to
  "`agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl` (every week shard, globbed and
  concatenated)".
- Line 157 (read confirmed): change "All file reads over `tickets/**` and
  `agent-monitoring/*.jsonl` live in this module" to "All file reads over `tickets/**` and
  `agent-monitoring/data/*/{runs,events,tools}.jsonl` (globbed across every ISO-week folder) live
  in this module".
- Scan the rest of the file for any other verbatim reference to the flat 3-file layout beyond
  these 2 confirmed lines before finishing this step (the investigation only confirmed these 2,
  but the file should be internally consistent once this ticket lands).
**Do NOT touch:** any other section of this contract doc (routes table, response-model
descriptions, glossary-merge description) — none of it references the 3 JSONL source paths'
physical layout.
**Verify:** No automated test — manual read-through confirming both lines now match the Step 3
implementation; `docs/REGISTRY.yaml` regeneration (Finalize's own post-migration self-check)
picks this up automatically since it's a `docs/` file.

### Step 7 — Update `docs/parity_ledger/infrastructure.yaml` INFRA-275

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Read confirmed at `docs/parity_ledger/infrastructure.yaml:4878-4897` — `INFRA-275`'s
`text` field states "ingest.py owns all file reads over `tickets/{inprogress,done,todos}/` and
`agent-monitoring/{runs,events,tools}.jsonl`" and its `v2_evidence` cites `ingest.py` line numbers
for the constructor/rebuild/cache behavior this ticket's diff shifts. Use
`tools/parity_ledger_writer.py` (the sanctioned, schema-validating updater — per this repo's own
prior-incident guidance against raw full-file YAML edits corrupting this file) to update:
- `text`: replace the flat-path phrase with the week-sharded glob description (same wording as
  Step 6's doc fix, for consistency).
- `v2_evidence`: append a new evidence note (following this entry's existing pattern of appended,
  dated notes rather than deleting prior ones — visible in the excerpt already citing
  TCK-20260717-TICKETS-TABLE-PAGINATION and TCK-20260718-STATUS-FACET-CANONICAL as prior
  append-only notes) citing this ticket's ID and the new line numbers/shape for
  `DashboardCache.__init__`, `_current_source_state()`, `_rebuild()`, and the 3 new module-level
  helpers (`_week_shard_paths`, `_max_mtime`, `_load_jsonl_counted_multi`) added in Step 3 —
  exact line numbers to be filled in from the actual diff at implementation time, not guessed
  here.
- `status` stays `verified`; `priority` stays `P2` (unchanged — this is a description-accuracy
  correction to an already-verified entry, not a status change).
**Do NOT touch:** any other entry in `infrastructure.yaml`, or `INFRA-275`'s `legacy_evidence`
field (`null`, unrelated to this ticket).
**Verify:** No dedicated automated test (P2, not P0 — no strict pre-existing `test_path` gate
applies per investigation.md); confirm `python3 tools/parity_ledger_writer.py` (or its validation
mode, per that tool's own usage) reports the file still schema-valid after the update.

## Scope Guards

- Do not touch `tools/agent-monitoring/build_index.py`, `generate_retro.py`, `manifest.py`,
  `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
  `done_ticket_monitoring_coverage.py`, `validate.py`, or `query.py` — child 3's territory.
- Do not touch the codex subsystem (`tools/agent_replay_codex/`, child 5) or referential-integrity
  tooling (child 6).
- Do not modify any `done_checker_static.py` check other than `check_monitoring_write_recorded`
  (AC #2 is explicit: "Zero unrelated functional change to any other check").
- Do not change `DashboardCache`'s public method names, its constructor signature
  (`repo_root: Path = _REPO_ROOT`), or its single-`threading.RLock()`-per-method locking pattern
  (AC #6, and this ticket's Out of Scope section).
- Do not touch `get_ticket_corpus_stats` or `get_glossary` — both are documented, deliberate
  exceptions to the mtime-cache pattern reading unrelated source files, and both are explicitly
  named as out-of-scope in investigation.md's Anti-Drift Hazards.
- Do not change any `/api/*` route's response shape, any `response_model=` Pydantic type, or any
  presenter built on top of `DashboardCache` — this ticket's fix is confined to the internal
  read-path layer beneath the existing public method surface.
- Do not create a new shared cross-module glob-helper module — each of `done_checker_static.py`
  and `ingest.py` gets its own small, duplicated glob helper (see Anti-Drift Notes for rationale).
- Do not touch `docs/agent-monitoring/schema.md` — already correctly updated by child 2 for the
  write-path/schema layer; this ticket's docs scope is read-path only (the 2 files named in
  Steps 6-7).

## Dependency Map

- Step 1 (done_checker_static.py fix) and Step 2 (its tests) are sequential (Step 2 depends on
  Step 1's new signature existing) but are entirely independent of Steps 3-5 (no shared file, no
  shared helper, no import between the two modules — confirmed in investigation.md).
- Step 3 (ingest.py fix) must land before Step 4 (test fixture repointing) and Step 5 (new tests)
  can pass, since both exercise `DashboardCache` against the new `_data_root`-based read path.
  Step 4 and Step 5 can be written in either order relative to each other but both require Step 3.
- Step 6 (contract doc) and Step 7 (parity ledger) both describe the Step 3 implementation and
  should be done after Step 3's diff is final (so line-number citations in Step 7's `v2_evidence`
  are accurate) — but have no code dependency on each other or on Steps 1-2.
- Recommended order: Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7, running the
  full scoped test sweep after Step 5 and again after Step 7 (docs-only, should be a no-op on
  test results).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A test asserts `check_monitoring_write_recorded` finds a real run/event pair in a non-`current`, older week folder | Step 1, Step 2 | `test_check_monitoring_write_recorded_finds_pair_in_non_current_week` |
| Zero unrelated functional change to any other `done_checker_static.py` check | Step 1 (scoped to `check_monitoring_write_recorded` + its new private helper only) | Full `pytest tests/tools/test_done_checker_static.py -v` run — all non-`check_monitoring_write_recorded` tests pass unmodified |
| A test proves `DashboardCache._rebuild()` aggregates `runs`/`events`/`tools` from 2+ week folders | Step 3, Step 5 | `test_dashboard_cache_rebuild_aggregates_across_multiple_weeks` |
| A test proves `_maybe_rebuild()` detects staleness from a write to a non-newest week folder, for each of the 3 sources | Step 3, Step 5 | `test_dashboard_cache_maybe_rebuild_detects_staleness_from_non_newest_week_write` |
| Regression test proving the `_tools_file` bug is fixed (`_tools_all`/`_tools_by_seq`/`_tools_by_run_recent` non-empty and correct) | Step 3, Step 5 | `test_dashboard_cache_tools_all_nonempty_against_real_sharded_layout` |
| No change to `DashboardCache`'s public API surface or its single-`RLock()` pattern | Step 3 (explicit Do NOT touch) | `test_dashboard_public_api_surface_and_lock_unchanged` |

## Anti-Drift Notes

- **Parameter-shape decision is final, not a placeholder**: `check_monitoring_write_recorded` now
  takes one `data_root: Path` parameter, not `runs_path`/`events_path`. All 4 pre-existing tests
  and both new tests in Step 2 must use this exact new call shape — do not half-migrate (e.g.
  leaving one test still passing `runs_path=`).
- **No shared cross-module helper**: `_jsonl_rows_for_run_id_across_weeks` (in
  `done_checker_static.py`) and `_week_shard_paths`/`_load_jsonl_counted_multi` (in `ingest.py`)
  are deliberately separate, duplicated implementations — matching this repo's existing precedent
  (`record_events.py::compute_tool_stats()`'s glob line is itself inlined, not factored out) and
  avoiding a new import coupling between `tools/gate_checks/` (process/gate tooling) and
  `src/api/agent_ops_dashboard/` (production API code), which currently do not import from each
  other at all.
- **`_unparsed_lines`'s semantics must become a sum across shards, not the last file's count
  silently overwriting earlier ones** — this was called out explicitly in investigation.md as an
  easy-to-miss bug; Step 3's `_load_jsonl_counted_multi` handles this correctly by accumulating
  `total_unparsed` in a loop.
- **`compute_inferred_active`'s `ACTIVE_WINDOW_MINUTES = 10` heuristic will start firing correctly
  in production for the first time in a while**, once `tools_by_run_recent` is built from the real
  multi-week `tools_all` instead of a permanently-empty list. This is a correctness improvement
  from fixing the `_tools_file` bug, not a new regression — call it out explicitly in
  Implementation Notes when this ticket is implemented so it is not mistaken for unintended
  behavior change during review.
- **Malformed-line fixtures must survive path changes with byte-identical content** — Step 4's
  `test_agent_ops_dashboard_api.py` malformed-content fixture
  (`"garbage\ngarbage\ngarbage\n"`) must keep its exact content; only its file path moves under
  `data/<week>/`. This is the test that proves tolerant-skip-and-count behavior still works when
  reads span multiple globbed files, not just a single file where a bad line's position is easy
  to reason about.
- **Test file scope in Step 4 is bounded to files with confirmed fixture writes** — do not touch
  `test_agent_ops_dashboard_api_boundary.py`, `test_agent_ops_dashboard_glossary.py`,
  `test_agent_ops_dashboard_frontend_api_surface.py`, or `test_agent_ops_dashboard_serve.py`;
  this session's grep confirmed zero `runs`/`events`/`tools` fixture construction in any of them.
- **`test_done_ticket_monitoring_coverage.py` is not this ticket's responsibility** — it is a
  known, pre-existing, out-of-scope collateral failure from child 2's migration (per that child's
  own documented deviation) covering a different check
  (`tools/agent-monitoring/done_ticket_monitoring_coverage.py`, explicitly child 3's territory).
  If it is still failing when this ticket's diff lands, do not treat that as evidence this
  ticket's own changes are broken.

## Deviations

- **Step 5's `test_dashboard_public_api_surface_and_lock_unchanged` public-method-name set**: this
  plan's Step 5 text lists 8 public method names (`get_tickets`, `get_runs`, `get_run`,
  `get_timeline`, `get_health`, `get_agent_monitoring_stats`, `get_ticket_corpus_stats`,
  `get_glossary`). A direct read of `src/api/agent_ops_dashboard/ingest.py` at implementation time
  found a 9th real public method, `get_bulk_timeline` (added by a prior ticket,
  TCK-20260720-BULK-RUN-TIMELINE, and already exercised by several pre-existing tests in this same
  test file). The implemented test asserts the real 9-name set, not the plan's 8-name list —
  asserting the plan's incomplete list would have made this specific architecture guard falsely
  fail against already-correct, already-shipped code. No other part of Step 5 or the AC map was
  affected by this correction.
