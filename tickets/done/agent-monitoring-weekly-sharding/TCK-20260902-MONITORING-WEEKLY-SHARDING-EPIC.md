---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC
phase: done
date: 2026-09-02
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC

## Title
Restructure `agent-monitoring/tools.jsonl`'s unbounded growth into weekly, ISO-week-numbered shard files

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`agent-monitoring/tools.jsonl` (appended synchronously by `tools/agent-monitoring/post_tool_hook.py:153`
on every single tool call across every concurrent session, via a hardcoded
`Path("agent-monitoring/tools.jsonl")`) has grown from ~68k lines (2026-07-28, per the archived
design doc `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md`) to
**179,096 lines / 64MB** as of 2026-09-02 — roughly 22k lines/week, ~375 bytes/line. `runs.jsonl`
(1,373 lines / 388K) and `events.jsonl` (8,879 lines / 3.2M) are growing far more slowly and are
explicitly **not** part of this epic's scope.

Concrete, observed consequences this session: GitHub prints a "file >50MB" warning on every push
touching `tools.jsonl`; `git commit`/`push` in this shared repo have repeatedly hit
`error: pack-objects died of signal 9` (an OOM-killed background auto-repack), very likely from
delta-compressing a 64MB blob staged on nearly every commit repo-wide (CLAUDE.md mandates staging
`agent-monitoring/` on every commit). The shared `.git/` directory is 4.4GB.

The gitignored, read-only SQLite derived index (`tools/agent-monitoring/build_index.py` →
`agent-monitoring-index/monitoring.db`, `make agent-monitoring-index`, shipped by the
`agent-monitoring-derived-index` batch — see Related Tickets) does NOT fix this: it is a read-side
convenience layer, rebuilt from the raw JSONL files, and does not bound the write-side file at all.
Its own archived design doc explicitly deferred this exact growth question in 2026-07 ("NOT
reopened... no evidence surfaced") — that evidence has now surfaced.

**Chosen design (decided this session, not open for re-derivation):** weekly, ISO-week-numbered
shard files. New writes go to `agent-monitoring/tools/tools-YYYY-Www.jsonl` (e.g.
`tools-2026-W36.jsonl`) instead of one ever-growing file. Each shard freezes once its week ends, so
its git delta-compression cost stabilizes instead of every historical commit re-diffing an
ever-larger blob. Weekly beats monthly because at current growth (~22k lines/week, ~375 bytes/line)
a monthly shard would already be ~35-40MB — uncomfortably close to the 50MB threshold this epic
exists to get away from, especially with agent activity trending up (more concurrent
worktrees/sessions), not down. Weekly shards land at ~8-9MB, giving real safety margin. This design
reuses the exact convention `agent-monitoring/retro/` already uses for its own weekly reports
(`RETRO-2026-W35.md`, `RETRO-2026-W36.md`, confirmed via `ls` this session) and the exact ISO-week
format (`%G-W%V`) already implemented by `tools/agent-monitoring/generate_retro.py::iso_week()` —
not a new convention invented for this epic.

## Scope
- Scope-only epic: create and track the 3 child tickets that implement weekly ISO-week sharding of
  `agent-monitoring/tools.jsonl`'s write path, historical migration, and consumer read paths. No
  direct implementation in this ticket itself, per Tier Routing's epic definition ("tracks child
  tickets; no direct implementation").
- Record the design and rationale above as already-decided.
- Sequence: write-path rotation lands first, then one-time migration/backfill of the existing
  179,096-line file, then consumer migration of the readers. See this batch folder's `SEQUENCE.md`.
- `events.jsonl`/`runs.jsonl` are explicitly out of scope for all 3 child tickets.

## Out of Scope
- Sharding `runs.jsonl` or `events.jsonl` — not this epic; no evidence of need (1,373 / 8,879 lines
  respectively vs. 179,096 for `tools.jsonl`).
- Any change to `tools/agent-monitoring/writer.py`'s `write_line()`/`write_lines()` locking
  protocol — its `O_CREAT|O_EXCL` lock-file path is already derived generically from `target_path`
  (`_lock_path_for`), so a new sharded target path gets correct per-file locking with zero code
  change there.
- Building any new tooling to auto-prune/archive/delete old shard files beyond git's own history —
  a frozen shard just stops growing; no retention/deletion policy is in scope.
- Redesigning the 13-field JSONL record schema itself — this epic changes physical file layout
  only, never the per-line record shape.
- Backfilling or repairing any pre-existing malformed/off-schema historical lines beyond what the
  migration child ticket's zero-data-loss check requires (every existing line must land somewhere,
  unmodified in content — content repair is not in scope for any child ticket).

## Acceptance Criteria
- [x] All 3 child tickets (`TCK-20260902-MONITORING-SHARD-WRITE-PATH`,
      `TCK-20260902-MONITORING-SHARD-MIGRATION`, `TCK-20260902-MONITORING-SHARD-CONSUMERS`) are DONE.
- [x] `post_tool_hook.py` writes new tool-call records to
      `agent-monitoring/tools/tools-YYYY-Www.jsonl` (current ISO week), never to
      `agent-monitoring/tools.jsonl`.
- [x] The historical 179,243-line (real count at migration run time, not the 179,096 stated when
      this epic was scoped) `agent-monitoring/tools.jsonl` has been split into weekly shards with a
      verified zero-data-loss check (`179243 + 190 live = 179433`, exact reconciliation), and the
      monolithic file no longer exists in the working tree (full content recoverable via
      `git log --follow`, confirmed 70 commits).
- [x] `query.py`, `generate_retro.py`, `validate.py`, `build_index.py` all read from the full set of
      sharded files, not one hardcoded path. (`query.py`/`validate.py` confirmed to need zero
      functional change — both are pure SQLite-index consumers, unaffected by the file-layout
      change; documented, not silently assumed.)
- [x] `.gitattributes` covers the new shard directory with `merge=union`, and no longer references
      the retired single-file path.
- [x] `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
      `docs/ai/system_overview.md` §6 describe the sharded shape, not "3 JSONL files."
      (`docs/guides/agent_monitoring.md` confirmed to need no change — its 2 references are
      logical/conceptual, not physical-file claims.)

## Related Tickets
- TCK-20260902-MONITORING-SHARD-WRITE-PATH (child 1)
- TCK-20260902-MONITORING-SHARD-MIGRATION (child 2)
- TCK-20260902-MONITORING-SHARD-CONSUMERS (child 3)
- TCK-20260713-MONITORING-SQLITE-INDEX and its sibling batch
  (`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`, `TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE`,
  `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`) — built the gitignored, full-rebuild-only SQLite
  index this epic's consumer-migration child ticket must keep working against sharded source files;
  confirmed this session that it does NOT itself fix the write-side growth problem (read-side only).
- TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS — fixed `generate_retro.py`'s index-staleness
  mtime check to compare against source JSONL mtimes; that check must be extended by child ticket 3
  to compare against the newest shard's mtime, not one file's.
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK — added the original write-locking guard directly
  to `post_tool_hook.py`; superseded in place by `writer.py`'s shared `write_line()` (below), which
  child ticket 1 continues to use unmodified for the new sharded path.
- TCK-20260721-MONITORING-WRITER-UNIFICATION — built the shared `writer.py::write_line()`/
  `write_lines()` module (`O_CREAT|O_EXCL` lock-file protocol, generic on `target_path`) that
  `post_tool_hook.py` already routes through.

## Related Docs
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` — archived design
  doc; its Open Questions section explicitly deferred this exact growth question in 2026-07 ("NOT
  reopened... no evidence surfaced"); that evidence has now surfaced.
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6 — all currently describe "3
  append-only JSONL files"; updated by child tickets 1 and 3.

## Related Stored Artifacts
None yet — epic ticket, no staging artifacts required (scope-only, per Tier Routing). Each standard-
tier child ticket requires its own `staging_artifacts/{ticket_id}/` per the Before Work rule.

## Related Code Areas
- `agent-monitoring/tools.jsonl` (179,096 lines / 64MB as of 2026-09-02; ~22k lines/week, ~375
  bytes/line)
- `agent-monitoring/retro/RETRO-2026-Www.md` — the existing ISO-week sharding convention this epic
  reuses
- `tools/agent-monitoring/post_tool_hook.py:153` — sole writer of `tools.jsonl`
- `tools/agent-monitoring/writer.py` — shared locked-append writer, generic on target path
- `tools/agent-monitoring/query.py`, `generate_retro.py`, `validate.py`, `build_index.py` — readers
- `tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded` — confirmed during
  this scoping session (grep across the file) to read only `runs.jsonl`/`events.jsonl` (lines
  691-692), NOT `tools.jsonl` at all — no change needed here; see child ticket 3's Assumptions for
  the correction to the original request's premise.
- `.gitattributes` line 8 (`agent-monitoring/tools.jsonl merge=union`)
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`

## Assumptions / Open Questions
- Design (weekly, ISO-week shards at `agent-monitoring/tools/tools-YYYY-Www.jsonl`, reusing
  `generate_retro.py::iso_week()`'s `%G-W%V` format) was decided with the requester this session and
  is recorded as already-decided, not reopened for implementer re-derivation.
- `events.jsonl`/`runs.jsonl` sharding is explicitly out of scope; if their growth rate changes
  materially in the future, that would be separate future scope, not silently folded into this epic.
- Correction found during this scoping session: `done_checker_static.py::check_monitoring_write_recorded`
  does NOT reference `tools.jsonl` in any way (only `runs.jsonl`/`events.jsonl`) — the original
  request's "confirm whether it hardcodes the old path" is answered NO; this file needs no change
  anywhere in this epic.
- `layer: observability` matches every other `agent-monitoring/` ticket in this repo's history
  (TCK-20260713-MONITORING-SQLITE-INDEX, TCK-20260716-..., TCK-20260721-..., TCK-20260811-...),
  confirmed via `python3 tools/layer_registry.py list`.

## Implementation Notes
All 3 child tickets implemented sequentially on branch `worktree-monitoring-tools-weekly-sharding`,
each through the full standard-tier pipeline (Investigate → Plan → Implement → Test →
Architecture-Verify → Verify → Finalize), each independently verified by architecture-reviewer and
done-checker before proceeding to the next.

Child 1 (write-path) surfaced no scope deviations. Child 2 (migration) discovered mid-implementation
that 2 additional real-corpus tests in `test_generate_retro.py` shared the identical root cause as
the 5 originally-planned `xfail`-marked tests; the orchestrating session extended the same treatment,
correcting the interim-gap list from 5 to 7 tests, all tracked for child 3 to resolve. Child 3
(consumers) discovered during its own Plan phase a live, previously-unknown, non-xfailed test failure
(`manifest.py::capture_lines()`, used by 2 real downstream consumers) sharing the same root defect as
the file's other broken function, and folded its fix in as the same fix applied to the file's second
function — not scope creep. All 7 originally-accepted `xfail` markers plus this 8th
previously-red test were confirmed genuinely `PASSED` (not `xfail`/`xpass`/`error`) before child 3's
own Finalize, satisfying the hard release gate child 2's plan.md staked on child 3 landing.

## Test Summary
Full regression sweep across all 3 children's combined changes (final state, child 3's Verify):
**257 passed, 0 failed, 0 xfail, 0 xpass, 0 error.** All 8 previously-broken/xfailed real-corpus
tests independently confirmed genuine `PASSED` by 2 separate gates (architecture-reviewer,
done-checker) beyond the implementer's own report.

## Files Changed
See each child ticket's own `## Files Changed` section
(`tickets/done/TCK-20260902-MONITORING-SHARD-WRITE-PATH.md`,
`tickets/done/TCK-20260902-MONITORING-SHARD-MIGRATION.md`,
`tickets/done/TCK-20260902-MONITORING-SHARD-CONSUMERS.md`) for the complete, itemized list. Summary:
`post_tool_hook.py` (write path), `migrate_tools_shards.py` (new, one-time migration script),
`validate.py`/`build_index.py`/`generate_retro.py`/`manifest.py` (dir-aware readers), `.gitattributes`,
4 doc files, 1 parity ledger entry (`INFRA-291`, via the sanctioned writer), and the historical
`agent-monitoring/tools.jsonl` file itself (removed, 179,243 lines relocated into 14 shard files
under `agent-monitoring/tools/`).

## Completion Summary
`agent-monitoring/tools.jsonl`'s unbounded growth (179,243 lines / 64MB by the time this epic
landed, causing repeated GitHub >50MB push warnings and `pack-objects` OOM failures observed live
across this very session) is resolved via weekly, ISO-week-numbered shard files
(`agent-monitoring/tools/tools-YYYY-Www.jsonl`), reusing the exact naming convention this repo's own
`agent-monitoring/retro/` reports already established. The write path (child 1), a one-time
zero-data-loss historical migration that retired the monolithic file (child 2), and every real
consumer's read path (child 3) all landed and were independently verified. No data was lost — full
history remains recoverable via `git log --follow`. `events.jsonl`/`runs.jsonl` were confirmed out
of scope, growing far more slowly with no evidence of needing the same treatment. One deferred
follow-up flagged, not silently dropped: root-level `agent-monitoring/README.md` (distinct from
`docs/agent-monitoring/README.md`) has the same stale single-file framing and is a good small
follow-up hotfix ticket candidate.
