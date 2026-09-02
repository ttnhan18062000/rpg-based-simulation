---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-CONSUMERS
phase: open
date: 2026-09-02
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260902-MONITORING-SHARD-CONSUMERS

## Title
Migrate `agent-monitoring/tools.jsonl` readers (`build_index.py`, `generate_retro.py`, `query.py`,
`validate.py`) to glob weekly shard files instead of one hardcoded path

## Status
OPEN

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
- [ ] `python3 tools/agent-monitoring/build_index.py` (`make agent-monitoring-index`) successfully
      builds `monitoring.db`'s `tools` table from all shard files under `agent-monitoring/tools/`,
      with a row count equal to the total across all shards.
- [ ] A test simulates 2+ shard files existing under a temp `agent-monitoring/tools/`-shaped
      directory and confirms `build_index.py` reads and includes records from all of them, not just
      one.
- [ ] `generate_retro.py`'s on-demand build path and its staleness check correctly detect a newly
      appended row in ANY shard (not only the most-recently-created one) as making the index stale.
- [ ] `query.py`'s existing test suite (`tests/tools/test_query.py`) still passes unmodified (or with
      only the confirmed-necessary changes, documented in Implementation Notes).
- [ ] `validate.py`'s drift-report functions produce identical results on the post-migration sharded
      corpus as they did pre-migration, for a fixed historical time window (regression check).
- [ ] `docs/agent-monitoring/README.md`, `schema.md`, `docs/guides/agent_monitoring.md`,
      `docs/ai/system_overview.md` §6 no longer describe `tools.jsonl` as a single physical file.
- [ ] `tools/gate_checks/done_checker_static.py` has zero diff in this ticket (confirms it was
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

## Test Summary

## Files Changed

## Completion Summary
