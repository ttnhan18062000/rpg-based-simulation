---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-MIGRATION
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Test Plan — TCK-20260902-MONITORING-SHARD-MIGRATION

## Regression Surface

### Unit — writer/lock protocol (unchanged, must keep passing)
- `tests/tools/test_monitoring_writer.py` — all 9 tests (`write_line`/`write_lines` lock protocol,
  concurrent writers, stale-lock recovery, diagnostic sidecar). The migration script calls
  `write_lines()` unmodified; these tests prove that contract still holds.
- `tests/tools/test_monitoring_writer_single_source.py` — all 4 tests (no call site bypasses the
  shared writer / reimplements locking). The new migration script is itself a new call site and
  must be added to whatever allowlist this test scans, or it will (correctly) fail if the script
  does its own file I/O outside `write_lines()`.
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`.

### Unit/integration — write path (child 1, must not regress)
- `tests/tools/test_post_tool_hook.py` — specifically
  `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`,
  `test_two_different_iso_weeks_write_to_two_distinct_shard_files`,
  `test_iso_week_shard_directory_created_on_first_write`,
  `test_iso_week_computation_failure_does_not_propagate`, plus the other 15 tests in the file. None
  of these read the real `agent-monitoring/` directory (all use `tmp_path`), so they are unaffected
  by retiring the real `tools.jsonl` — they exist to prove they must **stay** unaffected.

### Integration — `.gitattributes` union-merge behavior (2 tests will need direct edits, not just
"keep passing" — see New Tests Required)
- `tests/integrity/test_merge_union_gitattributes.py` —
  `test_concurrent_branch_appends_merge_without_conflict_markers` (parametrized, throwaway-repo
  based, unaffected by this ticket's real-repo `.gitattributes` edit — keep passing as-is);
  `test_gitattributes_lines_present_for_all_four_union_merge_paths` and
  `test_gitattributes_line_present_for_shard_glob` **will fail** once the legacy
  `agent-monitoring/tools.jsonl merge=union` line is removed from the real `.gitattributes` — these
  must be edited in the same change (see New Tests Required).

### Real-corpus tests that will hard-fail once `agent-monitoring/tools.jsonl` no longer exists
(must be resolved as part of this ticket's implementation — Plan must decide how; see
investigation.md Risk #1)
- `tests/tools/test_agent_monitoring_manifest.py` — all 5 tests, run against the real
  `agent-monitoring/` directory by explicit design (never `tmp_path`):
  `test_build_manifest_shape_against_real_corpus` (hardcodes `len(records) == 3` and the exact
  filename set including `"tools.jsonl"`), `test_manifest_cli_reproducible_byte_identical_across_two_runs`,
  `test_build_manifest_reproducible_byte_identical_direct_call`,
  `test_manifest_source_never_calls_full_file_read_methods` (unaffected — static-analysis test, no
  file I/O), `test_manifest_run_against_real_corpus_produces_zero_diff`. 4 of the 5 will raise
  `FileNotFoundError` via `manifest.py::_scan_file()`'s unconditional `open(path, "rb")`.
- `tests/tools/test_skill_usage_metric.py` — the real-corpus integration test that does
  `open(_REAL_TOOLS_FILE, encoding="utf-8")` unconditionally (line 136) will raise
  `FileNotFoundError`. (The synthetic-fixture unit tests in the same file are unaffected.)

### Regression surface unaffected but worth re-confirming post-migration (no code change expected,
verify by inspection/run)
- `tests/agent_replay/test_no_mutation_snapshot.py` — `_watched_files()` globs
  `agent-monitoring/*.jsonl`, self-heals once `tools.jsonl` is gone; `_WATCHED_GIT_PATHSPECS`'s
  literal `"agent-monitoring/tools.jsonl"` entry becomes an inert no-op pathspec for
  `git status --porcelain`, not an error — confirm this test still passes post-migration without
  modification, as a smoke check that the reasoning above is correct in practice, not just in
  theory.
- `tests/tools/test_generate_retro.py`, `tests/tools/test_build_index.py`,
  `tests/tools/test_record_events.py`, `tests/tools/test_validate_agent_monitoring.py` — all use
  synthetic `tmp_path` fixtures for their `tools.jsonl`-shaped inputs, never the real file. Should
  keep passing unmodified; run as a smoke check.

## New Tests Required

- **Test name**: `test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved`
  **Category**: integration (runs the real migration script against a snapshot/copy of the real
  historical file, or against the real file in a read-only dry-run mode if the script supports one)
  **Verifies**: total resulting shard line count (summed across every `agent-monitoring/tools/
  tools-YYYY-Www.jsonl` file the migration produces, plus the fallback-week file) equals the exact
  pre-migration line count of `agent-monitoring/tools.jsonl` captured at run start; every original
  line, re-parsed via `json.loads`, is found in exactly one output shard with identical content
  (modulo trailing newline); no line appears in two shards.
  **Where**: `tests/tools/test_migrate_tools_shards.py` (module name mirrors the script's own
  filename, per the ticket's suggested `migrate_tools_shards.py`).

- **Test name**: `test_within_week_bucket_preserves_original_append_order`
  **Category**: unit (synthetic fixture, deterministic input) **Verifies**: for a synthetic input
  file with multiple lines sharing an ISO week but non-monotonic content, the resulting shard's
  line order matches the original file's line order exactly (not re-sorted by `ts`, not sorted by
  any other key). **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_current_week_shard_migrated_rows_precede_existing_live_rows`
  **Category**: integration (synthetic fixture: pre-seed a `tools-YYYY-Www.jsonl` file with N "live"
  rows before running the migration script against a synthetic historical file with M rows for that
  same week) **Verifies**: post-migration, the shard file has exactly M+N lines, the first M are the
  migrated historical rows in original order, the last N are untouched, byte-identical to what was
  there before migration ran — proves the "append, never overwrite; migrated rows sort first" AC.
  **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_migration_uses_write_lines_one_lock_per_week_batch`
  **Category**: unit (monkeypatch/spy on `writer.write_lines`) **Verifies**: the migration script
  calls `tools/agent-monitoring/writer.py::write_lines()` exactly once per week bucket (not once
  per line, not a bare unlocked `open(..., "a")`), and never calls `write_line()` for bulk migrated
  content. **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_malformed_and_off_schema_rows_route_without_erroring`
  **Category**: unit (synthetic fixture reproducing the 2 real off-schema shapes found: missing
  `tool`+`seq` run-summary row, and missing-`tool`-only row with reduced-precision `ts`) **Verifies**:
  both rows are still routed to a real week bucket by whatever `ts` they carry (not dropped, not
  raising), with content byte-for-byte preserved. **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_missing_ts_row_routes_to_documented_fallback_bucket`
  **Category**: unit (synthetic fixture: one line with no `ts` field at all, matching the real
  file's line 1 shape) **Verifies**: the row lands in the fallback bucket Plan decides on (e.g.
  `agent-monitoring/tools/tools-unknown-week.jsonl`), is not silently dropped, and does not crash
  the run. **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_ts_format_variants_all_bucket_to_correct_week`
  **Category**: unit (synthetic fixture: standard `%Y-%m-%dT%H:%M:%S.%fZ` row, and the real
  reduced-precision `%Y-%m-%dT%H:%M:%S` no-`Z` row found at line 55,124) **Verifies**: both land in
  the correct `%G-W%V` week bucket — proves the migration's `ts` parser is not a single rigid
  `strptime` format string. **Where**: `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_full_corpus_verification_reports_exact_not_approximate_counts`
  **Category**: integration (real corpus or full copy of it) **Verifies**: the migration script's
  own zero-data-loss verification step reports an exact total-line-count match (not a sampled
  estimate), and explicitly reports the "current-week live rows are an explained delta, not data
  loss" distinction the ticket's Acceptance Criteria requires, rather than a bare
  `original_count == migrated_count` that would fail for the current week. **Where**:
  `tests/tools/test_migrate_tools_shards.py`.

- **Test name**: `test_tools_jsonl_removed_from_working_tree_after_migration`
  **Category**: architecture guard **Verifies**: `agent-monitoring/tools.jsonl` no longer exists on
  disk after the full migration+retirement flow runs (AC: "no longer exists in the working tree");
  paired with a `git log --follow -- agent-monitoring/tools.jsonl` check (or equivalent) proving
  history is still recoverable. **Where**: `tests/tools/test_migrate_tools_shards.py` or
  `tests/integrity/`.

- **Test name**: `test_gitattributes_no_longer_references_retired_tools_jsonl_path`
  **Category**: architecture guard (replaces/edits the now-failing assertions in
  `tests/integrity/test_merge_union_gitattributes.py`) **Verifies**: the real `.gitattributes` no
  longer contains the literal string `agent-monitoring/tools.jsonl merge=union`, while
  `agent-monitoring/tools/*.jsonl merge=union` (and the 3 other legacy-file union-merge lines that
  are untouched by this ticket: `runs.jsonl`, `events.jsonl`, `tickets/working_log.csv`) remain
  present. **Where**: edit
  `tests/integrity/test_merge_union_gitattributes.py::test_gitattributes_lines_present_for_all_four_union_merge_paths`
  (drop `tools.jsonl` from its expected-path tuple, or rename/reduce it to 3 paths) and
  `::test_gitattributes_line_present_for_shard_glob` (drop the second assertion that the legacy
  line is still present, update its docstring to say this ticket already retired it).

- **Test name**: `test_manifest_no_longer_scans_retired_tools_jsonl` (only if Plan decides to fix
  `manifest.py` as part of this ticket — see investigation.md Risk #1 option (a))
  **Category**: unit + architecture guard **Verifies**: `manifest.py::build_manifest()` either drops
  `tools.jsonl` from `_FILES_BY_SOURCE` or is pointed at the shard glob, and no longer raises
  `FileNotFoundError`; `tests/tools/test_agent_monitoring_manifest.py`'s real-corpus tests are
  updated to match the new expected file set. **Where**: `tests/tools/test_agent_monitoring_manifest.py`.
  **Flag for Plan, not pre-decided here**: if Plan instead defers this to child 3, this test is not
  needed by this ticket, but the 4 real-corpus manifest tests must then be explicitly
  skipped/xfailed with a comment pointing at child 3, not left to fail silently in CI.

## Scoped Pytest Commands

```bash
# Migration script's own new tests (once written)
pytest tests/tools/test_migrate_tools_shards.py -v

# Writer/lock-protocol regression surface (must not change)
pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py \
       tests/tools/test_monitoring_writer_lockfile_candidate.py -v

# Write-path regression surface (child 1, must not change)
pytest tests/tools/test_post_tool_hook.py -v

# .gitattributes integration (must be updated, then pass)
pytest tests/integrity/test_merge_union_gitattributes.py -v

# Real-corpus consumer surface directly at risk from retiring tools.jsonl
pytest tests/tools/test_agent_monitoring_manifest.py tests/tools/test_skill_usage_metric.py -v

# No-mutation snapshot smoke check (glob-based, should self-heal)
pytest tests/agent_replay/test_no_mutation_snapshot.py -v

# Broader agent-monitoring tools/ regression sweep (synthetic-fixture based, should be unaffected)
pytest tests/tools/ -k "monitoring or agent_monitoring or generate_retro or build_index or record_events or validate_agent_monitoring" -v
```

Never `pytest tests/` — scoped to the `agent-monitoring` tooling domain (`tests/tools/`,
`tests/integrity/test_merge_union_gitattributes.py`, `tests/agent_replay/`) per CLAUDE.md's
Testing Rule.

## Anti-Drift Test Guards

- **`test_migration_uses_write_lines_one_lock_per_week_batch`** (above) directly guards against the
  most likely silent-scope-creep failure mode: an implementer writing a bare unlocked
  `open(shard_path, "a")` loop instead of routing through `writer.py::write_lines()`, which would
  violate the ticket's explicit "one lock acquisition per batch" requirement and reintroduce the
  exact interleaved-write hazard `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK` fixed.
- **`test_within_week_bucket_preserves_original_append_order`** guards against an implementer
  "helpfully" re-sorting rows by `ts` within a bucket (rows sharing a week are not necessarily
  monotonic by `ts` if any clock skew or manual record exists) — the ticket requires *original
  append/line-position order*, not `ts`-sorted order.
- **`test_current_week_shard_migrated_rows_precede_existing_live_rows`** guards against the two
  most damaging failure modes for the one shard file already live: overwriting/truncating it
  (destroying this session's own already-recorded history) or appending migrated rows *after* the
  live rows instead of before (violating chronological order across the merge boundary).
  **`test_malformed_and_off_schema_rows_route_without_erroring`** and
  **`test_missing_ts_row_routes_to_documented_fallback_bucket`** guard against the migration script
  crashing on, or silently dropping, the 2+1 real known off-schema/ts-less lines — confirmed by this
  investigation's own full-corpus scan to be the complete and only set of anomalies in the real
  file, not a guessed/hypothetical set.
- **`test_gitattributes_no_longer_references_retired_tools_jsonl_path`** guards against the two
  pre-existing `.gitattributes` tests silently going red in CI without anyone connecting the
  failure to this ticket's own in-scope edit.
- The real-corpus `manifest.py`/`skill_usage_metric.py` test failures are the single largest
  anti-drift risk of this whole ticket: an implementer who runs the migration script,
  `git rm`s `tools.jsonl`, and stops there (matching the ticket's literal Acceptance Criteria)
  will leave CI red on 5 tests that were not in this ticket's own Related Code Areas. Re-running
  the full scoped command list above — not just the migration script's own new tests — before
  claiming completion is the guard against this.
