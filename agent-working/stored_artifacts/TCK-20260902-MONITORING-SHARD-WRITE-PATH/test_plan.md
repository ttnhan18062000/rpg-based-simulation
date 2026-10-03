---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-WRITE-PATH
artifact_type: test_plan
tags: [agent-monitoring, observability, hooks]
---

# Test Plan — TCK-20260902-MONITORING-SHARD-WRITE-PATH

## Regression Surface

All of `tests/tools/test_post_tool_hook.py` (14 tests) must keep passing, with paths updated from
`agent-monitoring/tools.jsonl` to the new sharded path where the test reads back written records.
Grouped:

- **Unit/subprocess — record shape and single-writer correctness:**
  `test_single_writer_produces_one_well_formed_line`,
  `test_phase_and_agent_included_when_sidecar_present`,
  `test_execution_identity_fields_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`
- **Integration — concurrency:** `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`
  (10 threads x 15 iterations = 150 hook invocations against one shard file; exercises
  `writer.py`'s real lock-file protocol under real contention)
- **Integration — sidecar attribution (unaffected by this ticket, must not regress):**
  `test_scoped_sidecar_preferred_over_stale_unscoped_sidecar`,
  `test_two_concurrent_sessions_each_attributed_correctly`,
  `test_foreign_scoped_sidecar_not_read_by_different_session`,
  `test_second_call_in_ad_hoc_session_reads_own_sentinel_not_unscoped_file`,
  `test_real_writesidecar_overwrites_earlier_ad_hoc_sentinel`,
  `test_ad_hoc_sentinel_pruned_identically_to_any_scoped_file`,
  `test_stale_scoped_sidecar_pruned`, `test_fresh_scoped_sidecar_not_pruned`
- **Fail-silent contract:** `test_locking_failure_does_not_propagate`

Also in scope as regression surface (writer.py is unmodified but shares test infrastructure and
should be re-run to confirm no incidental breakage from the path change propagates):
- `tests/tools/test_monitoring_writer.py`
- `tests/tools/test_monitoring_writer_single_source.py`
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`

**`tests/integrity/test_merge_union_gitattributes.py`** (found via `grep -rl gitattributes
tests/` — corrects an earlier assumption that no test file owns `.gitattributes` coverage; one
already does and must be extended, not duplicated in a new module). Its
`test_gitattributes_lines_present_for_all_four_union_merge_paths` sanity guard currently asserts
exactly 4 hardcoded `merge=union` lines are present in the real `.gitattributes`
(`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, `agent-monitoring/tools.jsonl`,
`tickets/working_log.csv`) and must keep passing unmodified — this ticket's Scope explicitly keeps
the existing `agent-monitoring/tools.jsonl merge=union` line in place, so this assertion should not
need to change, only gain a sibling assertion for the new glob (see New Tests Required).

Not regression surface for this ticket (explicitly out of scope — readers untouched):
`tests/tools/test_generate_retro.py`, `tests/tools/test_build_index.py`, any `query.py`/
`validate.py` tests. These may be worth a quick sanity run post-change only to confirm nothing
crashes on an empty/missing new shard directory, but no behavior change is expected or required
there by this ticket.

## New Tests Required

All new tests live in `tests/tools/test_post_tool_hook.py`, following the exact subprocess
invocation pattern every existing test in that file already uses (`_run_hook(cwd, payload)` /
`subprocess.run([sys.executable, str(_HOOK_PATH)], input=..., cwd=..., capture_output=True,
text=True, timeout=10)`) — the hook cannot be imported and called as a function (module docstring:
reading `sys.stdin` executes at import time), so every test must continue driving it as a
subprocess with `cwd` pointed at `tmp_path`.

**Controlling "now"**: no `freezegun`-style time-mocking utility exists anywhere in this repo
(`requirements.txt`/`requirements-knowledge.txt` do not list `freezegun`; no test in the whole
suite imports it). The established in-file precedent for injecting test-only control into this
specific top-level, subprocess-invoked script is `test_locking_failure_does_not_propagate`'s
"shim" technique: read the hook's own source (`_HOOK_PATH.read_text()`), prepend a small patch
block, write the combined source to a new file in `tmp_path`, and run *that* file as the
subprocess instead of the real hook. New tests must reuse this exact technique to control "now",
patching the `datetime` module's `datetime` class (assigning a frozen subclass onto
`datetime.datetime` before the hook source's own `from datetime import datetime, timezone`
executes) rather than inventing a new mocking mechanism (e.g. environment variables, no such seam
exists in the hook today, and adding one would itself be a scope-creep code change beyond what
this ticket's Scope authorizes).

- **`test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`**
  - Category: integration (subprocess + real filesystem)
  - Verifies: with "now" frozen to `2026-08-31T12:00:00Z` (ISO week `2026-W36`, confirmed via
    `datetime.fromisoformat("2026-08-31T12:00:00+00:00").strftime("%G-W%V")`), invoking the hook
    once appends its record to `agent-monitoring/tools/tools-2026-W36.jsonl`, and that
    `agent-monitoring/tools.jsonl` (the legacy path) is **not** created at all — asserts
    `not (tmp_path / "agent-monitoring" / "tools.jsonl").exists()` alongside asserting the new
    shard file's single line parses to the expected 13-field record (reusing this file's existing
    `_RECORD_FIELDS` set).
  - Lives in: `tests/tools/test_post_tool_hook.py`

- **`test_two_different_iso_weeks_write_to_two_distinct_shard_files`**
  - Category: integration (subprocess + real filesystem, two invocations with two frozen times)
  - Verifies: one hook invocation frozen to `2026-08-31T12:00:00Z` (`2026-W36`) and a second
    frozen to `2026-09-07T12:00:00Z` (`2026-W37`, confirmed via the same `strftime` check) each
    produce their own shard file (`tools-2026-W36.jsonl`, `tools-2026-W37.jsonl`), each containing
    exactly one line, and each line's own record matches only that invocation's `_payload()`
    (distinguish via `input_summary`/`command`, matching the existing concurrency test's pattern of
    keying assertions off distinct command strings). Also asserts neither shard file's content
    leaks into the other (no interleaving across files, which is trivially true given they're
    different files/locks, but worth asserting the record counts explicitly: exactly 1 line each,
    not 2 in one and 0 in the other from a path-computation bug).
  - Lives in: `tests/tools/test_post_tool_hook.py`

- **`test_iso_week_shard_directory_created_on_first_write`**
  - Category: integration (subprocess + real filesystem)
  - Verifies: on a `tmp_path` with no pre-existing `agent-monitoring/` directory at all (the
    default state for every test in this file already, since each uses a fresh `tmp_path`), a
    single hook invocation correctly creates `agent-monitoring/tools/` (not just
    `agent-monitoring/`) and the shard file inside it — directly exercises the
    `parent.mkdir(parents=True, exist_ok=True)` codepath (both the hook's own call and
    `write_line`'s internal one) traced in investigation.md, guarding against the
    `FileNotFoundError`-on-first-lock-acquire edge case identified there in case a future edit
    removes the hook's own pre-emptive mkdir call believing it "redundant."
  - Lives in: `tests/tools/test_post_tool_hook.py`

- **`test_iso_week_computation_failure_does_not_propagate`**
  - Category: unit/integration (subprocess, shimmed) — architecture/fail-silent guard
  - Verifies: mirrors `test_locking_failure_does_not_propagate`'s existing shim pattern, but forces
    a failure in the ISO-week computation itself (e.g. monkeypatch `datetime.datetime.now` in the
    shim to raise, or monkeypatch `strftime` to raise on the `"%G-W%V"` format) rather than in
    `os.open` for `.lock` paths. Asserts `result.returncode == 0`, `result.stderr == ""`, and — key
    difference from the existing locking-failure test — that **no record is written at all** to
    any shard file and no tool call is blocked, since a clock/format failure means the whole `try`
    block's record-building fails before `write_line` is ever reached, unlike a lock-acquire
    failure (which still gets as far as calling `write_line`, which itself fails gracefully and
    diagnostics). This test specifically targets the ticket's Scope requirement that the new
    ISO-week computation sits inside the *same* outer fail-silent boundary as everything else in
    the hook — a regression here (e.g. the computation accidentally placed outside the `try:`)
    would surface as a nonzero `returncode` or non-empty `stderr`, which today's suite has no test
    that would catch, since no existing test exercises a failure mode upstream of `write_line`.
  - Lives in: `tests/tools/test_post_tool_hook.py`

- **`test_gitattributes_lines_present_for_all_four_union_merge_paths` extended, or a new sibling
  sanity assertion added alongside it** (e.g. `test_gitattributes_line_present_for_shard_glob`)
  - Category: architecture guard (no subprocess — direct file read of the real repo's
    `.gitattributes`, matching this existing test's own pattern exactly:
    `(Path(__file__).parent.parent.parent / ".gitattributes").read_text()`)
  - Verifies: the literal line `agent-monitoring/tools/*.jsonl merge=union` (or whatever exact
    glob Implement chooses, per the ticket's own example) is present in the real repo's
    `.gitattributes`, and that the pre-existing `agent-monitoring/tools.jsonl merge=union` line is
    still present unchanged (this ticket keeps it; child ticket 2 removes it) — reuse the existing
    sanity test's simple string-membership style rather than inventing a new assertion style.
  - Category (second, optional but recommended): extend the parametrized
    `test_concurrent_branch_appends_merge_without_conflict_markers` test's `tracked_filename`
    parametrize list with one nested-path case, e.g.
    `"agent-monitoring/tools/tools-2026-W36.jsonl"`, to prove the real git-level union-merge
    behavior (not just the static `.gitattributes` line) also resolves correctly for a shard path
    one directory deeper than the existing four flat paths it already covers — the existing
    `_init_repo_with_union_attribute` helper already does `target.parent.mkdir(parents=True,
    exist_ok=True)`, so it already supports a nested path with no helper changes needed.
  - Lives in: `tests/integrity/test_merge_union_gitattributes.py` (existing file — extend, do not
    create a new module).

## Scoped Pytest Commands

```
pytest tests/tools/test_post_tool_hook.py -v
pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py tests/tools/test_monitoring_writer_lockfile_candidate.py -v
```

The extended/added `.gitattributes` guard tests:
```
pytest tests/integrity/test_merge_union_gitattributes.py -v
```

Never `pytest tests/` — scoped to the `tools/agent-monitoring/` write-path domain per CLAUDE.md's
Testing Rule.

## Anti-Drift Test Guards

- **`test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`'s explicit
  `not (tmp_path / "agent-monitoring" / "tools.jsonl").exists()` assertion** is itself the primary
  anti-drift guard for this ticket's core requirement — it would fail immediately if a future edit
  accidentally reverted the write target back to the legacy hardcoded path, or wrote to *both*
  paths (e.g. a botched migration-adjacent change that duplicates writes).
- **Existing `_RECORD_FIELDS` set reuse** (all new tests assert `set(record.keys()) ==
  _RECORD_FIELDS`, the same set every existing test in the file already asserts against) — guards
  against scope creep into the 13-field record shape, which this ticket must not touch.
- **`test_iso_week_computation_failure_does_not_propagate`** guards specifically against the
  ISO-week computation being accidentally placed outside the hook's single outer `try/except`
  block — the one architecturally load-bearing constraint this ticket's Scope calls out by name
  ("the outer `try/except Exception: pass` must continue to swallow any failure from the new
  ISO-week computation").
- **Re-running `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` unmodified
  (only its file-path assertions inside `_tools_lines()` need updating to read from the new shard
  path)** guards against a locking regression introduced incidentally by the path change — since
  `_lock_path_for` is generic on `target_path`, this test's 150-invocation concurrency stress
  against a single shard file is the strongest existing proof that per-shard locking still works
  correctly post-cutover.
- **The extended `tests/integrity/test_merge_union_gitattributes.py` assertion that the old
  `agent-monitoring/tools.jsonl merge=union` line is still present** guards against this ticket
  accidentally doing child ticket 2's job (removing the old file/its `.gitattributes` entry) ahead
  of schedule — an explicit Out of Scope item.
- **No new test asserts anything about `query.py`/`generate_retro.py`/`validate.py`/
  `build_index.py` behavior** — deliberately, since those readers are untouched (child ticket 3);
  adding assertions about their behavior here would falsely imply this ticket changes read-path
  visibility of the new shards, which it explicitly does not.
