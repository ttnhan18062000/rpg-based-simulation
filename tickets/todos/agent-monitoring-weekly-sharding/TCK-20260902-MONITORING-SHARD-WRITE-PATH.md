---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-WRITE-PATH
phase: open
date: 2026-09-02
tags: [agent-monitoring, observability, hooks]
---

# TCK-20260902-MONITORING-SHARD-WRITE-PATH

## Title
Cut over `post_tool_hook.py`'s tool-call append to weekly ISO-week-numbered shard files

## Status
OPEN

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
- [ ] A test asserts invoking `post_tool_hook.py` (subprocess, matching
      `tests/tools/test_post_tool_hook.py`'s existing invocation pattern) with a controlled/mocked
      "now" timestamp appends its record to `agent-monitoring/tools/tools-<expected-ISO-week>.jsonl`,
      never to `agent-monitoring/tools.jsonl`.
- [ ] A test asserts two invocations with mocked timestamps in two different ISO weeks write to two
      distinct shard files, each containing exactly its own expected record.
- [ ] Existing `tests/tools/test_post_tool_hook.py` single-writer and concurrent-writer tests (from
      `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`) still pass against the sharded path (paths
      updated as needed; behavior — one well-formed JSON line per invocation, no interleaving under
      concurrency — unchanged).
- [ ] `test_locking_failure_does_not_propagate` (fail-silent contract) still passes unmodified in
      behavior.
- [ ] `.gitattributes` contains a `merge=union` entry covering the new shard glob.
- [ ] `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section describes the
      per-ISO-week file naming and write path.
- [ ] No functional change to `tools/agent-monitoring/writer.py`.

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

## Test Summary

## Files Changed

## Completion Summary
