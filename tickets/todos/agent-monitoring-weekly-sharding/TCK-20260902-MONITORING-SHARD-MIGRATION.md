---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-MIGRATION
phase: open
date: 2026-09-02
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260902-MONITORING-SHARD-MIGRATION

## Title
One-time migration: split the historical `agent-monitoring/tools.jsonl` into weekly ISO-week shard
files and retire the monolithic file

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`agent-monitoring/tools.jsonl` currently holds 179,096 lines / 64MB of historical tool-call records,
predating `TCK-20260902-MONITORING-SHARD-WRITE-PATH` (child 1)'s cutover to per-ISO-week shard
files under `agent-monitoring/tools/`. This ticket is child 2 of
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`: a one-time migration that splits every existing
line of the historical file into the matching weekly shard (keyed by each record's own `ts` field,
not by physical line position), verifies zero data loss, and then retires the old monolithic file
from the working tree — its full content remains recoverable via git history, so this is a
structural supersession of the old physical layout, not a "don't delete data" violation; that
distinction must be explicit so a future implementer doesn't misread the constraint as "never touch
the old file."

This ticket has a hard prerequisite on child 1 (write-path rotation) having already landed: child 1
may already be actively writing new rows into the current week's shard file
(`agent-monitoring/tools/tools-<current-week>.jsonl`) by the time this migration runs, so the
migration must merge historical pre-cutover rows for that same week into the already-existing shard
correctly (chronological order preserved, no duplication), not assume it is creating every shard
file from scratch.

## Scope
- Write a one-time migration script under `tools/agent-monitoring/` (implementer's choice of exact
  filename, e.g. `migrate_tools_shards.py`) that:
  - Reads every line of the existing `agent-monitoring/tools.jsonl` (179,096 lines as of
    2026-09-02).
  - Buckets each record by its `ts` field's ISO week (`%G-W%V`, the same format used by
    `generate_retro.py::iso_week()` and child ticket 1's write path), preserving each record's
    original relative (append) order within its week bucket.
  - Handles the malformed/off-schema historical lines already documented in
    `docs/agent-monitoring/schema.md`'s Known Limitations (a handful of confirmed rows missing
    `tool`/`run_id`/`seq`) without erroring out — route them by whatever `ts` they do carry, or to a
    documented fallback bucket if `ts` itself is missing/unparseable; decide and document the exact
    fallback rule used.
  - Appends into (never overwrites) any shard file(s) child ticket 1's write-path rotation has
    already created for the current in-progress week, preserving chronological order — migrated
    historical rows for that week must sort before any post-cutover live rows already present in
    that shard.
  - Writes each week's bucket through `tools/agent-monitoring/writer.py::write_lines()` (one lock
    acquisition per batch, preserving its existing "one batch write = one contiguous block of lines"
    guarantee) rather than a bare unlocked file write.
- Zero-data-loss verification: confirm the total pre-cutover line count in
  `agent-monitoring/tools.jsonl` equals the sum of migrated-line counts across all resulting shard
  files (post-cutover live rows already in the current week's shard are an explained delta from
  child ticket 1's rotation, not data loss — report this distinction explicitly rather than diffing
  raw totals). Verify every migrated line round-trips (`json.loads` succeeds, content preserved
  modulo trailing newline) — implementer's choice on full-corpus vs. sampled verification, documented
  either way.
- Retire the old monolithic `agent-monitoring/tools.jsonl` from the working tree (`git rm`) once
  verification passes. Its content remains fully recoverable via git history (prior commits) — no
  data is actually lost. Make this "supersede the physical layout, not delete the data" distinction
  explicit in Implementation Notes.
- Remove the now-superseded `agent-monitoring/tools.jsonl merge=union` line from `.gitattributes`
  (the shard-directory glob added by child ticket 1 already covers ongoing writes).
- Run this as a genuinely one-time operation — no ongoing/scheduled re-run mechanism and no Make
  target (unlike `build_index.py`'s repeatable `make agent-monitoring-index`; this is a single
  structural migration, run once).

## Out of Scope
- Changing the write path itself — already done by child ticket 1 (hard prerequisite, per
  `SEQUENCE.md`).
- Updating `query.py`/`generate_retro.py`/`validate.py`/`build_index.py` to actually read the new
  shard files — that is `TCK-20260902-MONITORING-SHARD-CONSUMERS` (child 3). This ticket only
  produces correct shard files on disk; it does not require any production reader to consume them
  yet (though the migration script's own verification step necessarily reads its own output back).
- Repairing or normalizing the content of any malformed historical line beyond routing it to a
  correct week bucket — no schema upgrade, no backfill of missing fields, no content rewriting.
- Deleting or altering git history — retiring the file is a working-tree change (`git rm` + commit)
  only; all prior commits containing the monolithic file's full history remain untouched.

## Acceptance Criteria
- [ ] Every one of the 179,096 pre-cutover lines in the original `agent-monitoring/tools.jsonl` is
      present, content-preserved, in exactly one resulting
      `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard file — verified by an automated
      script/test, not manual spot-check.
- [ ] No line is duplicated across shards and no line is dropped (line-count and content
      reconciliation both pass, reported in Test Summary).
- [ ] Records within each shard file remain in original chronological (append) order.
- [ ] The current-week shard correctly contains both migrated historical rows and any live rows
      child ticket 1's rotation already wrote, in correct relative order (migrated rows first).
- [ ] `agent-monitoring/tools.jsonl` no longer exists in the working tree after this ticket closes
      (`git status`/`ls` confirms); its full history remains recoverable via `git log --follow`.
- [ ] `.gitattributes` no longer references the retired single-file path; the shard-glob entry from
      child ticket 1 remains.
- [ ] The migration script's own zero-data-loss verification run against the real historical file
      (not a synthetic fixture) is captured in Test Summary before the file is retired.

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC (parent epic)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH (child 1 — hard prerequisite: this ticket cannot
  correctly determine what the current week's shard already contains without it having landed
  first)
- TCK-20260902-MONITORING-SHARD-CONSUMERS (child 3 — depends on this ticket's shard files existing
  on disk to be testable end-to-end)
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK / TCK-20260721-MONITORING-WRITER-UNIFICATION —
  establish the `write_line()`/`write_lines()` locked-append contract this migration script's own
  writes must route through.

## Related Docs
- `docs/agent-monitoring/schema.md` — Known Limitations section (documents the handful of
  off-schema historical rows this migration must handle without erroring)
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` — precedent for
  this corpus's historical data-quality caveats being accepted-as-is (cited here as precedent that
  migration is a relocation, not a repair)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s batch-write
  lock-window tradeoff, directly relevant to this ticket's `write_lines()` usage.

## Related Code Areas
- `agent-monitoring/tools.jsonl` (source, retired by this ticket)
- `agent-monitoring/tools/` (shard directory, created by child ticket 1, populated by this ticket)
- `tools/agent-monitoring/writer.py` (`write_lines()`, reused unmodified)
- `.gitattributes`
- `docs/agent-monitoring/schema.md` Known Limitations section

## Assumptions / Open Questions
- Assumes child ticket 1 (write-path rotation) has already landed — `SEQUENCE.md` enforces this
  order via `implement-epic`.
- Assumes `ts` is present and parseable on the overwhelming majority of the 179,096 historical
  lines (the documented record shape includes `ts` per `docs/agent-monitoring/schema.md`); the
  exact fallback rule for the rare line with missing/malformed `ts` is an implementation decision
  to be made and documented, not pre-specified here.
- "Retire the monolithic file" means remove it from the working tree via a real commit, not delete
  git history — this distinction was explicitly requested to be made unambiguous for a future
  implementer, since CLAUDE.md's "don't mutate durable state outside authoritative flows" /
  "don't guess" hard rules could otherwise be misread as prohibiting this file's removal entirely.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
