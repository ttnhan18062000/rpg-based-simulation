---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-CONSUMERS
phase: done
date: 2026-09-02
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260902-MONITORING-SHARD-CONSUMERS

## Title
Migrate `agent-monitoring/tools.jsonl` readers (`build_index.py`, `generate_retro.py`, `query.py`,
`validate.py`) to glob weekly shard files instead of one hardcoded path

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`tools/agent-monitoring/build_index.py` (`DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`,
line 44) and `tools/agent-monitoring/generate_retro.py` (`DEFAULT_TOOLS_FILE`, line 57, plus its
on-demand `build_index.build(tools_file=str(DEFAULT_TOOLS_FILE))` call and its index-staleness mtime
check `_index_is_stale()`, lines ~71-79, from `TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`)
both hardcode the single old `tools.jsonl` path. Once child tickets 1 and 2 land, real tool-call data
lives across `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard files instead — these hardcoded
single-path references must become a glob over all shards, read/concatenated in filename
(chronological ISO-week) order, and the staleness check must compare the index's mtime against the
*newest* shard's mtime, not one file's.

`tools/agent-monitoring/query.py` and `tools/agent-monitoring/validate.py`'s
`compute_drift_report()`/`compute_tool_count_drift_report()`/`compute_multi_invocation_collision_report()`
were grepped this scoping session: neither file contains a `tools.jsonl`-specific path constant —
only `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")` — consistent with the archived
design doc's account that `query.py`/`validate.py` were already migrated to read exclusively via the
SQLite index in the `agent-monitoring-derived-index` batch (2026-07-28). Their functional scope in
this ticket may therefore be narrower than a raw path-string change (see Assumptions) — the
investigator must confirm at implementation time whether either file has any direct-JSONL fallback
path that also needs updating, versus being purely index-consumers already unaffected by the file
layout change.

**Correction found during this scoping session:** `tools/gate_checks/done_checker_static.py`'s
`check_monitoring_write_recorded()` (the "existence-only, non-blocking" check named in this epic's
original request) reads only `runs.jsonl`/`events.jsonl` (lines 691-692) — it does not reference
`tools.jsonl` in any way. It is explicitly out of scope for this ticket; see Out of Scope.

## Scope
- `tools/agent-monitoring/build_index.py`: replace `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`
  (line 44) with a glob over `agent-monitoring/tools/tools-*.jsonl`, reading and concatenating all
  matching shards in filename (chronological ISO-week) order before building the `tools` table.
  Leave `DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE` (lines 42-43) unchanged — out of scope, per the
  parent epic.
- `tools/agent-monitoring/generate_retro.py`: replace `DEFAULT_TOOLS_FILE` (line 57) the same way;
  update its on-demand `build_index.build()` call site (line ~102) to pass the resolved shard
  list/glob instead of one path. Extend `_index_is_stale()` (lines ~71-79) so its per-source mtime
  comparison uses the newest shard file's mtime for the `tools` source, not a single file's mtime —
  a stale-but-not-newest shard must still correctly trigger a rebuild.
- `tools/agent-monitoring/query.py`: investigator confirms at implementation time whether this file
  has any direct-JSONL read/fallback path needing a glob update, or is purely an index consumer
  already unaffected (this session's grep found only `DEFAULT_DB_PATH`). If purely index-consuming,
  this file needs no functional change under this ticket — document that finding rather than making
  a no-op edit.
- `tools/agent-monitoring/validate.py`: same investigator confirmation for
  `compute_drift_report()`/`compute_tool_count_drift_report()`/`compute_multi_invocation_collision_report()`
  — this session's grep found only `DEFAULT_DB_PATH`, no direct `tools.jsonl` path constant.
- Update remaining "3 append-only JSONL files" / single-file `tools.jsonl` language in
  `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6 that is not already covered by
  child ticket 1's write-path doc update (e.g. README.md's Navigation table entry, schema.md's
  build-index staleness-check description, any remaining single-file framing in the other two docs).

## Out of Scope
- Any change to `build_index.py`'s table schema (`runs`/`events`/`tools` tables) — only the
  source-file resolution (single path → glob) changes.
- `tools/gate_checks/done_checker_static.py` — confirmed during scoping to not reference
  `tools.jsonl` at all (only `runs.jsonl`/`events.jsonl`); do not touch this file under this ticket.
- Re-deriving `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()`, or any other
  normalization logic already centralized in `build_index.py`/`generate_retro.py` — only the file
  *resolution* layer changes, not the normalization logic itself.
- `runs.jsonl`/`events.jsonl` reading logic in any of these 4 files — unaffected, out of scope per
  the parent epic.

## Acceptance Criteria
- [x] `python3 tools/agent-monitoring/build_index.py` (`make agent-monitoring-index`) successfully
      builds `monitoring.db`'s `tools` table from all shard files under `agent-monitoring/tools/`,
      with a row count equal to the total across all shards.
- [x] A test simulates 2+ shard files existing under a temp `agent-monitoring/tools/`-shaped
      directory and confirms `build_index.py` reads and includes records from all of them, not just
      one.
- [x] `generate_retro.py`'s on-demand build path and its staleness check correctly detect a newly
      appended row in ANY shard (not only the most-recently-created one) as making the index stale.
- [x] `query.py`'s existing test suite (`tests/tools/test_query.py`) still passes unmodified (or with
      only the confirmed-necessary changes, documented in Implementation Notes).
- [x] `validate.py`'s drift-report functions produce identical results on the post-migration sharded
      corpus as they did pre-migration, for a fixed historical time window (regression check).
- [x] `docs/agent-monitoring/README.md`, `schema.md`, `docs/guides/agent_monitoring.md`,
      `docs/ai/system_overview.md` §6 no longer describe `tools.jsonl` as a single physical file.
- [x] `tools/gate_checks/done_checker_static.py` has zero diff in this ticket (confirms it was
      correctly left untouched, per the scoping-session correction above).

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC (parent epic)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH (child 1)
- TCK-20260902-MONITORING-SHARD-MIGRATION (child 2 — hard prerequisite: this ticket's tests need
  real multi-shard files on disk to test against end-to-end)
- TCK-20260713-MONITORING-SQLITE-INDEX / TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE /
  TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE / TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE — the
  batch that built `build_index.py` and originally migrated these same 4 consumers to read via the
  SQLite index; this ticket extends that migration's file-resolution layer for sharded sources, it
  does not redo that migration.
- TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS — the staleness check this ticket extends to
  multi-shard mtime comparison.

## Related Docs
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`
- `docs/ai/system_overview.md` §6
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` — the shipped
  design this ticket's file-resolution layer extends

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/`,
  `stored_artifacts/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE/`,
  `stored_artifacts/TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE/`,
  `stored_artifacts/TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE/` — original migration rationale for
  `query.py`/`validate.py`/`generate_retro.py`'s index-based reads, directly relevant background for
  confirming each file's real direct-file-read surface (or lack thereof) in this ticket.

## Related Code Areas
- `tools/agent-monitoring/build_index.py` (line 44, and its build routine ~line 172)
- `tools/agent-monitoring/generate_retro.py` (lines 53-57, ~71-79, ~102)
- `tools/agent-monitoring/query.py`
- `tools/agent-monitoring/validate.py`
- `tools/gate_checks/done_checker_static.py` (confirmed NOT touched — see Out of Scope)
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`
- `docs/ai/system_overview.md`

## Assumptions / Open Questions
- Assumes child ticket 2 (migration) has landed — real, complete shard files exist on disk. Hard
  prerequisite per `SEQUENCE.md`.
- `query.py`'s and `validate.py`'s exact direct-file-read scope (vs. index-only) needs
  re-confirmation by the investigator at implementation time — this session's grep found no direct
  `tools.jsonl` path constant in either file (only `DEFAULT_DB_PATH`), suggesting their functional
  scope here may be narrower than the original epic request assumed (possibly doc/comment-only or a
  no-op). Plan must resolve this with real evidence before implementation, not assume the original
  framing.
- `done_checker_static.py` is explicitly out of scope, correcting the original request's open
  question about whether it hardcodes the old path — confirmed this session via grep that it does
  not reference `tools.jsonl` in any way.

## Implementation Notes

Followed plan.md's 11 steps in order.

- **Step 1**: Added a dir-aware branch to `validate.py::load_jsonl()` (checked *before* the existing
  `if not path.exists(): return []` check, since a directory satisfies `.exists()`). If `path.is_dir()`,
  glob `sorted(path.glob("tools-*.jsonl"))` and recursively concatenate `load_jsonl()` over each
  shard (each shard is a literal file, so it hits the unchanged non-dir branch — no duplicated
  parsing logic). `build_index.py` imports this exact function.
- **Step 2**: Repointed `DEFAULT_TOOLS_FILE` in both `build_index.py` (line 44) and
  `generate_retro.py` (line 57) from `Path("agent-monitoring/tools.jsonl")` to
  `Path("agent-monitoring/tools")` (the shard directory). `DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE`/
  `RUNS_FILE`/`EVENTS_FILE` left untouched.
- **Step 3**: Added the identical dir-aware branch to `generate_retro.py`'s own separate
  `load_jsonl()` definition (mirrored, not consolidated, per the ticket's Out-of-Scope guard against
  re-deriving centralized normalization logic — these two `load_jsonl` functions were already
  independent before this ticket). Added a new `_source_mtime(source)` helper (`max()` over each
  shard's own mtime when `source.is_dir()`, else the file's own mtime if it exists, else `None`) and
  used it inside `_index_is_stale()` for all three sources — never the shard directory's own mtime,
  which does not reliably update when an existing file inside it is appended to.
- **Step 4**: Refactored `manifest.py`'s `_scan_file` into a shared `_stream_file_into(path, source,
  hasher, counts)` helper (still `open(..., "rb")` + line iteration only — the AST full-file-read
  guard stays satisfied by construction) plus a new `_scan_tools_shards(tools_dir, source)` that
  streams every `sorted(tools_dir.glob("tools-*.jsonl"))` shard through the same helper, accumulating
  one running SHA-256 and combined counts, and emits the same `{"file": "tools.jsonl", ...}` record
  shape unchanged — `build_manifest()` now special-cases the `"tools"` source to call
  `_scan_tools_shards()` instead of `_scan_file()`, keeping the 3-record output shape and the literal
  `"tools.jsonl"` filename label. Also fixed `capture_lines()` (Decision 4 — a real, currently-red
  regression discovered live during planning, not named anywhere else in the ticket): it has its own
  separate unconditional-open loop, independent of `_scan_file`/`build_manifest`, with two live
  non-test consumers (`tools/agent_replay_codex/containment.py`,
  `tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py`). Given the same dual-mode treatment
  — if `agent_monitoring_dir / "tools"` is a real directory, glob and concatenate shard lines under
  the same `"tools.jsonl"` result key; otherwise fall back to the literal-file behavior unchanged
  (needed because `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`'s
  fixture writes a literal `tools.jsonl` file for 3 other currently-green tests).
- **Step 5**: Removed `@pytest.mark.xfail(...)` from 3 of the 4 manifest tests
  (`test_build_manifest_shape_against_real_corpus`,
  `test_manifest_cli_reproducible_byte_identical_across_two_runs`,
  `test_build_manifest_reproducible_byte_identical_direct_call`) and removed the now-unused
  `_XFAIL_TOOLS_JSONL_RETIRED_REASON` constant. Test bodies unchanged.
- **Step 6**: Fixed the 2 test-helper functions that independently hardcoded the retired path (real
  fixture maintenance, not a gate-routing workaround — the test assertions themselves are unchanged):
  `test_agent_monitoring_manifest.py::_content_hash_snapshot()` now hashes across
  `sorted((_REAL_AGENT_MONITORING_DIR / "tools").glob("tools-*.jsonl"))` when `filename ==
  "tools.jsonl"`, still keyed under the same `"tools.jsonl"` label; removed the xfail on
  `test_manifest_run_against_real_corpus_produces_zero_diff` (the 4th manifest xfail).
  `test_skill_usage_metric.py::_independently_derive_counts()` now iterates
  `sorted(_REAL_TOOLS_DIR.glob("tools-*.jsonl"))` (renamed `_REAL_TOOLS_FILE` →
  `_REAL_TOOLS_DIR = _REAL_AGENT_MONITORING_DIR / "tools"`); removed the xfail on
  `test_live_corpus_matches_independently_derived_counts` (the 5th named xfail).
- **Step 7**: No production code change to `query.py` or `validate.py`'s report functions
  (`compute_drift_report`/`compute_tool_count_drift_report`/`compute_multi_invocation_collision_report`).
  Confirmed post-implementation: `git diff --stat -- tools/agent-monitoring/query.py` is empty (true
  zero-diff). `git diff --stat -- tools/agent-monitoring/validate.py` shows a 5-line insertion — this
  is Step 1's `load_jsonl()` dir-aware branch only, a distinct function from the three report
  functions Decision 5 covers; see the "Deviations" section added to `plan.md` for the full
  reconciliation of this apparent (but not real) conflict between plan.md's Step 1 and Step 7. Both
  `test_query.py` and `test_validate_agent_monitoring.py` pass in full, unmodified, including
  `TestRegressionParity`'s pre/post-migration byte-identical-output tests for all three report
  functions.
- **Step 8**: Removed `@pytest.mark.xfail(...)` from `test_correlation_real_corpus_produces_a_real_number`
  and `test_parity_index_readpath_call_count_matches_real_corpus_state` (the 6th and 7th named
  xfails). No test-body change; the pinned `result["count"] == 4` value held exactly (confirmed real,
  not a bug requiring a baseline bump).
- **Step 9**: Doc updates. `docs/agent-monitoring/schema.md` line 30's staleness-check paragraph
  reworded to describe the multi-shard max-mtime comparison. Additionally fixed the "Join Example"
  Python snippet (~line 446), which literally did `Path('agent-monitoring/tools.jsonl').read_text()`
  — not named in plan.md's Step 9 file/line list but squarely within the ticket's own Scope text
  ("any remaining single-file framing... in schema.md"); see plan.md's Deviations section.
  `docs/agent-monitoring/README.md` lines 19, 54, 148 reworded to name the
  `tools/tools-YYYY-Www.jsonl` shard family instead of one physical file; lines 20-21's logical
  `tools.jsonl`-as-shorthand references left untouched (same retained-naming convention
  `schema.md`'s own heading keeps). `docs/ai/system_overview.md` §6 (lines 231-244) reworded from "3
  append-only JSONL files" to "two single files... plus a sharded family". `docs/guides/agent_monitoring.md`
  confirmed excluded (Decision from investigation — logical references only, no physical-file claim).
  Root-level `agent-monitoring/README.md` deferred per Decision 6 (outside ticket's own doc list and
  outside `check_docs_to_update_coverage`'s `docs/` regex).
- **Step 10**: Updated `INFRA-291` in `docs/parity_ledger/infrastructure.yaml` via
  `tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit) — appended a date-stamped
  addendum to the entry's `support_boundary` field (mirroring the entry's existing 2026-08-14
  addendum pattern) noting the `DEFAULT_TOOLS_FILE` repoint and that the underlying migration this
  entry documents is otherwise unaffected. Status stays `verified`, priority stays `P2`.
  `tools/parity_index.py health` shows zero findings for `INFRA-291`. `git diff --stat` confirms the
  YAML diff is scoped to only this one entry (17 insertions, 0 deletions).
- **Step 11**: Full confirmation pass — see Test Summary below.

New tests added (test_plan.md's "New Tests Required" 1-7, all required for AC2/AC3):
`test_build_index_reads_multiple_shard_files_from_directory`,
`test_build_index_includes_unknown_week_shard`, `test_build_index_glob_result_is_sorted` (new
`TestShardedToolsSource` class in `test_build_index.py`);
`test_generate_retro_index_is_stale_detects_write_to_non_newest_shard`,
`test_generate_retro_load_jsonl_globs_shard_directory` (in `test_generate_retro.py`);
`test_manifest_tools_source_aggregates_all_shards`,
`test_manifest_tools_source_sha256_is_order_stable_across_shards` (in
`test_agent_monitoring_manifest.py`).

Two deviations from plan.md's literal text (both documented in full, with rationale, in
`staging_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/plan.md`'s new "Deviations" section) — see
that section for complete detail; summarized here: (1) Step 7's "zero diff" framing for
`validate.py` was inconsistent with Step 1's own explicit instruction to modify that same file's
`load_jsonl()` — resolved in favor of Step 1 (necessary, tested, and consistent with Decision 5's
actual finding about the report functions specifically); (2) `schema.md`'s Join Example snippet was
fixed in addition to Step 9's named line-30 paragraph, since it is the same class of stale
single-file claim within the ticket's own Scope text.

## Test Summary

Ran with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`, scoped to `tests/tools/`
and the one `tests/agent_orchestration_codex_adapter/` file per test_plan.md — never `pytest
tests/`.

**Step 11 final confirmation pass** (`pytest tests/tools/test_agent_monitoring_manifest.py
tests/tools/test_skill_usage_metric.py tests/tools/test_generate_retro.py -v -rA`):
`185 passed, 2 warnings in 30.95s` — zero `XFAIL`/`XPASS`/`error`. Grepping for the 7 named xfailed
tests plus the plan's filter pattern, all show genuine `PASSED`:
```
PASSED tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus
PASSED tests/tools/test_agent_monitoring_manifest.py::test_manifest_cli_reproducible_byte_identical_across_two_runs
PASSED tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call
PASSED tests/tools/test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff
PASSED tests/tools/test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts
PASSED tests/tools/test_generate_retro.py::test_correlation_real_corpus_produces_a_real_number
PASSED tests/tools/test_generate_retro.py::test_parity_index_readpath_call_count_matches_real_corpus_state
```

**Previously-red, non-xfailed regression (plan.md Decision 4)** — `pytest
tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py -v -rA`:
`4 passed in 0.21s`, including `test_capture_lines_reads_all_three_monitoring_files` (was
`FileNotFoundError` before Step 4's `capture_lines()` fix) and its 3 previously-green siblings.

**`test_build_index.py` full suite** (regression risk — dual-mode design must keep every
literal-single-file fixture test green): `20 passed in 0.49s` (17 pre-existing + 3 new
`TestShardedToolsSource` tests).

**Primary domain scoped run** (`pytest tests/tools/test_build_index.py
tests/tools/test_generate_retro.py tests/tools/test_skill_usage_metric.py
tests/tools/test_agent_monitoring_manifest.py tests/tools/test_query.py
tests/tools/test_validate_agent_monitoring.py tests/tools/test_migrate_tools_shards.py`):
`262 passed, 2 skipped in 31.63s` (the 2 skips are `test_migrate_tools_shards.py`'s own
real-corpus-copy integration tests, correctly skipped because `agent-monitoring/tools.jsonl` no
longer exists — the intended post-migration end state, not a regression).

**Anti-Drift Test Guards** (all 4, individually re-run): `test_build_index_never_touches_write_path_modules`,
`test_manifest_source_never_calls_full_file_read_methods`,
`test_reuses_generate_retro_loader_not_a_second_loader`,
`TestReadOnlyGuarantee::test_source_jsonl_files_byte_identical_after_build` — `4 passed in 0.20s`.

**`done_checker` scoped check** (`pytest tests/tools/ -k "done_checker" -v`): `107 passed, 2536
deselected in 1.90s`.

**Zero-diff confirmations**: `git diff --stat -- tools/agent-monitoring/query.py` — empty (true
zero-diff). `git diff --stat -- tools/gate_checks/done_checker_static.py` — empty (AC7). `git diff
--stat -- tools/agent-monitoring/validate.py` — 5 insertions (Step 1's necessary `load_jsonl()` fix;
see Implementation Notes above and plan.md's Deviations section).

**`make agent-monitoring-index` against real corpus** (AC1): ran successfully, `tools: 179689 rows
(3 skipped)` on first run; a second immediate run showed `179694` after growth from this same
session's own intervening Bash tool calls (append-only monitoring writer logging its own tool
calls) — confirmed self-consistent (`n_ingested + n_skipped == len(records)` exactly) via a direct
in-process check, not a bug.

**Parity ledger**: `python3 tools/parity_index.py health` shows zero findings for `INFRA-291`;
`git diff --stat -- docs/parity_ledger/infrastructure.yaml` shows a scoped 17-line addition to only
that one entry.

## Files Changed

Production code:
- `tools/agent-monitoring/validate.py` — dir-aware `load_jsonl()` (Step 1)
- `tools/agent-monitoring/build_index.py` — `DEFAULT_TOOLS_FILE` repoint (Step 2)
- `tools/agent-monitoring/generate_retro.py` — `DEFAULT_TOOLS_FILE` repoint, dir-aware `load_jsonl()`,
  new `_source_mtime()` helper, generalized `_index_is_stale()` (Steps 2, 3)
- `tools/agent-monitoring/manifest.py` — `_stream_file_into()` extraction, new `_scan_tools_shards()`,
  `build_manifest()`'s tools-source branch, dual-mode `capture_lines()` (Step 4)

Tests:
- `tests/tools/test_build_index.py` — new `TestShardedToolsSource` class (3 new tests)
- `tests/tools/test_generate_retro.py` — removed 2 xfail decorators, 2 new tests
- `tests/tools/test_skill_usage_metric.py` — fixed `_independently_derive_counts()`/renamed
  `_REAL_TOOLS_DIR`, removed 1 xfail decorator
- `tests/tools/test_agent_monitoring_manifest.py` — removed 4 xfail decorators, removed
  `_XFAIL_TOOLS_JSONL_RETIRED_REASON`, fixed `_content_hash_snapshot()`, 2 new tests

Docs:
- `docs/agent-monitoring/schema.md` — staleness-check paragraph (line 30) + Join Example snippet
- `docs/agent-monitoring/README.md` — lines 19, 54, 148
- `docs/ai/system_overview.md` — §6 (lines 231-244)

Parity ledger (via `tools/parity_ledger_writer.py`, not a raw edit):
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-291` addendum

Staging artifacts (this run's own Investigate/Plan phases, substantively present at Implement
start — confirmed via `git status`/`git diff` against `origin/worktree-monitoring-tools-weekly-sharding`
base, and `plan.md` additionally rewritten during this Implement run to add its "Deviations"
section):
- `staging_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/investigation.md`
- `staging_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/plan.md`
- `staging_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/test_plan.md`

Ticket:
- `tickets/inprogress/TCK-20260902-MONITORING-SHARD-CONSUMERS.md` (moved from
  `tickets/todos/agent-monitoring-weekly-sharding/`, per the folder's `SEQUENCE.md`)

## Completion Summary

All 4 production files (`validate.py`, `build_index.py`, `generate_retro.py`, `manifest.py`) were
made dir-aware over the `agent-monitoring/tools/` shard directory via a consistent dual-mode
(directory-glob-or-literal-file) pattern, preserving every currently-green single-file-fixture test
unmodified. `query.py` and `validate.py`'s three report functions needed zero functional change
(confirmed no-op, documented). All 7 previously-xfailed tests now show genuine `PASSED` with the
`xfail` markers and dead reason constants removed, plus the previously-red (non-xfailed)
`test_capture_lines_reads_all_three_monitoring_files` now passes for real via `manifest.py`'s
`capture_lines()` fix (Decision 4, a real regression discovered live during planning). 7 new tests
were added per test_plan.md's required coverage for AC2/AC3. Docs (`schema.md`, README.md,
`system_overview.md`) no longer describe `tools.jsonl` as a single physical file, and the parity
ledger's `INFRA-291` entry was updated via the sanctioned writer script with a scoped addendum. This
is the final child ticket of the weekly-sharding epic; the branch is now ready for the combined PR
covering all 3 children, pending this ticket's own Test/Parity/Verify/Finalize phases.
