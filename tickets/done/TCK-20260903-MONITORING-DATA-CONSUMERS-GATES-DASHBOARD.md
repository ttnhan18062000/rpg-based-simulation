---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, dashboard]
---

# TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD

## Title
Migrate `done_checker_static.py`'s monitoring-write check and `agent_ops_dashboard/ingest.py`'s
`DashboardCache` to the unified per-week `agent-monitoring/data/` layout, fixing the live
`DashboardCache._tools_file` ground-truth bug

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 4 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. Split out from the core-consumers ticket
(child 3) deliberately, because both files here carry a different risk profile than internal
`tools/agent-monitoring/` tooling: `done_checker_static.py::check_monitoring_write_recorded` gates
every ticket's DoD closure, and `src/api/agent_ops_dashboard/ingest.py::DashboardCache` is real,
production API-facing code (not a dev tool) — both warrant independent, more careful review rather
than being folded into the larger core-consumers change.

`tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded` (default args
`runs_path: Path = Path("agent-monitoring/runs.jsonl")` line 691,
`events_path: Path = Path("agent-monitoring/events.jsonl")` line 692) was explicitly out of scope for
the prior tools-only epic (it never referenced `tools.jsonl` at all) — now squarely in scope, since
this epic shards `runs`/`events` too.

`src/api/agent_ops_dashboard/ingest.py::DashboardCache.__init__` hardcodes 3 single-file paths (lines
474-476): `self._runs_file`, `self._events_file`, `self._tools_file`. **Confirmed via direct source
read this session: `self._tools_file` already points at the retired legacy
`agent-monitoring/tools.jsonl` path** — the same live bug class as `record_events.py`'s (fixed in
child 1) and `weight_sensitivity_check.py`'s (fixed in child 3). `_rebuild()` (line 521) calls
`load_jsonl_counted(self._tools_file)`, which degrades silently (no crash) to an empty `tools_all`
list, feeding `_tools_by_seq`/`_tools_by_run_recent` and ultimately the Skill Usage / cost-proxy
dashboard views with silently-wrong (empty) data since the prior epic's `git rm`.

## Scope
- `tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded`: change its default
  path resolution (or the arguments callers pass) to glob `agent-monitoring/data/*/runs.jsonl` and
  `agent-monitoring/data/*/events.jsonl` (all week folders), confirming a real run/event pair exists
  anywhere in the corpus for the ticket under check — not just in one hardcoded file.
- `src/api/agent_ops_dashboard/ingest.py::DashboardCache`:
  - `_current_source_state()`: change the per-source mtime computation for `"runs.jsonl"`,
    `"events.jsonl"`, `"tools.jsonl"` keys to the max mtime across every week folder's corresponding
    file, so cache invalidation correctly fires on a write to ANY week, not just a fixed single file.
  - `_rebuild()`: change `load_jsonl_counted(self._runs_file)` / `(self._events_file)` /
    `(self._tools_file)` to read/concatenate across all week folders for each source, in ISO-week
    order.
  - **Fix the `_tools_file` bug** as an explicit, dedicated line item — restore real `tools_all`
    content from the multi-week glob.
  - Given this is real production API code, add explicit test coverage beyond "doesn't crash":
    correct aggregation across 2+ weeks, correct staleness detection from a write to a non-newest
    week, and the specific regression proving `tools_all` is non-empty against real sharded data.

## Out of Scope
- `tools/agent-monitoring/build_index.py`, `generate_retro.py`, `manifest.py`, `seq_offset.py`,
  `weight_sensitivity_check.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py`,
  `validate.py`, `query.py` — child 3.
- Any other `done_checker_static.py` check besides `check_monitoring_write_recorded` — this ticket
  changes only that check's path resolution, not its pass/fail logic or any other DoD condition.
- Any change to `DashboardCache`'s public method surface, its `threading.RLock()` locking pattern, or
  any presenter/API-route shape built on top of it — only the 3 source-file constants' resolution and
  the mtime/read logic that depends on them change.
- The codex subsystem (child 5) and referential-integrity tooling (child 6).

## Acceptance Criteria
- [x] A test asserts `done_checker_static.py::check_monitoring_write_recorded` correctly finds a real
      run/event pair for a given `run_id` when that pair lives in a non-`current`, older week folder
      — not just the newest one.
- [x] Zero unrelated functional change to any other `done_checker_static.py` check (diff scoped to
      `check_monitoring_write_recorded`'s path resolution only).
- [x] A test proves `DashboardCache._rebuild()` aggregates `runs`/`events`/`tools` records from 2+
      week folders, not just one.
- [x] A test proves `DashboardCache._maybe_rebuild()` correctly detects staleness from a write to a
      non-newest week folder for each of the 3 sources.
- [x] **Regression test proving the `_tools_file` bug is fixed**: `DashboardCache._tools_all` (and
      derived `_tools_by_seq`/`_tools_by_run_recent`) is non-empty and correct against real
      post-migration multi-week `tools` data.
- [x] No change to `DashboardCache`'s public API surface or its existing single-`RLock()` guarding
      pattern.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE (child 3 — independent, file-disjoint, parallelizable
  with this ticket once child 2 lands)
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD (or equivalent — the ticket
  that wired `_tools_all` retention into `DashboardCache` for Skill Usage; directly relevant context
  for why this bug's blast radius includes the Skill Usage dashboard view, confirm exact ticket ID at
  implementation time).
- TCK-20260902-MONITORING-SHARD-CONSUMERS — confirmed `done_checker_static.py` out of scope for the
  tools-only epic; this ticket is the direct follow-up that brings it into scope now that
  `runs`/`events` shard too.

## Related Docs
None beyond code-level accuracy — no doc currently claims `DashboardCache`'s internal file-resolution
shape (that's an implementation detail, not documented API behavior).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py` (lines ~691-692, `check_monitoring_write_recorded`)
- `src/api/agent_ops_dashboard/ingest.py` (lines 474-476, 497-521, `DashboardCache`)

## Assumptions / Open Questions
- Assumes child 2 (migration) has landed.
- `DashboardCache` is explicitly called out by the requester's original context as "real production
  API-facing code, not just a dev tool" — this ticket's test coverage bar is intentionally higher
  (explicit staleness/aggregation tests, not just no-crash smoke tests) to match that risk profile.
- `layer: observability` matches this repo's established pattern; `dashboard` tag added specifically
  for the `agent_ops_dashboard/ingest.py` portion of this ticket's scope.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD/plan.md`'s
7 steps, in the recommended order, with no deviations from the plan's design.

- **Step 1** (`tools/gate_checks/done_checker_static.py`): added
  `_jsonl_rows_for_run_id_across_weeks(data_root, filename, run_id)` directly below
  `_jsonl_rows_for_run_id` (reused unchanged as the per-shard worker). Rewrote
  `check_monitoring_write_recorded`'s signature from `(ticket_id, runs_path=Path("agent-monitoring/runs.jsonl"),
  events_path=Path("agent-monitoring/events.jsonl"))` to `(ticket_id, data_root=Path("agent-monitoring/data"))`
  per the ratified design decision (single `data_root`, not two path params). Body now globs
  `data_root/*/runs.jsonl` and `data_root/*/events.jsonl` across every ISO-week shard.
- **Step 2** (`tests/tools/test_done_checker_static.py`): updated the 4 existing
  `check_monitoring_write_recorded` tests to nest fixtures under `tmp_path/2026-W23/` and call with
  `data_root=tmp_path`. Added the 2 required new tests:
  `test_check_monitoring_write_recorded_finds_pair_in_non_current_week` and
  `test_check_monitoring_write_recorded_still_fails_when_absent_from_all_weeks`.
- **Step 3** (`src/api/agent_ops_dashboard/ingest.py`): added `_week_shard_paths`, `_max_mtime`
  (guards the `max()`-over-empty-sequence `ValueError`), and `_load_jsonl_counted_multi` module-level
  helpers below `load_jsonl_counted`. Replaced `DashboardCache.__init__`'s 3 hardcoded
  `_runs_file`/`_events_file`/`_tools_file` fields with one `self._data_root = repo_root /
  "agent-monitoring" / "data"`. `_current_source_state()` now computes each source's mtime via
  `_max_mtime(_week_shard_paths(...))`. `_rebuild()` now reads/concatenates via
  `_load_jsonl_counted_multi(...)` per source, correctly summing `_unparsed_lines` across shards
  instead of the old single-file count. This is the dedicated fix for the live `_tools_file` bug —
  `tools_all` is no longer permanently empty.
- **Step 4** (4 dashboard test files): added a `_FIXTURE_WEEK = "2026-W23"` constant to each of
  `test_agent_ops_dashboard_ingest.py`, `test_agent_ops_dashboard_stats.py`,
  `test_agent_ops_dashboard_concurrency.py`, `test_agent_ops_dashboard_api.py`, and repointed every
  fixture helper/inline write from the flat `agent-monitoring/{runs,events,tools}.jsonl` layout to
  `agent-monitoring/data/<week>/{runs,events,tools}.jsonl`. The malformed-content fixture in
  `test_agent_ops_dashboard_api.py` (`"garbage\ngarbage\ngarbage\n"`) kept byte-identical content —
  only its path moved. `test_agent_ops_dashboard_api_boundary.py`, `_glossary.py`,
  `_frontend_api_surface.py`, `_serve.py` confirmed to construct zero `runs`/`events`/`tools`
  fixtures (grep-verified) — left untouched.
- **Step 5** (`test_agent_ops_dashboard_ingest.py`): added the 5 new required `DashboardCache` tests
  — `test_dashboard_cache_rebuild_aggregates_across_multiple_weeks`,
  `test_dashboard_cache_maybe_rebuild_detects_staleness_from_non_newest_week_write` (all 3 sources,
  from the older of two week folders), `test_dashboard_cache_tools_all_nonempty_against_real_sharded_layout`
  (the dedicated `_tools_file` regression), `test_current_source_state_empty_data_dir_returns_zero_not_crash`,
  and `test_dashboard_public_api_surface_and_lock_unchanged`.
  One minor correction versus plan.md's Step 5 text: the public-method-surface assertion set is 9
  names, not 8 — plan.md's own list omitted `get_bulk_timeline`, which is a real public method
  (confirmed via direct source read of `ingest.py`, line ~781, and already exercised elsewhere in
  this same test file). Recorded here per staging_artifacts' Deviations note.
- **Step 6** (`docs/observability/agent_ops_dashboard_contract.md`): updated lines 16 and 158 (line
  158, not 157, after the Step 3 diff's line shift) to describe the week-sharded glob read pattern.
  Scanned the rest of the file for other flat-layout claims — one other passage (near line 397)
  mentions `agent-monitoring/tools.jsonl` but is a historical claim about a different, already-closed
  ticket's write-path behavior at the time it landed, not a current physical-layout claim about
  `ingest.py`'s read contract — left untouched per plan.md's scope guard.
- **Step 7** (`docs/parity_ledger/infrastructure.yaml`, `INFRA-275`): updated via
  `tools/parity_ledger_writer.py::write_entry()` (loaded the entry with `yaml.safe_load`, edited only
  `text` and `v2_evidence` in-process, called `write_entry`) — never a raw YAML edit. `text` now
  describes the week-sharded glob read pattern; `v2_evidence` gained an appended, dated note (this
  ticket's ID, the new helper names, the bug-fix framing, and the regression test names) following
  the entry's existing append-only-notes convention. `status` stayed `verified`, `priority` stayed
  `P2`. Confirmed via `git diff` that the writer's rewrite touched only this one entry's `text`/
  `v2_evidence` fields — no reformatting drift elsewhere in the 5000+-line shard file.

**Correctness-improvement side effect (not a regression)**: per plan.md's Anti-Drift Notes, fixing
the `_tools_file` bug means `compute_inferred_active`'s 10-minute-window heuristic will now actually
fire in production for the first time in a while, since `tools_by_run_recent` is built from real
data instead of a permanently-empty list. A currently-running run will now correctly show
`is_inferred_active=True` on the live dashboard — this is the bug being fixed working as intended,
not new unintended behavior.

## Test Summary

Ran (via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`, the project's
real dependency-complete venv — bare `python3` lacks `pydantic`):

- `tests/tools/test_done_checker_static.py` + `tests/tools/test_finalize_tag_drift_wiring.py`: 107
  passed (includes all 6 `check_monitoring_write_recorded` tests: 4 updated + 2 new).
- `tests/tools/test_agent_ops_dashboard_ingest.py` (48 tests, including the 5 new ones) +
  `test_agent_ops_dashboard_stats.py` + `test_agent_ops_dashboard_concurrency.py` +
  `test_agent_ops_dashboard_api.py` + `test_agent_ops_dashboard_api_boundary.py` +
  `test_agent_ops_dashboard_glossary.py` + `test_agent_ops_dashboard_frontend_api_surface.py` +
  `test_agent_ops_dashboard_serve.py`: 107 passed.
- Combined run of both groups together: 214 passed, 0 failed.
- Broader confirmation sweep, `pytest tests/tools/ -k "done_checker or agent_ops_dashboard or
  monitoring_write" -v`: 233 passed, 2449 deselected, 0 failed — confirms no collateral damage to
  the wider `tests/tools/` surface (this filter also picks up `test_monitoring_writer*.py`, which is
  unrelated to this ticket's scope and passed unmodified).
- Never ran unscoped `pytest tests/`, per CLAUDE.md's Testing Rule.

## Files Changed

- `tools/gate_checks/done_checker_static.py` — added `_jsonl_rows_for_run_id_across_weeks`; rewrote
  `check_monitoring_write_recorded`'s signature and body around `data_root: Path`.
- `tests/tools/test_done_checker_static.py` — updated 4 existing `check_monitoring_write_recorded`
  tests to the new call shape; added 2 new tests.
- `src/api/agent_ops_dashboard/ingest.py` — added `_week_shard_paths`/`_max_mtime`/
  `_load_jsonl_counted_multi`; replaced `DashboardCache`'s 3 private file fields with `_data_root`;
  fixed `_current_source_state()` and `_rebuild()`.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — repointed fixture helper/inline writes to the
  week-sharded layout; added 5 new `DashboardCache` tests.
- `tests/tools/test_agent_ops_dashboard_stats.py` — repointed `_write_runs`/`_write_events`/
  `_write_tools` helpers to the week-sharded layout.
- `tests/tools/test_agent_ops_dashboard_concurrency.py` — repointed `_init_repo`/`_append_run`/inline
  writes to the week-sharded layout.
- `tests/tools/test_agent_ops_dashboard_api.py` — repointed `_client_with_repo` and 8 inline
  single-file writes to the week-sharded layout (malformed-content fixture kept byte-identical).
- `docs/observability/agent_ops_dashboard_contract.md` — updated the physical read-path description
  (2 locations).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-275`'s `text`/`v2_evidence` updated via
  `tools/parity_ledger_writer.py` (sanctioned tool, not a raw edit).
- `staging_artifacts/TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD/investigation.md`,
  `plan.md`, `test_plan.md` — pre-existing artifacts from this run's own Investigate/Plan phases
  (present on disk before this Implement phase began; not authored by this agent, but part of this
  run's real changeset).
- `tickets/inprogress/TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD.md` — this file
  (Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion
  Summary).

No file outside this list was modified by this Implement run. Confirmed via `git status` that files
belonging to children 3/5/6 (e.g. `tools/agent-monitoring/build_index.py`, `manifest.py`,
`seq_offset.py`, `tools/agent_replay_codex/*`, `tests/agent_codex_realrepo_pilot_harness/*`) were
already modified by concurrent sessions in this shared worktree before this run started and were
left untouched throughout.

## Completion Summary

Migrated `done_checker_static.py::check_monitoring_write_recorded` and
`agent_ops_dashboard/ingest.py::DashboardCache` from the retired flat `agent-monitoring/{runs,events,tools}.jsonl`
layout to a sorted glob over every `agent-monitoring/data/<ISO-week>/` shard, mirroring the
`record_events.py::compute_tool_stats()` precedent. This fixes two live, silent production bugs: the
DoD gate's monitoring-write check was unconditionally FAILing for every ticket (loud-but-non-blocking
per CLAUDE.md's Hard Rule, so not pipeline-blocking, but a spurious warning on every close), and
`DashboardCache._tools_all`/`_tools_by_seq`/`_tools_by_run_recent` were permanently empty, silently
zeroing Skill Usage stats and disabling the `is_inferred_active` heuristic on the live dashboard.
`DashboardCache`'s public method surface and single-`RLock()`-per-method locking pattern are
unchanged (architecture-guard-tested). All 6 acceptance criteria are met with dedicated tests; 214
tests pass across the full regression surface named in test_plan.md, plus a 233-test broader
confirmation sweep with zero failures.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently re-ran 214/214 (scoped) and 233/233 (broader sweep), confirmed the `_tools_all`
regression test is genuine (writes only the real sharded path, would fail pre-fix), confirmed the
public API surface via diff, and confirmed the 9-vs-8 method deviation is legitimate via
`git log -S` (pre-existing, not scope creep). Architecture-Verify (architecture-reviewer):
**APPROVED** — production API surface confirmed internal-only, locking confirmed byte-identical,
parity ledger update confirmed tool-mediated (YAML entry-count parity check), no scope creep, 151
tests independently re-confirmed. Verify (done-checker): **READY TO CLOSE**, 13/13 Definition-of-
Done conditions PASS.
