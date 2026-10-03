---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality, dashboard]
---

# Test Plan — TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD

## Regression Surface

**unit / done_checker_static.py:**
- `tests/tools/test_done_checker_static.py` — specifically the `check_monitoring_write_recorded`
  block (lines ~936-1002): `test_check_monitoring_write_recorded_fails_when_run_missing`,
  `test_check_monitoring_write_recorded_fails_when_events_missing`,
  `test_check_monitoring_write_recorded_passes_when_both_present`,
  `test_check_monitoring_write_recorded_applies_under_hotfix_tier`. All 4 currently construct
  explicit single-file `tmp_path / "runs.jsonl"` / `tmp_path / "events.jsonl"` fixtures and pass
  them as `runs_path=`/`events_path=` kwargs — these will need call-signature updates matching
  whatever parameter shape Plan chooses (see investigation.md's Open Question). Every other test
  in this file (other `check_*` functions) must show zero behavior change — confirmed only 2 call
  sites of `_jsonl_rows_for_run_id` exist and both are inside `check_monitoring_write_recorded`.
- `tests/tools/test_finalize_tag_drift_wiring.py` — asserts ordering/adjacency of
  `check_monitoring_write_recorded` relative to `check_tag_drift` in the workflow source text; does
  not construct fixture files, should be unaffected by an internal path-resolution change as long
  as the function name/call-site text in `implement-ticket.js` is untouched.

**unit / agent_ops_dashboard ingest & cache:**
- `tests/tools/test_agent_ops_dashboard_ingest.py` (1028 lines) — broadest surface. The
  `_write_runs_events_tools` helper (lines 77-91) and its ~6 call sites (lines 912-1024) write the
  old flat `tmp_path/agent-monitoring/{runs,events,tools}.jsonl` layout; must be repointed to
  `tmp_path/agent-monitoring/data/<week>/{runs,events,tools}.jsonl`. Every other test in this file
  not touching those 3 sources (ticket parsing, glossary merge, tag facets, pagination) must remain
  byte-for-byte unaffected.
- `tests/tools/test_agent_ops_dashboard_stats.py` (429 lines) — `_write_runs`/`_write_events`/
  `_write_tools` helpers (lines 24-36) write the same old flat layout; all tests in this file
  construct their fixtures exclusively through these 3 helpers (confirmed via grep — only 3 direct
  path refs in the whole file), so fixing the helpers should fix the whole file's fixtures in one
  place.
- `tests/tools/test_agent_ops_dashboard_concurrency.py` (199 lines) — `_write_ticket` (appends to
  `runs_file` across simulated concurrent writers, lines 41-55) and a `tools_file`/`runs_file`
  direct-write pair (~lines 135-173). This file specifically exercises the `RLock`/rebuild-under-
  concurrency contract — must keep asserting the same lock/rebuild behavior after the path change,
  not just get its fixtures relocated.
- `tests/tools/test_agent_ops_dashboard_api.py` (301 lines) — 8 direct single-file writes across
  several tests (facet fixtures, malformed-line handling at line 178-180, health-endpoint fixtures
  around lines 250-280). Includes at least one test writing deliberately malformed content
  (`"garbage\ngarbage\ngarbage\n"`, line 179) that must still exercise the same
  tolerant-skip-and-count behavior once under the new multi-week path.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` — asserts `main.py` never mounts
  `StaticFiles`; does not construct `runs`/`events`/`tools` fixtures per the grep above (only
  `tests/tools/test_agent_ops_dashboard_api_boundary.py` matched the DashboardCache-adjacent grep
  for unrelated reasons — confirm no fixture writes exist there before assuming zero-touch).
- `tests/tools/test_agent_ops_dashboard_glossary.py`,
  `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`,
  `tests/tools/test_agent_ops_dashboard_serve.py` — confirmed via grep to construct no
  `runs`/`events`/`tools` fixtures; must show zero change in outcome (glossary/frontend-surface/
  serve-module tests are structurally independent of the 3 JSONL sources).

**integration (regression, not new):**
- `tests/integrity/` — no direct reference to these 3 paths found via this ticket's own scoped
  grep; not expected to be touched, included here only as a broad regression check since Verify's
  prior ticket (child 2) surfaced unexpected collateral there for a related but different reason
  (path retirement, not path resolution).

## New Tests Required

- **Name**: `test_check_monitoring_write_recorded_finds_pair_in_non_current_week`
  **Category**: unit
  **Verifies**: AC #1 — `check_monitoring_write_recorded` returns `PASS` for a `run_id` whose
  matching `runs.jsonl`/`events.jsonl` rows live only in an older, non-newest week folder (e.g.
  `agent-monitoring/data/2026-W23/`), not just the current/newest one, proving the fix globs across
  weeks rather than reading a single fixed file or only the latest week.
  **Where**: `tests/tools/test_done_checker_static.py`, in the existing
  `check_monitoring_write_recorded` test block.

- **Name**: `test_check_monitoring_write_recorded_still_fails_when_absent_from_all_weeks`
  **Category**: unit
  **Verifies**: negative-path regression companion to the above — a `run_id` present nowhere
  across any week folder still correctly returns `FAIL`, proving the glob doesn't silently
  false-positive by matching an unrelated row.
  **Where**: `tests/tools/test_done_checker_static.py`.

- **Name**: `test_dashboard_cache_rebuild_aggregates_across_multiple_weeks`
  **Category**: unit
  **Verifies**: AC #3 — `DashboardCache._rebuild()` (or its public effect via `get_runs`/
  `get_agent_monitoring_stats`) correctly aggregates `runs`, `events`, and `tools` rows written
  across 2+ distinct week folders into single unified `_runs_all`/`_events_all`/`_tools_all` lists
  — not just reading one week and silently dropping the rest.
  **Where**: `tests/tools/test_agent_ops_dashboard_ingest.py`.

- **Name**: `test_dashboard_cache_maybe_rebuild_detects_staleness_from_non_newest_week_write`
  **Category**: unit
  **Verifies**: AC #4 — for each of the 3 sources independently (`runs`, `events`, `tools`), a
  write (mtime bump) to a file in a week folder that is *not* the most-recently-created week folder
  still causes `_maybe_rebuild()` to detect staleness and rebuild — proving the max-mtime-across-
  weeks computation in `_current_source_state()`, not a computation that only watches the newest
  week's file. Should reuse the existing `_bump_mtime` helper pattern
  (`test_agent_ops_dashboard_ingest.py:70-74`) applied to an older week's file.
  **Where**: `tests/tools/test_agent_ops_dashboard_ingest.py`.

- **Name**: `test_dashboard_cache_tools_all_nonempty_against_real_sharded_layout`
  **Category**: unit (regression, explicitly required by AC #5)
  **Verifies**: the `_tools_file` bug is actually fixed — `DashboardCache._tools_all` and its
  derived `_tools_by_seq`/`_tools_by_run_recent` are non-empty and content-correct when fixture
  `tools.jsonl` rows are written under the real post-migration
  `agent-monitoring/data/<week>/tools.jsonl` shape (not the old flat path this bug silently read
  from). This is the dedicated regression the ticket calls out by name — must fail against the
  pre-fix code (i.e. must actually exercise the multi-week path, not accidentally pass against a
  test fixture that happens to also populate the old flat location).
  **Where**: `tests/tools/test_agent_ops_dashboard_ingest.py` or
  `tests/tools/test_agent_ops_dashboard_stats.py` (wherever `skill_usage`/Skill-Usage-adjacent
  fixtures already live — confirm exact placement against
  `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD`'s own test file choice
  at implementation time).

- **Name**: `test_current_source_state_empty_data_dir_returns_zero_not_crash`
  **Category**: unit (edge case / architecture guard)
  **Verifies**: `_current_source_state()`'s new max-mtime-across-glob computation returns `0.0`
  (matching today's single-file "doesn't exist" precedent) rather than raising `ValueError` from
  `max()` over an empty sequence, when `agent-monitoring/data/` doesn't exist or contains no
  matching week folders yet (a fresh `tmp_path` fixture with no data written at all). Guards
  against the specific empty-glob footgun flagged in investigation.md's Risks section.
  **Where**: `tests/tools/test_agent_ops_dashboard_ingest.py`.

- **Name**: `test_dashboard_public_api_surface_and_lock_unchanged`
  **Category**: architecture guard
  **Verifies**: AC #6 — `DashboardCache`'s public method names (`get_tickets`, `get_runs`,
  `get_run`, `get_timeline`, `get_health`, `get_agent_monitoring_stats`, `get_ticket_corpus_stats`,
  `get_glossary`) are unchanged, and it still constructs exactly one `threading.RLock()` instance
  (not per-source locks) — a structural guard against scope creep into the locking pattern, which
  the ticket explicitly forbids touching. Can be a lightweight `inspect`-based check (mirrors
  `test_ingest_never_imports_query_module`'s existing `inspect.getsource` pattern in this same
  file) rather than a full behavioral test.
  **Where**: `tests/tools/test_agent_ops_dashboard_ingest.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
pytest tests/tools/test_finalize_tag_drift_wiring.py -v
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/tools/test_agent_ops_dashboard_serve.py -v
```

Broader confirmation sweep before Finalize (matches child 2's own precedent of a wider net to
catch collateral, given this ticket touches shared read paths):

```
pytest tests/tools/ -k "done_checker or agent_ops_dashboard or monitoring_write" -v
```

Never `pytest tests/` unscoped.

## Anti-Drift Test Guards

- **`test_dashboard_public_api_surface_and_lock_unchanged`** (above) directly guards against the
  AC #6 "no public API / no locking pattern change" constraint — the single highest-value guard
  against scope creep in this ticket, since the fix necessarily touches `__init__`/
  `_current_source_state`/`_rebuild`, all adjacent to the lock.
- **Existing `test_ingest_reuses_extract_frontmatter_and_validate_allowlists` and
  `test_ingest_never_imports_query_module`** (already in `test_agent_ops_dashboard_ingest.py`)
  must continue passing unmodified — they guard the "reuse, not reimplement" architecture rule for
  this module generally; a glob-based rewrite must not accidentally reimplement
  `validate.load_jsonl`'s tolerant parsing inline instead of continuing to call it per-file.
- **`test_get_ticket_corpus_stats`/`test_get_glossary`-adjacent tests** (wherever they live) should
  be run as part of the full-file regression pass even though they're declared out of scope — they
  share the same file and same `DashboardCache` instance construction pattern
  (`ingest.DashboardCache(repo_root=tmp_path)`), so a mistake in `__init__` could silently break
  them even though their own logic is untouched.
- **`check_monitoring_write_recorded`'s hotfix-tier test**
  (`test_check_monitoring_write_recorded_applies_under_hotfix_tier`) guards that the function still
  has no `tier` parameter and no NA branch after the path-resolution change — the function's own
  docstring calls this out as a deliberate design decision (CLAUDE.md's Hard Rule applies
  regardless of tier); a well-intentioned refactor must not accidentally introduce a tier-skip
  branch while restructuring the path logic.
- **A malformed-line test must survive** (e.g. `test_agent_ops_dashboard_api.py`'s
  `"garbage\ngarbage\ngarbage\n"` fixture around line 179) — confirms the tolerant-skip-on-
  unparseable-line behavior (`validate.load_jsonl`'s per-line try/except) still applies identically
  when reading is spread across multiple globbed files, not just a single file where a bad line's
  position is easy to reason about.
- **No test should assert a raw dict/response-shape change on any `/api/*` route.** Per
  `docs/observability/agent_ops_dashboard_contract.md`'s Architecture Law and this ticket's own
  scope ("no presenter/API-route shape built on top of it... changes"), the existing
  `response_model=` Pydantic assertions in `test_agent_ops_dashboard_api.py`/`_stats.py` must stay
  green untouched — any red here signals the fix leaked past the internal read-path layer into the
  typed response boundary, which is out of scope.
