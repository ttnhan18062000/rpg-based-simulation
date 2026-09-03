---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-CORE
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260903-MONITORING-DATA-CONSUMERS-CORE

## Title
Migrate `tools/agent-monitoring/` core readers (`build_index.py`, `generate_retro.py`,
`manifest.py`, `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
`done_ticket_monitoring_coverage.py`, `validate.py`, `query.py`) to the unified per-week
`agent-monitoring/data/` layout, fixing `weight_sensitivity_check.py`'s live `TOOLS_FILE`
ground-truth bug

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 3 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. Confirmed hardcoded single-path constants
via direct grep this session (line numbers as of this scoping session, reconfirm at implementation):

- `generate_retro.py`: `RUNS_FILE` (line 53), `EVENTS_FILE` (line 54) — still single-file.
  `DEFAULT_TOOLS_FILE` (line 57) already dir-aware for the prior epic's `tools/` shard directory only
  — must be repointed to the new `agent-monitoring/data/` layout, generalized across all 3 sources.
- `build_index.py`: `DEFAULT_RUNS_FILE` (line 42), `DEFAULT_EVENTS_FILE` (line 43) — still
  single-file. `DEFAULT_TOOLS_FILE` (line 44) — same repoint/generalize as above.
- `seq_offset.py`: `EVENTS_FILE` (line 27) — still single-file.
- `retro_nudge_hook.py`: `RUNS_FILE` (line 18) — still single-file.
- `weight_sensitivity_check.py`: `TOOLS_FILE` (line 29) — **confirmed to hardcode the literal,
  now-permanently-empty legacy path `agent-monitoring/tools.jsonl`, the same live bug class as
  `record_events.py`'s (fixed in child 1) — this file's tools-source read has been silently reading
  nothing since the prior epic's `git rm`.** `EVENTS_FILE` (line 30) — still single-file.
- `done_ticket_monitoring_coverage.py`: reads `runs.jsonl` directly per its own doc comments (lines
  62, 70, 94) — exact literal path constant to confirm at implementation time (not fully resolved by
  this session's grep).
- `validate.py`/`query.py`: the prior epic confirmed these are largely SQLite-index consumers with no
  direct `tools.jsonl` path constant (only `DEFAULT_DB_PATH`); `validate.py` additionally has a
  dir-aware `load_jsonl()` the prior epic's child 3 added for the `tools` source specifically. Neither
  file's `runs.jsonl`/`events.jsonl` surface has ever been checked, since the prior epic was tools-
  only — must be reconfirmed here, not assumed unaffected.

## Scope
- Generalize each hardcoded single-path constant (`RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_RUNS_FILE`/
  `DEFAULT_EVENTS_FILE` etc.) in `build_index.py`, `generate_retro.py`, `seq_offset.py`,
  `retro_nudge_hook.py`, `weight_sensitivity_check.py`, `done_ticket_monitoring_coverage.py` to glob
  across `agent-monitoring/data/*/<source>.jsonl` (all week folders, sorted by ISO week,
  concatenated), reusing/extending the dual-mode directory-glob-or-literal-file `load_jsonl()`
  pattern `generate_retro.py`/`validate.py` already have for the `tools` source, generalized to all
  3 sources for every consumer that reads more than one.
- Extend `generate_retro.py`'s `_index_is_stale()` / `_source_mtime()` helper (already built by the
  prior epic for the `tools` source) so `runs` and `events` staleness also compares against the
  newest week folder's mtime for that source, not one file's.
- Extend `build_index.py`'s table-build routine so `monitoring.db`'s `runs`/`events` tables are built
  from the full multi-week glob, same as `tools` already is.
- **Fix `weight_sensitivity_check.py`'s `TOOLS_FILE` bug** as an explicit, dedicated line item — its
  tools-source read must glob `agent-monitoring/data/*/tools.jsonl`, matching child 1's fix to the
  same bug class in `record_events.py`.
- Confirm and fix (or document as a confirmed no-op) `validate.py`'s and `query.py`'s
  `runs.jsonl`/`events.jsonl` surface.
- Confirm `done_ticket_monitoring_coverage.py`'s exact `runs.jsonl` reference and generalize it the
  same way as the other single-source consumers.

## Out of Scope
- `tools/gate_checks/done_checker_static.py` and `src/api/agent_ops_dashboard/ingest.py` — those are
  child 4, kept separate for independent, more careful review of production-API-facing/gate-blocking
  code.
- `tools/agent_replay_codex/monitoring_shards.py` and the codex subsystem — child 5.
- Referential-integrity verification — child 6.
- Any change to `build_index.py`'s table schema, or to `_resolve_status()`/`_is_legacy_event()`/any
  other centralized normalization logic — only the file-resolution layer changes.
- The write path — already done by child 1 (hard prerequisite via child 2).

## Acceptance Criteria
- [ ] `python3 tools/agent-monitoring/build_index.py` (`make agent-monitoring-index`) builds
      `monitoring.db`'s `runs`/`events`/`tools` tables from all week folders under
      `agent-monitoring/data/`, with row counts equal to the totals across all weeks, for all 3
      tables.
- [ ] A test simulates 2+ week folders under a temp `agent-monitoring/data/`-shaped directory and
      confirms `build_index.py` reads and includes records from all of them, for all 3 sources.
- [ ] `generate_retro.py`'s on-demand build path and staleness check correctly detect a newly
      appended row in ANY week folder's ANY of the 3 files as making the index stale.
- [ ] **Regression test proving `weight_sensitivity_check.py`'s bug is fixed**: a test with real
      multi-week seeded `tools`/`events` data asserts the script's tools-source-derived weight
      computation is nonzero/correct, not silently empty.
- [ ] `seq_offset.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py` each correctly read
      the union of week folders for the source(s) they consume.
- [ ] `query.py`'s existing test suite passes unmodified (or with only confirmed-necessary changes,
      documented in Implementation Notes).
- [ ] `validate.py`'s drift-report functions produce identical results on the post-migration corpus as
      pre-migration, for a fixed historical time window (regression check).

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: this ticket's tests need real
  multi-week files on disk)
- TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD (child 4 — independent, file-disjoint,
  parallelizable with this ticket once child 2 lands)
- TCK-20260902-MONITORING-SHARD-CONSUMERS — the prior epic's tools-only consumer migration this
  ticket extends to `runs`/`events` and generalizes across all 3 sources.

## Related Docs
- `docs/agent-monitoring/schema.md`, `docs/agent-monitoring/README.md` (staleness-check description,
  Navigation table — broader consumer-facing doc language deferred to child 7 per the prior epic's
  own child-1/child-3 split, but confirm no accuracy gap is left dangling by this ticket's own
  functional change).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/` — the dual-mode
  directory-glob-or-literal-file pattern and multi-shard mtime staleness-check design this ticket
  generalizes from `tools`-only to all 3 sources.

## Related Code Areas
- `tools/agent-monitoring/build_index.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/manifest.py`
- `tools/agent-monitoring/seq_offset.py`
- `tools/agent-monitoring/weight_sensitivity_check.py`
- `tools/agent-monitoring/retro_nudge_hook.py`
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py`
- `tools/agent-monitoring/validate.py`
- `tools/agent-monitoring/query.py`

## Assumptions / Open Questions
- Assumes child 2 (migration) has landed — real, complete week-folder data exists on disk.
- `done_ticket_monitoring_coverage.py`'s exact `runs.jsonl` path constant was not fully pinned down by
  this session's grep (only doc-comment references were found) — the investigator must confirm the
  real constant/read site at implementation time before planning the fix.
- `query.py`'s/`validate.py`'s exact `runs.jsonl`/`events.jsonl` direct-read scope (vs. pure
  index-consumption) needs re-confirmation with real evidence at implementation time, same caveat the
  prior epic's consumer-migration ticket carried for the `tools` source.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
