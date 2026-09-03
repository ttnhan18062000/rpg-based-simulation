---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-MIGRATION
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260903-MONITORING-DATA-MIGRATION

## Title
One-time migration: consolidate monolithic `runs.jsonl`/`events.jsonl` and the prior epic's already-
sharded `tools/tools-YYYY-Www.jsonl` files into `agent-monitoring/data/YYYY-Www/{runs,events,
tools}.jsonl`, retire all 3 old physical shapes

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child 2 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. This ticket consolidates **3 different
current physical shapes** into the one unified shape, in the same migration run:

1. `agent-monitoring/runs.jsonl` (monolithic) — bucket each record by its own `start_ts` field's ISO
   week into `agent-monitoring/data/<week>/runs.jsonl`.
2. `agent-monitoring/events.jsonl` (monolithic) — bucket each record by its own `ts` field's ISO week
   into `agent-monitoring/data/<week>/events.jsonl`.
3. `agent-monitoring/tools/tools-YYYY-Www.jsonl` (already correctly bucketed by the prior epic's
   `migrate_tools_shards.py`, plus a `tools-unknown-week.jsonl` fallback bucket) — this is a
   **relocation, not a re-bucketing**: each shard's week is already correct, it only needs to move
   from `agent-monitoring/tools/tools-<week>.jsonl` into `agent-monitoring/data/<week>/tools.jsonl`.

This ticket has a hard prerequisite on child 1 (write-path unification) having already landed: child
1 may already be actively writing new rows into the current week's folder
(`agent-monitoring/data/<current-week>/`) for all 3 sources by the time this migration runs, so the
migration must merge historical pre-cutover rows into any already-existing current-week files
correctly (chronological order preserved, migrated rows first, no duplication) — reuse the prior
epic's `migrate_tools_shards.py::write_week_bucket()` rename-aside + single-combined-`write_lines()`
algorithm, generalized to 3 sources instead of 1.

## Scope
- Write a one-time migration script under `tools/agent-monitoring/` (e.g.
  `migrate_monitoring_data.py`) that:
  - Reads every line of the existing `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
    and every `agent-monitoring/tools/tools-*.jsonl` shard (including `tools-unknown-week.jsonl`).
  - Buckets `runs`/`events` rows by their own `start_ts`/`ts` field's ISO week (`%G-W%V`), tolerant of
    the same handful of malformed/off-schema historical lines already documented in
    `docs/agent-monitoring/schema.md`'s Known Limitations — route them by whatever timestamp field
    they do carry, or to a documented fallback bucket (e.g. `unknown-week`, matching the prior epic's
    convention) if it's missing/unparseable. Decide and document the exact fallback rule.
  - Relocates `tools` shards by parsing the ISO week directly out of each existing shard's filename
    (`tools-YYYY-Www.jsonl` → week `YYYY-Www`; `tools-unknown-week.jsonl` → the same fallback bucket
    used for `runs`/`events`) — no re-bucketing of individual `tools` records needed, only file
    relocation, since the prior epic already did the per-line bucketing correctly.
  - For any week folder child 1's write-path cutover has already created and started writing into
    (for any of the 3 sources independently — `runs`, `events`, and `tools` need not all be
    "current" in the same way, since `tools`/`events` bucket by write-time but `runs`/`events`'
    historical rows bucket by their own field), append migrated historical rows so they sort strictly
    before any already-present live rows, using a rename-aside + single-combined-`write_lines()` call
    per (week, source) pair — reuse and generalize `migrate_tools_shards.py::write_week_bucket()`
    rather than reinventing it.
  - Writes every batch through `tools/agent-monitoring/writer.py::write_lines()` (one lock
    acquisition per batch), never a bare unlocked file write.
- Zero-data-loss verification, per source: confirm the pre-cutover line count for each of
  `runs.jsonl`, `events.jsonl`, and the sum across all `tools/tools-*.jsonl` shards equals the sum of
  migrated-line counts across all resulting `agent-monitoring/data/*/<source>.jsonl` files (any
  already-present live rows are an explained delta, reported explicitly, not diffed away). Verify
  every migrated line round-trips (`json.loads` succeeds, content preserved) — full-corpus, not
  sampled, matching the prior epic's precedent.
- Retire, via `git rm`, all 3 old physical paths once verification passes:
  `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and the entire
  `agent-monitoring/tools/` directory. Full content remains recoverable via git history — this is a
  supersession of physical layout, not data loss; make that distinction explicit in Implementation
  Notes, same as the prior epic's migration ticket did.
- Update `.gitattributes`: remove the 3 now-superseded lines (`agent-monitoring/runs.jsonl`,
  `agent-monitoring/events.jsonl`, `agent-monitoring/tools/*.jsonl`), keeping only the unified glob
  child 1 already added.
- Run as a genuinely one-time operation — no ongoing/scheduled re-run mechanism, no Make target.

## Out of Scope
- Changing the write path itself — already done by child 1 (hard prerequisite).
- Updating any consumer (`build_index.py`, `generate_retro.py`, `manifest.py`, etc.) to read the new
  layout — that is children 3 and 4. This ticket only produces correct files on disk (its own
  verification step necessarily reads its own output back, but no production reader is required to
  consume the new layout yet).
- The codex-subsystem re-migration (child 5) and referential-integrity tooling (child 6) — both
  depend on this ticket's output but are separate scope.
- Repairing or normalizing the content of any malformed historical line beyond routing it to a
  correct week bucket.
- Deleting or altering git history — retiring the old paths is a working-tree change (`git rm` + a
  real commit) only.

## Acceptance Criteria
- [ ] Every pre-cutover line in `agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl`,
      and every line across all `agent-monitoring/tools/tools-*.jsonl` shards, is present,
      content-preserved, in exactly one resulting `agent-monitoring/data/<week>/<source>.jsonl` file —
      verified by an automated script/test against the real corpus, not manual spot-check.
- [ ] No line is duplicated or dropped for any of the 3 sources (line-count and content reconciliation
      both pass per source, reported in Test Summary).
- [ ] Records within each resulting file remain in original chronological (append) order.
- [ ] Any week folder already receiving live rows from child 1's write-path cutover correctly
      contains migrated historical rows before live rows, for each source independently.
- [ ] `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and
      `agent-monitoring/tools/` no longer exist in the working tree after this ticket closes; full
      history remains recoverable via `git log --follow`.
- [ ] `.gitattributes` no longer references any of the 3 retired paths; the unified glob from child 1
      remains.
- [ ] The migration script's own zero-data-loss verification run against the real historical data
      (not a synthetic fixture) is captured in Test Summary before any file is retired.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1 — hard prerequisite)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD, -CODEX-REMIGRATION,
  -REFERENTIAL-INTEGRITY (children 3-6 — all depend on this ticket's shard files existing on disk)
- TCK-20260902-MONITORING-SHARD-MIGRATION — the prior epic's tools-only migration this ticket reuses
  the rename-aside + `write_lines()` batch algorithm from, generalized to 3 sources and to relocating
  (not re-bucketing) the already-correct `tools` shards.

## Related Docs
- `docs/agent-monitoring/schema.md` — Known Limitations section (malformed historical rows).
- `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` — precedent that
  this corpus's historical data-quality caveats are accepted-as-is; migration is relocation, not
  repair.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/` — the rename-aside algorithm and
  cross-worktree `git rm` merge-conflict runbook this ticket directly reuses/extends.

## Related Code Areas
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl` (sources, retired by this ticket)
- `agent-monitoring/tools/` (source, retired by this ticket)
- `agent-monitoring/data/` (destination, created by this ticket)
- `tools/agent-monitoring/writer.py` (`write_lines()`, reused unmodified)
- `tools/agent-monitoring/migrate_tools_shards.py` (reference implementation to generalize/reuse)
- `.gitattributes`

## Assumptions / Open Questions
- Assumes child 1 has already landed — `SEQUENCE.md` enforces this.
- Assumes `start_ts` (`runs.jsonl`) and `ts` (`events.jsonl`) are present and parseable on the
  overwhelming majority of historical lines; the exact fallback rule for a rare missing/malformed
  value is an implementation decision to make and document, not pre-specified here.
- Cross-worktree `git rm` merge-conflict handling: same runbook as the prior epic's migration ticket
  (take the deletion side, re-run this migration against any other branch's pre-merge interim rows if
  needed) — document in this ticket's own header comment/Implementation Notes rather than assuming
  it's automatically inherited.
- **Explicitly re-evaluated, not silently carried forward: this ticket retires 3 paths in one commit
  (`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, the entire `agent-monitoring/tools/`
  directory) instead of the prior epic's 1 (`tools.jsonl` alone) — a 3x larger modify/delete
  conflict surface for every other concurrently-active worktree/session in this shared repo whose
  branch later merges past this commit (this is not hypothetical: the exact scenario already fired
  for real once this session, on `tools.jsonl` alone, during PR #112's own merge with `main`).
  Decision: **stay documented-runbook-only, do not build new automated coordination tooling** — this
  repo's established precedent (the `docs/REGISTRY.yaml` no-merge-driver case, and the prior epic's
  own choice) is "document the recovery step," not "prevent the scenario," and nothing about 3 files
  vs. 1 changes the actual recovery mechanics (still: take the deletion side per path, re-run this
  same migration script against the delta). What DOES change, and must be reflected in this ticket's
  runbook comment/Implementation Notes: name all 3 retired paths explicitly (not just describe the
  pattern abstractly once), and — operational guidance, not tooling — recommend the implementer land
  and merge this epic's PR promptly once ready rather than letting it sit open, precisely because the
  exposure window is now 3x wider. Do not silently reuse language that only mentions `tools.jsonl`.
- "Retire" means remove from the working tree via a real commit, not delete git history — same
  explicit distinction the prior epic's migration ticket required, carried forward here.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
