---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
artifact_type: test_plan
tags: [agent-monitoring, observability, hooks, data-quality]
---

# Test Plan — TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Regression Surface

Existing tests that must keep passing (all under `unit` category — none of this subsystem's tests
are integration/arena-combat; there is no arena-combat surface here at all):

- `tests/tools/test_post_tool_hook.py` — all existing tests EXCEPT the ones asserting the OLD
  shard path, which must be *updated in place* (not just left passing) since they currently assert
  a path this ticket retires:
  - `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl` — update to assert
    `agent-monitoring/data/<week>/tools.jsonl`, and rename to reflect the new target (e.g.
    `test_writes_to_unified_week_folder_not_legacy_tools_shard_or_monolith`).
  - `test_two_different_iso_weeks_write_to_two_distinct_shard_files` — update both asserted paths.
  - `test_iso_week_shard_directory_created_on_first_write` — update asserted directory
    (`agent-monitoring/data/<week>/`, not `agent-monitoring/tools/`).
  - `test_iso_week_computation_failure_does_not_propagate` — update its two negative-path
    assertions (`not (tmp_path / "agent-monitoring" / "tools").exists()` and `.../tools.jsonl`)
    to also assert `not (tmp_path / "agent-monitoring" / "data").exists()`.
  - `test_locking_failure_does_not_propagate` — update the diagnostic-path assertion (currently
    `tmp_path / "agent-monitoring" / "tools" / ".writer_health.jsonl"`) to
    `tmp_path / "agent-monitoring" / "data" / "<frozen-week>" / ".writer_health.jsonl"` — this test
    doesn't currently freeze "now," so it needs either a frozen-now shim added or an
    unfrozen-but-real-"now"-computed week folder in the assertion (compute the same
    `datetime.now(timezone.utc).strftime("%G-W%V")` in the test body to build the expected path).
  - `_tools_lines()` helper — update to read from `agent-monitoring/data/<week>/tools.jsonl`.
  - All other existing tests (`test_single_writer_produces_one_well_formed_line`,
    `test_phase_and_agent_included_when_sidecar_present`,
    `test_execution_identity_fields_included_when_sidecar_present`,
    `test_phase_and_agent_default_to_none_on_partial_sidecar`,
    `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`,
    `test_scoped_sidecar_preferred_over_stale_unscoped_sidecar`,
    `test_two_concurrent_sessions_each_attributed_correctly`,
    `test_foreign_scoped_sidecar_not_read_by_different_session`,
    `test_second_call_in_ad_hoc_session_reads_own_sentinel_not_unscoped_file`,
    `test_real_writesidecar_overwrites_earlier_ad_hoc_sentinel`,
    `test_ad_hoc_sentinel_pruned_identically_to_any_scoped_file`,
    `test_stale_scoped_sidecar_pruned`, `test_fresh_scoped_sidecar_not_pruned`) all go through
    `_tools_lines()` and must keep passing unmodified once that helper is updated — they exercise
    sidecar/attribution logic orthogonal to the write-path change.
- `tests/tools/test_record_run.py` — `validate_record`/`compute_duration_s` unit tests
  (unaffected by path change, no update needed): `test_valid_record_has_no_errors`,
  `test_missing_key_rejected`, `test_null_required_field_rejected_identically_to_missing_key`,
  `test_multiple_null_fields_all_reported`, `test_falsy_but_non_null_value_still_passes`,
  `test_missing_agent_count_rejected`, `test_null_agent_count_rejected`,
  `test_agent_count_zero_is_falsy_but_valid`, `test_compute_duration_s_from_valid_start_and_end`,
  `test_compute_duration_s_none_when_end_ts_missing`,
  `test_compute_duration_s_none_when_end_ts_null`,
  `test_compute_duration_s_none_when_end_before_start`,
  `test_compute_duration_s_zero_when_end_equals_start`. `TestExitCodeContract` (both tests) are
  path-independent (only assert stderr/exit code on validation failure, before any write happens)
  — no update needed. `TestDurationWrittenToRecord` (3 tests) and
  `test_execution_identity_fields_pass_through_unchanged` DO read back
  `tmp_path / "agent-monitoring" / "runs.jsonl"` directly — must update to
  `tmp_path / "agent-monitoring" / "data" / "<week>" / "runs.jsonl"` (compute the real current
  week in the test body via `datetime.now(timezone.utc).strftime("%G-W%V")`, since these tests
  don't need a frozen clock — they only need to read back whatever week the write actually landed
  in). `test_append_failure_is_non_blocking` monkeypatches `record_run.write_line` directly — no
  path assertion, no update needed.
- `tests/tools/test_record_events.py` — `validate_record`/`warn_vocabulary_drift` unit tests
  unaffected by path change: `test_valid_event_has_no_errors`, `test_missing_key_rejected`,
  `test_null_required_field_rejected_identically_to_missing_key`, `test_null_agent_rejected`,
  `test_null_summary_does_not_crash_and_is_reported`, `TestExitCodeContract` (3 tests),
  `TestVocabularyWarning` (7 tests). Tests needing update because they read back
  `agent-monitoring/events.jsonl` directly or write to the old `agent-monitoring/tools.jsonl` via
  `_write_tools_jsonl()`:
  - `_write_tools_jsonl(tmp_path, rows)` helper — update to write into
    `tmp_path / "agent-monitoring" / "data" / "<week>" / "tools.jsonl"` (the week used must match
    whatever week the glob-based `compute_tool_stats()` will actually search at test run time —
    either freeze "now" for these tests, or write into the real current week computed the same way
    the source does).
  - `test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`,
    `test_cost_proxy_score_absent_when_no_tools_jsonl_exists`,
    `test_compute_tool_stats_only_targets_implement_ticket_workflow` — all depend on
    `_write_tools_jsonl()`; update alongside it. `test_cost_proxy_score_absent_when_no_tools_jsonl_
    exists` specifically exercises the "no matching files at all" branch — with a glob-based read,
    this now means "the glob matches zero files" rather than "the single file doesn't exist";
    behaviorally identical (`compute_tool_stats` must still return `0`/`0.0`, not crash), but the
    test's own docstring/comment should be updated to describe the glob-empty case accurately.
  - `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` — pure
    `compute_tool_stats(records)` call with `wanted` computed as empty (no `implement-ticket`
    workflow records) — never reaches the file-read branch at all, no update needed.
  - `test_execution_identity_fields_pass_through_unchanged`,
    `test_vocabulary_warning_never_raises_or_exits` (inside `TestVocabularyWarning`),
    `test_append_failure_is_non_blocking`, `test_batch_write_holds_contiguous_lines_under_
    concurrent_writer` — all read back or write to `agent-monitoring/events.jsonl` directly; update
    read/write paths to the new `agent-monitoring/data/<week>/events.jsonl` location (real current
    week, no frozen clock needed for these either, same reasoning as `record_run.py`'s equivalent
    tests).

## New Tests Required

1. **`test_writes_to_unified_week_folder` (post_tool_hook.py)**
   - Category: unit (subprocess-driven, matching this file's established pattern — the hook is not
     importable).
   - Verifies: with a frozen "now" (reuse `_run_hook_with_frozen_now()`), the hook appends its
     record to `agent-monitoring/data/<expected-ISO-week>/tools.jsonl`, and NOT to
     `agent-monitoring/tools/tools-*.jsonl` (prior epoch's shape) or `agent-monitoring/tools.jsonl`
     (the original, already-retired legacy monolith).
   - Location: `tests/tools/test_post_tool_hook.py` (replaces/renames
     `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl` per Regression Surface above —
     counts as satisfying Acceptance Criteria bullet 1 for `post_tool_hook.py`).

2. **`test_writes_to_unified_week_folder` (record_run.py)**
   - Category: unit (in-process, via `record_run.main()` called directly with `monkeypatch.chdir`
     and a monkeypatched `datetime.now`, following `test_append_failure_is_non_blocking`'s existing
     in-process pattern — no subprocess shim needed since `record_run.py` is importable).
   - Verifies: a run record lands at `agent-monitoring/data/<expected-ISO-week>/runs.jsonl`, and
     `agent-monitoring/runs.jsonl` (the legacy monolithic path) is NOT created.
   - Location: `tests/tools/test_record_run.py` (satisfies Acceptance Criteria bullet 2, half 1).

3. **`test_writes_to_unified_week_folder` (record_events.py)**
   - Category: unit (in-process, mirroring #2's approach via `record_events.main()`).
   - Verifies: an event record lands at `agent-monitoring/data/<expected-ISO-week>/events.jsonl`,
     and `agent-monitoring/events.jsonl` (legacy path) is NOT created.
   - Location: `tests/tools/test_record_events.py` (satisfies Acceptance Criteria bullet 2, half 2).

4. **`test_two_different_iso_weeks_write_to_two_distinct_week_folders`** — one per source (3 tests
   total, or one parametrized test per file if the implementer prefers, matching each file's
   existing style — `test_post_tool_hook.py` already has a non-parametrized precedent for this
   exact shape).
   - Category: unit.
   - Verifies: two writes under two different frozen/mocked "now" values (e.g. one in `2026-W36`,
     one in `2026-W37`, matching the existing `post_tool_hook.py` test's week choices for
     consistency) land in two distinct `agent-monitoring/data/<week>/` folders, each containing
     exactly its own record.
   - Location: one test per file (`test_post_tool_hook.py` already has this — just needs its
     asserted paths updated per Regression Surface, doesn't need a NEW test unless the
     implementer wants a dedicated week-boundary variant); `test_record_run.py`,
     `test_record_events.py` need new tests here since they've never had one.
   - Satisfies Acceptance Criteria bullet 3.

5. **`test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder`
   (record_events.py) — THE CRITICAL REGRESSION TEST for the bug fix.**
   - Category: unit (integration-flavored at the file-system/subprocess level, but still scoped to
     one module — categorize as `unit` per this repo's `tests/tools/` convention, not
     `integration`, matching every other test in this file).
   - Design:
     ```python
     def test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder(tmp_path):
         # Simulates a paused/resumed session (TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
         # precedent): tool-call rows for this (run_id, seq) were written in an EARLIER week than
         # the event being recorded now. This is the exact scenario that motivates the full-corpus
         # glob fix over a current-week-only read.
         data_dir = tmp_path / "agent-monitoring" / "data"
         # Week the tool calls actually happened in (earlier, "pre-pause" week):
         (data_dir / "2026-W20").mkdir(parents=True)
         with open(data_dir / "2026-W20" / "tools.jsonl", "w") as f:
             for row in [
                 {"run_id": "TCK-CROSS-WEEK-TEST", "seq": 4, "tool": "Bash", "duration_ms": 1000},
                 {"run_id": "TCK-CROSS-WEEK-TEST", "seq": 4, "tool": "Read", "duration_ms": 5},
             ]:
                 f.write(json.dumps(row) + "\n")
         # A second week folder with unrelated rows, proving the glob reads ALL weeks, not just
         # the two involved, and doesn't accidentally cross-contaminate keys:
         (data_dir / "2026-W21").mkdir(parents=True)
         with open(data_dir / "2026-W21" / "tools.jsonl", "w") as f:
             f.write(json.dumps({"run_id": "TCK-UNRELATED", "seq": 1, "tool": "Bash", "duration_ms": 1}) + "\n")

         record = {**_VALID_EVENT, "run_id": "TCK-CROSS-WEEK-TEST", "seq": 4}
         result = subprocess.run(
             [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
             capture_output=True, text=True, cwd=tmp_path,
         )
         assert result.returncode == 0

         # Event itself was written "now" — whatever the real current week is — separate from
         # where the tool-call ground truth lives (2026-W20). Read back from wherever the source
         # actually put it (real current week, computed the same way the source does).
         current_week = datetime.now(timezone.utc).strftime("%G-W%V")
         written = json.loads(
             (data_dir / current_week / "events.jsonl").read_text().strip()
         )
         assert written["tool_call_count"] == 2  # nonzero — the actual bug being fixed
         assert written["cost_proxy_score"] > 0.0
     ```
   - Verifies: `record_events.py` computes a correct nonzero `tool_call_count`/`cost_proxy_score`
     for a `(run_id, seq)` pair whose matching tool-call rows live in a week folder *different*
     from the one the event itself is written into — directly exercises the multi-week glob, not
     just "does the glob find the current week's own file" (which would be a weaker test that
     could pass even with a narrower, wrong current-week-only fix).
   - Location: `tests/tools/test_record_events.py`, alongside the existing `TCK-20260719-COST-
     PROXY-WRITE-PATH` test block.
   - **This is Acceptance Criteria bullet 4 — the highest-priority test in this ticket.** Without
     it, a regression back to a narrower (e.g. current-week-only) glob would silently reintroduce a
     variant of the same class of bug this ticket fixes, and nothing else in the regression surface
     would catch it (every other `compute_tool_stats` test uses same-week fixtures).

6. **`test_tool_call_count_sums_rows_across_multiple_weeks_for_same_key`** (optional but
   recommended companion to #5) — seed matching rows for the SAME `(run_id, seq)` split across two
   different week folders (simulating a session that itself straddled a week boundary while still
   active, distinct from pause/resume) and assert the counts are additive across both files, not
   just correctly read from whichever one file happens to match. Strengthens confidence beyond #5's
   single-non-current-week case. Location: same file, same block.

7. **`test_writer_py_directory_creation_still_correct_for_two_level_nesting`** (architecture-guard
   style, but scoped narrowly — not a broad architecture test) — confirms the ordering hazard
   identified in investigation.md (caller's own `mkdir` before `write_line`, since `_acquire_lock`
   runs before `write_line`'s own internal `mkdir`) still holds for the new two-levels-deep
   `agent-monitoring/data/<week>/` path, by deleting/never-creating the target directory ahead of
   time and confirming the write still succeeds (proving the caller-side `mkdir` call was correctly
   preserved in each of the 3 rewritten call sites, not accidentally dropped during the path-string
   edit). One instance per source file (3 tests), or fold into each source's existing
   `test_iso_week_shard_directory_created_on_first_write`-style test (recommended — avoids
   duplicating the same assertion pattern 3x with only cosmetic differences).
   - Category: architecture guard (durable-state / write-path integrity, per CLAUDE.md's
     Architecture Rule: "Authoritative application is the only place durable state should be
     committed" — confirming the directory-creation precondition for that commit path).
   - Location: one per test file, or folded into #4 above.

## Scoped Pytest Commands

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v
```

`writer.py`'s own test file is `tests/tools/test_monitoring_writer.py` (confirmed via directory
listing; not read in this investigation since the ticket scopes `writer.py` as read-only/
unmodified, but its behavior is load-bearing for all 3 rewritten callers — worth a sanity re-run
alongside the 3 rewritten sources to confirm the shared writer still behaves correctly against the
new nested target paths):

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_monitoring_writer.py -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` for this ticket's affected domain
(`agent-monitoring/` write path). No `src/` or simulation-domain test directory is affected.

## Anti-Drift Test Guards

- **`.gitattributes` line-count guard**: a quick assertion (can be a one-off `grep -c` in the
  Verify phase rather than a pytest test, since `.gitattributes` has no existing test file) that
  the 3 legacy `merge=union` lines are still present verbatim AND the new unified-glob line is
  present — catches an implementer accidentally replacing rather than adding, which would silently
  break merge behavior for any in-flight branch still appending to the legacy paths.
- **`writer.py` no-diff guard**: `git diff --stat tools/agent-monitoring/writer.py` should show no
  changes at all after implementation — if it shows any diff, that's a scope violation against the
  ticket's own Acceptance Criteria ("No functional change to `tools/agent-monitoring/writer.py`").
  Not a pytest test (nothing to assert against without a real diff to inspect), but call out
  explicitly for Verify phase to check.
- **Legacy-path negative assertions**: every rewritten write-path test (new tests #1-#4 above)
  should assert BOTH that the new path exists/has the record AND that the corresponding legacy
  path (`agent-monitoring/tools.jsonl`, `agent-monitoring/tools/tools-*.jsonl`,
  `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`) does NOT get created by a fresh
  write in a clean `tmp_path` — this is the guard against a partial/incomplete cutover (e.g. one of
  the 3 writers gets updated but another is missed, or a leftover reference to the old constant
  survives alongside the new one).
- **`compute_tool_stats` scope guard**: `test_implement_epic_and_create_tickets_records_unaffected_
  no_sidecar` (existing, unmodified) already guards against the glob change accidentally widening
  which workflows get `tool_call_count` computed — it must keep asserting `stats == {}` for
  non-`implement-ticket` run_id prefixes regardless of what the glob finds on disk. Re-run this
  specific test as an explicit anti-drift check, not just incidentally via the full file run.
- **`writer.py` batch-contiguity guard**: `test_batch_write_holds_contiguous_lines_under_
  concurrent_writer` (existing, path-updated per Regression Surface) directly guards against the
  new per-week target-path computation accidentally breaking `write_lines`' one-lock-one-batch
  contiguity property — keep this test's core race-condition mechanics unchanged, only the target
  path constant it reads back from should move.
