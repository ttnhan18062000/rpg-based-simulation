---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-CONSUMERS
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality]
---

# Test Plan — TCK-20260902-MONITORING-SHARD-CONSUMERS

## Regression Surface

Existing tests that must keep passing (all currently green; none of these are among the 7 named
xfails). Group by domain:

**`build_index.py` unit tests** (`tests/tools/test_build_index.py`, all classes):
- `TestBuildHappyPath::test_build_creates_gitignored_sqlite_db`
- `TestReadOnlyGuarantee::test_source_jsonl_files_byte_identical_after_build`
- `TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status`,
  `test_completeness_matches_validate_legacy_allowlists`
- `TestLegacyShapeGuards::test_type_checker_legacy_shape_does_not_crash_build`,
  `test_build_index_skips_offschema_tools_records`, `test_events_table_tolerates_duplicate_run_id_seq`
- `TestRerunStability::test_build_twice_produces_same_row_counts`
- `TestMakeTarget::*`, `TestGitignore::*`
- `TestArchitectureGuards::test_no_incremental_build_flag_exists`,
  `test_build_index_never_touches_write_path_modules`, `test_build_index_imports_vocabulary_not_reencoded`
- **At risk from the fix**: all of these construct a single literal `tmp_path / "tools.jsonl"` file
  via `_make_corpus()`/`_args()` and pass it as `tools_file`. The dual-mode (dir-or-file) design in
  investigation.md keeps every one of these passing unmodified — verify this explicitly after
  implementation, since it is the single biggest regression risk in this ticket.

**`generate_retro.py` unit tests** (`tests/tools/test_generate_retro.py`, large file — targeted
subset most load-bearing for this ticket):
- `test_generate_retro_builds_index_on_demand_when_missing` (line 896)
- `test_generate_retro_rebuilds_stale_index_not_just_missing_index` (line 922)
- `test_index_is_stale_false_when_index_newer_than_all_sources` (line 972)
- `test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails` (line 989+)
- `test_tool_safety_function_is_pure_no_file_io` (line 1967) and
  `test_new_sections_never_write_any_file` (line 2311) — architecture guards asserting the pure
  `compute_*` functions never reference `DEFAULT_TOOLS_FILE`/`load_jsonl`/`RUNS_FILE`/`EVENTS_FILE`
  in their own source; must stay true (these functions are not touched by this ticket's fix).
- `test_parity_index_readpath_detection_matches_real_call_when_present`,
  `test_parity_index_readpath_detection_false_positive_guards`,
  `test_parity_index_readpath_section_never_silent_has_derivation` — synthetic-fixture tests, no
  file dependency, unaffected.
- All ~50+ remaining tests in this file that construct `tools`/`runs`/`events` as in-memory fixtures
  (the overwhelming majority) — unaffected by a file-resolution-layer change.

**`skill_usage_metric.py` unit tests** (`tests/tools/test_skill_usage_metric.py`):
- `test_reuses_generate_retro_loader_not_a_second_loader` (line 47) — pins the reuse-not-reimplement
  import shape; must stay true.
- `test_never_calls_json_loads_on_input_summary` (line 53),
  `test_does_not_import_generate_retro_tag_breakdown_internals` (line 70) — AST guards, unaffected.
- `test_counts_skill_invocations_by_name`, `test_none_run_id_buckets_under_unattributed`,
  `test_missing_run_id_key_also_buckets_under_unattributed`,
  `test_unparseable_input_summary_counted_not_dropped_not_crashed`,
  `test_empty_input_produces_empty_report_not_error`, `test_derivation_string_present_and_non_fabricated`
  — all synthetic-fixture, unaffected.
- `test_cli_runs_against_real_corpus_and_prints_json` (line 173) and
  `test_causes_zero_diff_on_real_corpus` (line 183) — currently pass vacuously (empty corpus today);
  must keep passing with real, non-empty data after the fix — verify they don't start failing once
  the corpus is no longer empty (e.g. a report-shape assumption that happened to hold trivially on
  `[]`).

**`manifest.py` unit tests** (`tests/tools/test_agent_monitoring_manifest.py`):
- `test_manifest_source_never_calls_full_file_read_methods` (line 93) — AST guard; the glob-based
  fix must stay within `open(..., "rb")` + per-line iteration, never `read_text`/`read_bytes`/
  `readlines`/`read`.

**`query.py`/`validate.py`** (`tests/tools/test_query.py`, `tests/tools/test_validate_agent_monitoring.py`):
- Full suites of both files — investigation confirmed both files are purely index-consumers with no
  direct `tools.jsonl` dependency; both suites are expected to pass with **zero code changes** to
  either source file. Running them is a regression check that the assumption held, not a check on
  new code.

**Migration script's own suite** (`tests/tools/test_migrate_tools_shards.py`) — not modified by this
ticket, but shares the same shard-filename conventions this ticket's glob patterns must match; worth
including in the scoped run as a cross-check that shard-naming assumptions haven't drifted.

## New Tests Required

Per acceptance criteria and the investigation's scope-gap recommendation (bringing `manifest.py`/
`skill_usage_metric.py` formally into scope):

1. **`test_build_index_reads_multiple_shard_files_from_directory`**
   - Category: integration (real multi-file directory fixture)
   - Verifies: given a temp `agent-monitoring/tools/`-shaped directory containing 2+ shard files
     (e.g. `tools-2026-W01.jsonl` with 2 records, `tools-2026-W02.jsonl` with 3 records), calling
     `build_index.build()` with `tools_file` pointing at that directory produces a `tools` table with
     `COUNT(*) == 5` (sum across shards), not just the records from one shard. This is the ticket's
     own AC2, verbatim.
   - Location: `tests/tools/test_build_index.py`, new test in `TestBuildHappyPath` or a new
     `TestShardedToolsSource` class.

2. **`test_build_index_includes_unknown_week_shard`**
   - Category: unit
   - Verifies: a shard directory containing `tools-unknown-week.jsonl` alongside dated shards has its
     rows included in the `tools` table — regression guard against the "widen glob / filter unknown
     shard" anti-drift hazard.
   - Location: `tests/tools/test_build_index.py`.

3. **`test_build_index_glob_result_is_sorted`**
   - Category: unit / architecture guard
   - Verifies: shard files are concatenated in filename-sorted (chronological ISO-week) order —
     e.g. construct shards out of filesystem-creation-order such that an unsorted glob would
     concatenate them differently, and assert row order in the `tools` table (by `id`) matches
     sorted-filename order, not creation order.
   - Location: `tests/tools/test_build_index.py`.

4. **`test_generate_retro_index_is_stale_detects_write_to_non_newest_shard`**
   - Category: integration
   - Verifies: with 2+ shard files present and the index freshly built (not stale), appending a new
     row to the *older* (non-newest-by-filename) shard and touching its mtime still makes
     `_index_is_stale()` return `True` — directly covers the ticket's AC3 ("correctly detect a newly
     appended row in ANY shard, not only the most-recently-created one") and the anti-drift hazard
     around not using directory-mtime as a shortcut.
   - Location: `tests/tools/test_generate_retro.py`, near the existing `_index_is_stale` tests
     (~line 972).

5. **`test_generate_retro_load_jsonl_globs_shard_directory`**
   - Category: unit
   - Verifies: `generate_retro.load_jsonl(shard_dir)` (a directory path) returns the concatenation of
     all `tools-*.jsonl` files inside it in sorted order, while `generate_retro.load_jsonl(single_file_path)`
     (a literal file, existing or not) retains its exact current behavior (including
     `if not path.exists(): return []`) — proves the dual-mode design doesn't regress the
     `runs.jsonl`/`events.jsonl` single-file call sites.
   - Location: `tests/tools/test_generate_retro.py`.

6. **`test_manifest_tools_source_aggregates_all_shards`**
   - Category: unit
   - Verifies: given a temp `agent-monitoring/`-shaped directory with `runs.jsonl`, `events.jsonl`,
     and a `tools/` subdirectory containing 2+ shard files, `build_manifest()` returns exactly 3
     records (not more), the `"tools.jsonl"` record's `line_count` equals the sum across all shards,
     and `parser_result.parsed_ok + parser_result.parse_errors == line_count` still holds for the
     aggregate. Directly covers the "must not change the 3-record shape" anti-drift hazard.
   - Location: `tests/tools/test_agent_monitoring_manifest.py`.

7. **`test_manifest_tools_source_sha256_is_order_stable_across_shards`**
   - Category: unit
   - Verifies: the aggregate `sha256` for the tools source is identical across two separate calls to
     `build_manifest()` against the same fixture directory (reproducibility), and changes if a byte
     inside any one shard changes (sensitivity) — a minimal, targeted version of what
     `test_build_manifest_reproducible_byte_identical_direct_call` already checks end-to-end, isolated
     to the aggregation logic itself.
   - Location: `tests/tools/test_agent_monitoring_manifest.py`.

## Un-xfailing the 7 Named Tests — Coverage Outline

For each, what must be true before the `@pytest.mark.xfail` marker can be removed and the test
passes for real (not just "doesn't crash"):

1. **`test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`** — requires
   `manifest.py`'s `_scan_file`/`build_manifest` fix (New Test 6's production-code counterpart)
   landed and exercised against the real `agent-monitoring/` directory; the real `tools` shard
   directory must aggregate to exactly one `{"file": "tools.jsonl", ...}` record with the expected
   keys/types.
2. **`test_agent_monitoring_manifest.py::test_manifest_cli_reproducible_byte_identical_across_two_runs`**
   — requires the aggregate glob to be explicitly sorted (Risk #3 in investigation.md) so two
   subprocess runs of the real CLI produce byte-identical stdout.
3. **`test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call`**
   — same sortedness requirement, direct-call form.
4. **`test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`** —
   requires BOTH the production fix AND `_content_hash_snapshot()`/`_WATCHED_JSONL_FILES` in the test
   file itself to be updated to hash across the real shard directory's files instead of the retired
   single `agent-monitoring/tools.jsonl` path (investigation.md Risk #5) — otherwise the test
   helper's own `path.read_bytes()` still raises `FileNotFoundError` regardless of the production fix.
5. **`test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts`** — requires
   `_independently_derive_counts()`/`_REAL_TOOLS_FILE` in the test file itself updated to iterate the
   sorted real shard glob (investigation.md Risk #5) — the production side needs no independent fix
   here (skill_usage_metric.py has zero direct hardcoded reference; it fully inherits
   `generate_retro.py`'s fix), but the test's own independent-re-derivation helper does, since by
   design it deliberately does NOT call the function under test to compute its expected value.
6. **`test_generate_retro.py::test_correlation_real_corpus_produces_a_real_number`** — requires
   `generate_retro.DEFAULT_TOOLS_FILE`/`load_jsonl`'s fix landed; once `DEFAULT_TOOLS_FILE` points at
   the real shard directory and `load_jsonl` is dir-aware, `generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)`
   at this test's own call site returns the full real corpus and both `compliant_group`/
   `non_compliant_group` counts should be `> 0` against real historical Investigate-phase data.
7. **`test_generate_retro.py::test_parity_index_readpath_call_count_matches_real_corpus_state`** —
   same fix dependency as #6; once the full real corpus loads, `compute_parity_index_readpath_call_count()`
   should reproduce the pinned `result["count"] == 4` value (4 confirmed real historical
   `parity_index.py entry/impact/health` Bash calls, per the test's own inline history comment) — this
   count is a fixed historical fact about already-migrated, byte-preserved data, so it should not
   have changed due to sharding itself; if it does not equal 4 after the fix, that is a real bug in
   the glob/aggregation logic (e.g. a shard silently skipped), not a legitimate new "expected drift"
   requiring a baseline update — investigate before assuming the pinned value needs bumping.

## Scoped Pytest Commands

```bash
# Primary domain: agent-monitoring tooling and its tests
pytest tests/tools/test_build_index.py tests/tools/test_generate_retro.py \
       tests/tools/test_skill_usage_metric.py tests/tools/test_agent_monitoring_manifest.py \
       tests/tools/test_query.py tests/tools/test_validate_agent_monitoring.py \
       tests/tools/test_migrate_tools_shards.py -v

# Confirm done_checker_static.py truly has zero diff / zero new coupling to this ticket's changes
pytest tests/tools/ -k "done_checker" -v

# Full xfail-removal confirmation pass (must show 0 xfail, 0 xpass, all listed tests PASSED)
pytest tests/tools/test_agent_monitoring_manifest.py tests/tools/test_skill_usage_metric.py \
       tests/tools/test_generate_retro.py -v -rA | grep -E "XFAIL|XPASS|PASSED.*(manifest|skill_usage|correlation_real_corpus|parity_index_readpath_call_count)"
```

Never `pytest tests/` — scoped to `tests/tools/` (the agent-monitoring domain) per CLAUDE.md's
Testing Rule.

## Anti-Drift Test Guards

- **`test_build_index_never_touches_write_path_modules`** (existing, `test_build_index.py:378`) —
  already guards against `build_index.py` importing `writer`/`post_tool_hook`/`pre_tool_hook`/
  `record_run`/`record_events`; re-run after the fix to confirm the glob-resolution change didn't
  accidentally pull in a write-path import.
- **`test_manifest_source_never_calls_full_file_read_methods`** (existing,
  `test_agent_monitoring_manifest.py:93`) — re-run after the `manifest.py` fix to confirm the
  multi-shard aggregation still streams line-by-line rather than reverting to a full-file read for
  convenience.
- **New Test 6 (`test_manifest_tools_source_aggregates_all_shards`)** doubles as an anti-drift guard
  against a future change accidentally emitting one manifest record per shard file instead of one
  aggregate `"tools.jsonl"` record — a real, easy-to-make regression given the natural instinct to
  "just loop and emit one record per file."
- **`test_reuses_generate_retro_loader_not_a_second_loader`** (existing,
  `test_skill_usage_metric.py:47`) — re-run to confirm the fix did not introduce a second,
  independently-drifting loader in `skill_usage_metric.py` instead of fixing `generate_retro.py`'s
  shared one.
- **Existing `TestReadOnlyGuarantee::test_source_jsonl_files_byte_identical_after_build`** and the
  manifest suite's zero-mutation tests — re-run explicitly (not just incidentally via the full file
  run) to confirm the glob-based read path is still strictly read-only against every shard file, not
  just the one it happens to test with today.
- **`tools/gate_checks/done_checker_static.py` diff check** — `git diff --stat -- tools/gate_checks/done_checker_static.py`
  should show zero output after implementation; this is the ticket's own AC7 made concrete as a
  literal command, not just a claim.
