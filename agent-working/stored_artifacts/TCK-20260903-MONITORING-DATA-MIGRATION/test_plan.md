---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-MIGRATION
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Test Plan — TCK-20260903-MONITORING-DATA-MIGRATION

## Regression Surface

**Unit / synthetic-fixture (must keep passing unmodified — new script reuses these primitives'
patterns, does not change the modules they test):**
- `tests/tools/test_migrate_tools_shards.py` — the prior epic's own test file stays as regression
  coverage for the still-imported `bucket_lines_by_week`, `write_week_bucket`, `verify_migration`,
  `_parse_ts_to_week` functions (this ticket's new script is expected to import/reuse or closely
  mirror these, per investigation's finding that the merge/reconciliation logic itself needs no
  change to generalize). **Two tests in this file require updating as part of this ticket's own
  diff, not left broken** (see New Tests Required / conflicts below):
  - `test_gitattributes_no_longer_references_retired_tools_jsonl_path` (lines 283-286) — its
    `assert "agent-monitoring/tools/*.jsonl merge=union" in content` will fail once this ticket
    removes that exact line.
  - `_run_migration_against_copy()`-based integration tests
    (`test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved`,
    `test_full_corpus_verification_reports_exact_not_approximate_counts`) already `pytest.skip()`
    once `agent-monitoring/tools.jsonl` no longer exists (it already doesn't, per prior epic) — these
    stay skipped, no change needed, confirmed by design already tolerant.
  - `test_tools_jsonl_removed_from_working_tree_after_migration` (line 275-280) — already asserts the
    monolithic file is absent; stays passing unmodified (still true after this ticket).
- `tests/tools/test_monitoring_writer.py`, `test_monitoring_writer_lockfile_candidate.py`,
  `test_monitoring_writer_single_source.py` — `writer.py::write_line`/`write_lines` are reused
  unmodified by this ticket; these must all still pass with zero changes (confirms the "reused
  unmodified" scope guarantee).
- `tests/tools/test_post_tool_hook.py`, `test_record_events.py` (record_run has no dedicated file
  name matched above but is covered by its own suite), and any `test_record_run.py` — the live write
  path (child 1's own change) is untouched by this ticket; these must all still pass unmodified.
- `tests/tools/test_agent_monitoring_manifest.py`, `test_validate_agent_monitoring.py`,
  `test_build_index.py`, `test_generate_retro.py`, `test_query.py`, `test_done_ticket_monitoring_
  coverage.py`, `test_agent_ops_dashboard_ingest.py`, `test_agent_ops_dashboard_api.py`,
  `test_agent_ops_dashboard_stats.py` — all confirmed to construct their fixtures/caches against
  `tmp_path`-scoped repo roots (`DashboardCache(repo_root=tmp_path)` pattern confirmed for the
  dashboard suite; the others use their own tmp/synthetic fixtures per their own existing test
  design), not the real `agent-monitoring/` directory — unaffected by this ticket's retirement of the
  real `runs.jsonl`/`events.jsonl`/`tools/` paths. Run as a broad confirming pass, not because a
  break is expected.

**Integrity (this ticket's `.gitattributes` change directly affects two existing assertions — must
be updated as part of this ticket's own diff):**
- `tests/integrity/test_merge_union_gitattributes.py`:
  - `test_gitattributes_lines_present_for_three_legacy_union_merge_paths` (lines 85-99) currently
    asserts `agent-monitoring/runs.jsonl merge=union` and `agent-monitoring/events.jsonl merge=union`
    are present — must be updated once this ticket removes both lines (either rewrite the assertion
    to the remaining legacy line set, which after this ticket is empty, or retire the test with a
    comment explaining all 3 legacy sources are now retired, matching the docstring style the prior
    epic already used when it removed `tools.jsonl` from this same list).
  - `test_gitattributes_line_present_for_shard_glob` (lines 102-111) asserts
    `agent-monitoring/tools/*.jsonl merge=union` is present — must be updated/retired once this
    ticket removes that line too.
  - `test_concurrent_branch_appends_merge_without_conflict_markers` (parametrized, lines 42-83) is
    **unaffected** — it builds its own throwaway `.gitattributes` inline per test case (line 33) and
    does not read the real repo's file; no change required, though adding a parametrize case for the
    new `agent-monitoring/data/2026-W36/tools.jsonl`-shaped path would be a reasonable (not required)
    coverage addition.

**Run broadly (confirm nothing else in the monitoring/tooling suite assumes the legacy paths exist
as real files on disk):**
- `pytest tests/tools/ tests/integrity/ -k "monitoring or gitattributes or agent_ops_dashboard or migrate"`
  as a first broad pass before narrowing to the scoped command below.

## New Tests Required

New file: `tests/tools/test_migrate_monitoring_data.py` (mirrors `test_migrate_tools_shards.py`'s
own structure: synthetic-fixture unit tests → integration tests against a copy of the real corpus →
architecture guards run only post-retirement).

1. **`test_runs_bucket_by_start_ts_preserving_order`**
   Category: unit. Verifies: a `runs`-source bucketing function groups synthetic records by their
   `start_ts` field's ISO week, preserving original file order within each bucket (mirrors
   `test_within_week_bucket_preserves_original_append_order`, field changed to `start_ts`).
   Location: `tests/tools/test_migrate_monitoring_data.py`.

2. **`test_events_bucket_by_ts_preserving_order`**
   Category: unit. Verifies: the `events`-source bucketing path groups by `ts` (may directly reuse
   `bucket_lines_by_week` if the field name is parameterized, or a near-identical sibling) with the
   same order-preservation guarantee. Location: same file.

3. **`test_runs_and_events_fallback_field_priority_documented_and_correct`**
   Category: unit. Verifies: a record missing its primary field (`start_ts`/`ts`) but carrying a
   documented alternate (`timestamp`, `started_at`, etc., per investigation's quantified list) routes
   to the correct ISO week via the alternate, not straight to `unknown-week` — and a record with
   truly no usable timestamp-like field (the `"ts": null` shape, and the pure-`event_type`/`details`
   shape confirmed in investigation, 22 real examples in `events.jsonl`) routes to the shared
   `UNKNOWN_WEEK_KEY`/`unknown-week` fallback bucket. Location: same file.

4. **`test_tools_shard_relocation_parses_week_from_filename_not_content`**
   Category: unit. Verifies: for the `tools` source, the target week is derived from each existing
   shard's filename (`tools-2026-W24.jsonl` → `2026-W24`; `tools-unknown-week.jsonl` → the same
   fallback key used for `runs`/`events`), and the shard's entire content is treated as one
   contiguous bucket — no per-line `json.loads()`/re-bucketing occurs during this step (assert via a
   spy/monkeypatch that no per-line week-computation function is called for the `tools` source, or
   equivalently assert output bucket boundaries exactly match input file boundaries regardless of
   each line's own `ts`). Location: same file.

5. **`test_case_b_merge_precedes_live_rows_for_all_three_sources`**
   Category: unit/integration. Verifies: `write_week_bucket()` (or its generalized equivalent) applied
   independently to each of `runs`/`events`/`tools` for a week that already has live content produces
   `migrated + live` order (mirrors `test_current_week_shard_migrated_rows_precede_existing_live_
   rows`, parametrized or duplicated across all 3 sources — this is explicitly called out as a hard
   AC: "for each source independently"). Location: same file.

6. **`test_migration_uses_one_write_lines_call_per_week_per_source`**
   Category: unit. Verifies: exactly one `write_lines()` call per `(week, source)` pair, never split
   into two calls even when merging with live content (mirrors `test_migration_uses_write_lines_one_
   lock_per_week_batch`, extended to assert across all 3 sources independently — a batch for
   `runs`/`2026-W36` and a batch for `tools`/`2026-W36` in the same run must be two separate
   `write_lines()` calls to two separate target files, never combined). Location: same file.

7. **`test_every_pre_cutover_line_lands_in_exactly_one_file_per_source_content_preserved`**
   Category: integration, against a **copy of the real historical corpus** (never the real
   `agent-monitoring/` directory — mirrors `_run_migration_against_copy()`'s tmp_path-copy pattern
   exactly, extended to copy `runs.jsonl`, `events.jsonl`, and all `tools/tools-*.jsonl` shards, plus
   whatever real `agent-monitoring/data/*/` week folders currently exist, found dynamically never
   hardcoded). Verifies per-source multiset equality (`collections.Counter`) between source lines and
   migrated lines, for all 3 sources independently. Location: same file.

8. **`test_full_corpus_verification_reports_exact_counts_per_source`**
   Category: integration, against the real-corpus copy. Verifies `verify_migration()`'s (or its
   3-source-aware equivalent's) `reconciles_exactly`/`content_preserved`/`all_lines_parse` all report
   `True` independently per source, and that `explained_delta` for whichever source(s) currently have
   live current-week content is `> 0` (mirrors `test_full_corpus_verification_reports_exact_not_
   approximate_counts`'s explicit non-zero-delta guard, extended per-source — investigation confirmed
   at write time only `tools` has live current-week content, so this test must not hardcode an
   assumption that `runs`/`events` also have a nonzero delta; check dynamically). Location: same
   file.

9. **`test_tools_relocation_is_route_only_not_re_bucketed`**
   Category: integration, against the real-corpus copy. Verifies specifically that every line inside
   a given `tools-YYYY-Www.jsonl` shard lands in the *same* target week folder regardless of that
   line's own `ts` content (i.e., confirms relocation ignores per-line `ts` entirely) — this is the
   test that would catch an accidental "helpfully" re-bucketing of `tools` data that silently
   reshuffles a handful of lines whose `ts` happens to fall in a different ISO week than their shard's
   filename claims (a real possible edge case worth explicitly testing, not just asserting the happy
   path). Location: same file.

10. **`test_legacy_paths_removed_after_migration`** (architecture guard, run only after Step 5's
    retirement — mirrors `test_tools_jsonl_removed_from_working_tree_after_migration`)
    Category: architecture guard. Verifies: none of `agent-monitoring/runs.jsonl`,
    `agent-monitoring/events.jsonl`, `agent-monitoring/tools/` exist in the working tree.
    Location: same file.

11. **`test_gitattributes_no_longer_references_any_of_the_3_retired_paths`** (architecture guard)
    Category: architecture guard. Verifies: `.gitattributes` contains none of the 3 removed
    `merge=union` lines, and still contains `agent-monitoring/data/*/*.jsonl merge=union`.
    Location: same file — distinct from, and a superset of, the two now-updated
    `tests/integrity/test_merge_union_gitattributes.py` assertions above (keeping both is fine; they
    check the same fact from two different test suites, matching the prior epic's own precedent of
    having both a `migrate_tools_shards`-local guard and a separate `tests/integrity/` guard).

## Scoped Pytest Commands

```
pytest tests/tools/test_migrate_monitoring_data.py tests/tools/test_migrate_tools_shards.py \
       tests/integrity/test_merge_union_gitattributes.py -v
```

Broader regression confirmation pass (scoped to the monitoring/tooling domain, not the full suite):

```
pytest tests/tools/ tests/integrity/ -k "monitoring or gitattributes or agent_ops_dashboard or migrate or writer" -v
```

Never: `pytest tests/` (full suite) — out of scope for this ticket's domain per repo testing
convention.

## Anti-Drift Test Guards

- **`test_tools_relocation_is_route_only_not_re_bucketed`** (#9 above) is the specific guard against
  the most likely scope-creep failure mode for this ticket: "helpfully" re-running per-line `ts`
  bucketing on `tools` data that's already correctly bucketed by filename, which could silently
  reshuffle a small number of lines whose own `ts` disagrees with their shard filename's claimed
  week (a real, plausible edge case given the prior epic's own tolerant-parser fallback logic).
- **`test_case_b_merge_precedes_live_rows_for_all_three_sources`** (#5) and
  `test_migration_uses_one_write_lines_call_per_week_per_source` (#6), run independently per source,
  guard against a subtle three-source generalization bug: accidentally sharing one `write_lines()`
  call across two different sources' buckets for the same week (e.g. writing `runs` and `events`
  historical rows for `2026-W36` into a single combined call) — this would violate both the "one
  lock = one contiguous batch in one file" contract and produce a file mixing schemas.
- **`test_runs_and_events_fallback_field_priority_documented_and_correct`** (#3) guards against
  silently routing the wrong count of records to `unknown-week` — investigation's quantified finding
  (0 truly-timestamp-less `runs.jsonl` records, 22 truly-timestamp-less `events.jsonl` records) is a
  regression-detectable fact: if a future change to the fallback-field priority list causes more
  records to fall through to `unknown-week` than this evidence-backed count, this test should catch
  it.
- **Existing `test_migrate_tools_shards.py` tests kept exactly as-is (not deleted, not weakened)**
  serve as the anti-drift guard that this ticket's generalization doesn't silently change the
  already-correct rename-aside/reconciliation mechanics for the `tools` source's underlying
  primitives — any accidental behavior change there would show up as a failure in the prior epic's
  own still-active synthetic-fixture tests before it ever reaches the new 3-source script.
- **`test_gitattributes_no_longer_references_any_of_the_3_retired_paths`** (#11) plus the two updated
  `tests/integrity/test_merge_union_gitattributes.py` assertions together guard against a partial
  `.gitattributes` edit (e.g. removing 2 of the 3 legacy lines but missing one) — a real, easy-to-make
  mistake given this ticket retires 3 lines in one edit rather than the prior epic's single line.
