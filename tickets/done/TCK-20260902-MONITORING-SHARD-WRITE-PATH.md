---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-WRITE-PATH
phase: done
date: 2026-09-02
tags: [agent-monitoring, observability, hooks]
---

# TCK-20260902-MONITORING-SHARD-WRITE-PATH

## Title
Cut over `post_tool_hook.py`'s tool-call append to weekly ISO-week-numbered shard files

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tools/agent-monitoring/post_tool_hook.py` fires synchronously on every tool call across every
concurrently-running Claude Code session and appends one JSON record per line to a hardcoded
`tools_file = Path("agent-monitoring/tools.jsonl")` (line 153), via
`tools/agent-monitoring/writer.py::write_line()`. This single file has grown to 179,096 lines /
64MB (2026-09-02), causing GitHub's ">50MB" push warning and repeated `pack-objects died of signal
9` OOM failures on commits that stage `agent-monitoring/` (mandated on every commit by CLAUDE.md).

This ticket is child 1 of `TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` and must land **first** in
the batch (per `SEQUENCE.md`): it changes where NEW writes go. It does not touch the historical
179k-line file's content (child ticket 2) or any reader (child ticket 3).

Chosen design (already decided, not open here): new writes target
`agent-monitoring/tools/tools-YYYY-Www.jsonl` (ISO week, e.g. `tools-2026-W36.jsonl`), reusing the
exact `%G-W%V` format `tools/agent-monitoring/generate_retro.py::iso_week()` already implements and
the exact convention `agent-monitoring/retro/RETRO-YYYY-Www.md` already uses.

## Scope
- Change `tools/agent-monitoring/post_tool_hook.py`'s hardcoded `tools_file =
  Path("agent-monitoring/tools.jsonl")` (line 153) to compute the current UTC ISO week at write time
  and target `agent-monitoring/tools/tools-YYYY-Www.jsonl` instead (`%G-W%V` format, matching
  `generate_retro.py::iso_week()`).
- Decide, and document the decision, on how the ISO-week computation is shared with
  `generate_retro.py::iso_week()` without importing that ~2000-line reporting module into the hot
  hook path (which fires on every tool call and must stay lightweight/fail-silent): either (a)
  extract a tiny shared helper (e.g. into `writer.py` or a new small module both files import), or
  (b) duplicate the 2-line `strftime("%G-W%V")` computation locally in `post_tool_hook.py`. Either
  is acceptable; pick based on which keeps the hook's import graph lightest.
- Continue routing the append through `tools/agent-monitoring/writer.py::write_line()` unmodified —
  its lock-file path (`_lock_path_for`) is already derived generically from `target_path`, so the
  new sharded path gets correct per-file locking with zero changes to `writer.py`.
- Verify `write_line()`'s existing `target_path.parent.mkdir(parents=True, exist_ok=True)` correctly
  creates the new nested `agent-monitoring/tools/` directory on first write (the old path had no
  subdirectory — confirm this codepath, don't assume).
- Extend `.gitattributes` to add `merge=union` for the new shard glob (e.g.
  `agent-monitoring/tools/*.jsonl merge=union`), keeping the existing
  `agent-monitoring/tools.jsonl merge=union` line in place during this ticket (child ticket 2 removes
  it once the monolithic file is retired from the working tree).
- Update the write-side language in `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl`
  section (including its "Write locking" subsection from `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`)
  to describe per-ISO-week file naming, without removing the accurate per-record schema/field
  documentation (unchanged — only the file-layout framing changes).
- Preserve the hook's fail-silent contract exactly: the outer `try/except Exception: pass` must
  continue to swallow any failure from the new ISO-week computation exactly like every other failure
  mode already handled in this file — a clock/format edge case must never propagate and block a tool
  call.

## Out of Scope
- Splitting/migrating the existing 179,096-line `agent-monitoring/tools.jsonl` into shards — that is
  `TCK-20260902-MONITORING-SHARD-MIGRATION` (child 2).
- Updating `query.py`/`generate_retro.py`/`validate.py`/`build_index.py` to read the new sharded
  files — that is `TCK-20260902-MONITORING-SHARD-CONSUMERS` (child 3). A known, accepted transient
  gap: after this ticket alone lands, new rows written post-cutover are invisible to those 4 readers
  until child ticket 3 lands — acceptable because child tickets 2/3 land immediately after per
  `SEQUENCE.md`, not as a standalone release.
- Removing the historical `agent-monitoring/tools.jsonl` file from the working tree — it stays
  present (frozen, receiving no more appends after this ticket's cutover) until child ticket 2
  migrates its content into shards and retires it.
- Any change to `writer.py`'s locking protocol itself.
- Changing the 13-field per-line record schema written by `post_tool_hook.py`.

## Acceptance Criteria
- [x] A test asserts invoking `post_tool_hook.py` (subprocess, matching
      `tests/tools/test_post_tool_hook.py`'s existing invocation pattern) with a controlled/mocked
      "now" timestamp appends its record to `agent-monitoring/tools/tools-<expected-ISO-week>.jsonl`,
      never to `agent-monitoring/tools.jsonl`.
- [x] A test asserts two invocations with mocked timestamps in two different ISO weeks write to two
      distinct shard files, each containing exactly its own expected record.
- [x] Existing `tests/tools/test_post_tool_hook.py` single-writer and concurrent-writer tests (from
      `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`) still pass against the sharded path (paths
      updated as needed; behavior — one well-formed JSON line per invocation, no interleaving under
      concurrency — unchanged).
- [x] `test_locking_failure_does_not_propagate` (fail-silent contract) still passes — behavior
      unchanged (a lock-acquire failure is still caught and diagnostic-logged, never propagated);
      its diagnostic-path assertion needed a mechanical path update since the diagnostic sidecar is
      now per-shard-directory (see plan.md Deviations).
- [x] `.gitattributes` contains a `merge=union` entry covering the new shard glob.
- [x] `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section describes the
      per-ISO-week file naming and write path.
- [x] No functional change to `tools/agent-monitoring/writer.py`.

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC (parent epic)
- TCK-20260902-MONITORING-SHARD-MIGRATION (child 2 — depends on this ticket landing first)
- TCK-20260902-MONITORING-SHARD-CONSUMERS (child 3)
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK — original write-locking guard added directly to
  `post_tool_hook.py`; superseded by `writer.py::write_line()`, which this ticket continues to use
  unmodified.
- TCK-20260721-MONITORING-WRITER-UNIFICATION — built `writer.py`'s shared `write_line()`/
  `write_lines()`.
- TCK-20260719-LIVE-PHASE-AGENT-LABEL — established the current 13-field `tools.jsonl` record shape
  (including `phase`/`agent`) this ticket's per-line writes must continue to match exactly.

## Related Docs
- `docs/agent-monitoring/schema.md` — `## agent-monitoring/tools.jsonl` section + Write locking
  subsection
- `docs/agent-monitoring/README.md` — Navigation table description of `tools.jsonl`
- `docs/guides/agent_monitoring.md`
- `docs/ai/system_overview.md` §6

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s design rationale
  (lock-file protocol, generic on `target_path`) this ticket relies on unmodified.

## Related Code Areas
- `tools/agent-monitoring/post_tool_hook.py` (primary target, line 153)
- `tools/agent-monitoring/writer.py` (read-only reference; not modified)
- `tools/agent-monitoring/generate_retro.py` (`iso_week()`, line ~123 — reference/reuse target for
  the ISO-week format, not modified by this ticket beyond the doc-language update above)
- `.gitattributes` (line 8)
- `docs/agent-monitoring/schema.md`
- `tests/tools/test_post_tool_hook.py`

## Assumptions / Open Questions
- Assumes UTC is the correct timezone for ISO-week computation (matching `post_tool_hook.py`'s
  existing `datetime.now(timezone.utc)` usage for the `ts` field and `generate_retro.py::iso_week()`'s
  own UTC-based computation) — no timezone ambiguity expected, but worth confirming at
  implementation time since a week boundary crossing near midnight UTC is the one edge case that
  could misfile a record by one week.
- Whether to extract a shared ISO-week helper or duplicate the 2-line computation is left to the
  implementer's judgment (see Scope) — either satisfies DRY concerns without adding hook-path import
  weight.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring/` tooling
  tickets.

## Implementation Notes

Implemented plan.md's 7 steps in order:

- **Step 1** (`tools/agent-monitoring/post_tool_hook.py`): replaced the single `now = ...`
  timestamp computation with `now_dt = datetime.now(timezone.utc)` captured once, deriving both
  `now` (the `ts` field, unchanged format) and `iso_week = now_dt.strftime("%G-W%V")` from that one
  instant — avoids a two-clock-read race at a week boundary. Replaced the hardcoded
  `tools_file = Path("agent-monitoring/tools.jsonl")` with
  `tools_file = Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"`. Kept the hook's own
  pre-emptive `tools_file.parent.mkdir(parents=True, exist_ok=True)` call unchanged — it now does
  real load-bearing work (see investigation.md's trace: prevents `write_line`'s internal
  `_acquire_lock` from hitting `FileNotFoundError` on first write to a new `agent-monitoring/tools/`
  directory). Also updated the module's one-line docstring (line 2) to reference the new path
  pattern — a small accuracy fix adjacent to but not explicitly named in plan.md's Step 1 text.
  Updated `tests/tools/test_post_tool_hook.py`'s shared `_tools_lines()` helper to compute the
  current ISO week and read from the sharded path, matching production exactly.
- **Step 2**: added `_run_hook_with_frozen_now(cwd, payload, frozen_iso)` shim helper (reuses the
  file's existing source-patch-and-run-as-subprocess technique, patching `datetime.datetime.now`
  via a frozen subclass) and three new tests:
  `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`,
  `test_two_different_iso_weeks_write_to_two_distinct_shard_files`,
  `test_iso_week_shard_directory_created_on_first_write`.
- **Step 3**: added `test_iso_week_computation_failure_does_not_propagate`, forcing
  `datetime.datetime.now` to raise inside a shimmed copy of the hook, asserting `returncode == 0`,
  empty `stderr`, and no shard file/directory created.
- **Step 4**: added `agent-monitoring/tools/*.jsonl merge=union` to `.gitattributes`, directly below
  the pre-existing (unremoved) `agent-monitoring/tools.jsonl merge=union` line.
- **Step 5**: extended `tests/integrity/test_merge_union_gitattributes.py` — added
  `"agent-monitoring/tools/tools-2026-W36.jsonl"` to the existing parametrized
  `test_concurrent_branch_appends_merge_without_conflict_markers` test's `tracked_filename` list,
  and added a new `test_gitattributes_line_present_for_shard_glob` sanity test asserting both the
  new shard-glob line and the old legacy line are present in the real `.gitattributes`.
- **Step 6**: updated `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section
  — added a paragraph describing the new per-ISO-week shard file naming/write path immediately
  after the section's opening sentence (schema/field table left untouched), and rewrote the
  "Write locking" subsection's stale `fcntl.flock`-based description (pre-dating
  `TCK-20260721-MONITORING-WRITER-UNIFICATION`) to accurately describe the current
  `writer.py::write_line()` O_CREAT|O_EXCL lock-file protocol, including the now-per-shard-file
  locking behavior.
- **Step 7**: ran all three scoped pytest commands (all green — see Test Summary) and
  `make knowledge-index-update` (completed: 89 files changed/new, 10389 chunks total).

**Deviations from plan.md's literal text** (both discovered via real `pytest` failures during
Step 7's first run, fixed rather than routed around, both documented in full in plan.md's new
"Deviations" section at the bottom of that file):

1. `test_locking_failure_does_not_propagate`'s diagnostic-path assertion was hardcoded to
   `tmp_path / "agent-monitoring" / ".writer_health.jsonl"`, but `writer.py::_diagnostic_path_for`
   derives that path from `target_path.parent`, which after Step 1's cutover is
   `agent-monitoring/tools/` (the shard directory) — exactly the "diagnostic sidecar split"
   investigation.md's Risks section already flagged as an expected side effect. Fixed by updating
   the assertion path; the test's fault-injection logic and what it verifies are unchanged.
2. `test_iso_week_computation_failure_does_not_propagate`'s shim, as literally specified in
   plan.md's Step 3, raised `ModuleNotFoundError` for `writer` because `from writer import
   write_line` (hook line 10) executes at module-import time — before the frozen/raising
   `datetime.now()` override even matters — and the shim runs from `tmp_path`, not the real
   `tools/agent-monitoring/` directory. Fixed by adding the same
   `sys.path.insert(0, str(_MONITORING_TOOLS_DIR))` prefix already used by
   `_run_hook_with_frozen_now` and `test_locking_failure_does_not_propagate`.

Neither deviation touches `writer.py`, the 13-field record shape, or production behavior — both are
test-setup/assertion corrections required to make the tests actually exercise what they claim to.

## Test Summary

All four required commands run with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`:

- `pytest tests/tools/test_post_tool_hook.py -v` → **18 passed** (14 pre-existing + 4 new:
  `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`,
  `test_two_different_iso_weeks_write_to_two_distinct_shard_files`,
  `test_iso_week_shard_directory_created_on_first_write`,
  `test_iso_week_computation_failure_does_not_propagate`)
- `pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py tests/tools/test_monitoring_writer_lockfile_candidate.py -v` → **16 passed**, 0 changes to `writer.py`
- `pytest tests/integrity/test_merge_union_gitattributes.py -v` → **7 passed** (5 parametrized
  concurrent-branch-append cases including the new nested-path case, plus the original 4-line
  sanity test, plus the new `test_gitattributes_line_present_for_shard_glob`)
- `make knowledge-index-update` → completed successfully (89 files changed/new re-embedded, 3156
  unchanged from cache, 10389 chunks total, 0 errors)

`git diff -- tools/agent-monitoring/writer.py` confirmed empty (0 lines) — zero functional change,
as AC-mandated.

## Files Changed

- `tools/agent-monitoring/post_tool_hook.py` — write-path cutover (Step 1)
- `tests/tools/test_post_tool_hook.py` — `_tools_lines()` helper update, new
  `_run_hook_with_frozen_now` shim helper, 4 new tests, 2 deviation fixes to
  `test_locking_failure_does_not_propagate`'s assertion path and the new
  `test_iso_week_computation_failure_does_not_propagate`'s shim (Steps 1-3)
- `.gitattributes` — new shard-glob `merge=union` line (Step 4)
- `tests/integrity/test_merge_union_gitattributes.py` — new parametrize case, new sanity test
  (Step 5)
- `docs/agent-monitoring/schema.md` — file-layout paragraph + rewritten "Write locking" subsection
  (Step 6)
- `staging_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/plan.md` — added "Deviations" section
  documenting the two test-code corrections found during Step 7
- `tickets/inprogress/TCK-20260902-MONITORING-SHARD-WRITE-PATH.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Acceptance Criteria checkboxes, Completion Summary)

Not modified (confirmed): `tools/agent-monitoring/writer.py` (0-line diff),
`tools/agent-monitoring/generate_retro.py`, `query.py`, `validate.py`, `build_index.py`,
`docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`,
historical `agent-monitoring/tools.jsonl` content (no code of this ticket appends to it going
forward; it kept receiving rows from concurrent sessions' tool calls made before this ticket's
`post_tool_hook.py` edit took effect in this live shared worktree — collateral of a hot-path change
in an actively-used repo, not a regression).

## Completion Summary

Cut over `post_tool_hook.py`'s tool-call append target from the single hardcoded
`agent-monitoring/tools.jsonl` to a per-UTC-ISO-week shard file,
`agent-monitoring/tools/tools-YYYY-Www.jsonl`, computed from one captured `datetime.now(timezone.utc)`
instant shared with the existing `ts` field, with the `%G-W%V` format duplicated locally (not
imported from `generate_retro.py`) to keep the hook's import graph stdlib-only. `writer.py` is
untouched — its lock-file and mkdir logic were already fully generic on `target_path`, so locking
and directory creation work correctly for the new nested path with zero code changes there. Added
4 new tests (2 shard-targeting, 1 directory-creation, 1 fail-silent guard) plus a `.gitattributes`
shard-glob entry and updated `docs/agent-monitoring/schema.md`'s write-path/locking description
(also correcting pre-existing stale `fcntl` prose in the same edit). All 18 tests in
`test_post_tool_hook.py`, all 16 writer tests, and all 7 `.gitattributes` integrity tests pass; the
knowledge index was rebuilt for the doc change. Two minor test-code corrections beyond plan.md's
literal text were required and are documented as Deviations in plan.md and above — neither touches
production behavior.
