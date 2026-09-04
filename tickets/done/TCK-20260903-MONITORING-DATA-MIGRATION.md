---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-MIGRATION
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260903-MONITORING-DATA-MIGRATION

## Title
One-time migration: consolidate monolithic `runs.jsonl`/`events.jsonl` and the prior epic's already-
sharded `tools/tools-YYYY-Www.jsonl` files into `agent-monitoring/data/YYYY-Www/{runs,events,
tools}.jsonl`, retire all 3 old physical shapes

## Status
DONE

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
- [x] Every pre-cutover line in `agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl`,
      and every line across all `agent-monitoring/tools/tools-*.jsonl` shards, is present,
      content-preserved, in exactly one resulting `agent-monitoring/data/<week>/<source>.jsonl` file —
      verified by an automated script/test against the real corpus, not manual spot-check.
- [x] No line is duplicated or dropped for any of the 3 sources (line-count and content reconciliation
      both pass per source, reported in Test Summary).
- [x] Records within each resulting file remain in original chronological (append) order.
- [x] Any week folder already receiving live rows from child 1's write-path cutover correctly
      contains migrated historical rows before live rows, for each source independently.
- [x] `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and
      `agent-monitoring/tools/` no longer exist in the working tree after this ticket closes; full
      history remains recoverable via `git log --follow`.
- [x] `.gitattributes` no longer references any of the 3 retired paths; the unified glob from child 1
      remains.
- [x] The migration script's own zero-data-loss verification run against the real historical data
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

Implemented exactly per `staging_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/plan.md`'s 10
steps, in order, with one real deviation discovered post-Step-7 (documented below and in plan.md's
own new "Deviations" section).

- **Step 1-5**: `tools/agent-monitoring/migrate_monitoring_data.py` (new). Imports
  `_parse_ts_to_week`/`UNKNOWN_WEEK_KEY` from `migrate_tools_shards.py` (unmodified) and
  `write_lines` from `writer.py` (unmodified). Two genuinely distinct orchestration paths:
  `_migrate_rebucketed_source()` (runs/events — per-line `json.loads()` + `RUNS_FIELD_PRIORITY`/
  `EVENTS_FIELD_PRIORITY` 8-field fallback lookup via `bucket_lines_by_week_multi_field()`) and
  `_migrate_tools_relocation()` (tools — pure filename-based relocation via
  `relocate_tools_shards()`, zero per-line `json.loads()` for bucketing purposes). Both converge on
  the generalized `write_week_bucket()`/`verify_migration()` primitives (mechanically identical to
  the reference implementation except `_target_path_for_week()` replacing `_shard_path_for_week()`).
  `main()` never calls `git rm`.
- **Step 6**: Ran the real migration against the actual `agent-monitoring/runs.jsonl` (1,388 lines),
  `agent-monitoring/events.jsonl` (9,018 lines), and `agent-monitoring/tools/` (180,292 lines across
  14 shards). `verification_passed: true` for all 3 sources — full report in Test Summary below.
- **Step 7**: `git rm agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` and
  `git rm -r agent-monitoring/tools/`, run only after Step 6's report confirmed
  `verification_passed: true` for all 3 sources.
- **Step 8**: `.gitattributes` — removed the 3 superseded `merge=union` lines; kept
  `agent-monitoring/data/*/*.jsonl merge=union` and `tickets/working_log.csv merge=union` plus both
  comment blocks.
- **Step 9**: `tests/tools/test_migrate_tools_shards.py`'s
  `test_gitattributes_no_longer_references_retired_tools_jsonl_path` — flipped the second assertion
  to `not in content`. `tests/integrity/test_merge_union_gitattributes.py` — renamed
  `test_gitattributes_lines_present_for_three_legacy_union_merge_paths` to
  `test_gitattributes_line_present_for_working_log_csv` (drops the 2 retired-line assertions, keeps
  only `working_log.csv`), and rewrote `test_gitattributes_line_present_for_shard_glob` to
  `test_gitattributes_lines_absent_for_retired_monitoring_paths` (asserts all 3 retired lines absent
  and the unified glob present). `test_concurrent_branch_appends_merge_without_conflict_markers` left
  untouched per plan (builds its own throwaway `.gitattributes`, unaffected).
- **Step 10**: `docs/agent-monitoring/schema.md` — updated the 3 "remains present... until a future
  migration ticket" sections (runs.jsonl, events.jsonl, tools.jsonl) to state the migration is
  complete, name this ticket, and cite `git log --follow` for history recovery. Ran
  `make knowledge-index-update` after.

**Deviation (discovered post-Step-7, documented in plan.md's own new "Deviations" section, not
worked around):** the broad regression pass surfaced 7 newly-failing tests across 3 files
(`test_agent_monitoring_legacy_reader.py` x2, `test_agent_monitoring_manifest.py` x4,
`test_done_ticket_monitoring_coverage.py` x1) that read the real `agent-monitoring/` directory
directly and depend on the now-retired `runs.jsonl`/`events.jsonl`/`tools/` paths — broader
collateral than the Test Plan's Regression Surface section anticipated (it incorrectly asserted
these were `tmp_path`-scoped and unaffected). This is the same class of accepted risk the plan
already documented for `src/api/agent_ops_dashboard/ingest.py` (children 3/4's consumer-update job),
just wider than originally traced. No consumer tool or test was modified to route around this — see
plan.md's Deviations section for the full breakdown and the 8th, unrelated, pre-existing
`test_kgmcp_phase3_pilot_acceptance_measurement.py` resource-budget timeout failure (confirmed
unrelated to this ticket by traceback).

## Test Summary

Scoped command run: `pytest tests/tools/test_migrate_monitoring_data.py
tests/tools/test_migrate_tools_shards.py tests/integrity/test_merge_union_gitattributes.py -v`
→ **26 passed, 5 skipped** (the 5 skips are `_run_migration_against_copy()`-style real-corpus
integration tests that correctly skip once their source has been retired — the intended end state,
not a regression, matching the prior epic's own precedent).

Broad regression pass: `pytest tests/tools/ tests/integrity/ -k "monitoring or gitattributes or
agent_ops_dashboard or migrate or writer" -v` → **273 passed, 8 failed, 5 skipped, 2406 deselected**.
7 of the 8 failures are the documented Deviation above (real-corpus-dependent consumer tests broken
by legacy-path retirement, out of scope to fix here); the 8th (`test_kgmcp_phase3_pilot_acceptance_
measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`) is a
pre-existing, unrelated resource-budget `TimeoutError` reading `docs/REGISTRY.yaml` via a live
gateway call, marked `@pytest.mark.extra_slow`/`@pytest.mark.slow`.

**Step 6's real migration report (against the actual historical corpus, run before any `git rm`):**

```json
{
  "runs": {
    "original_total": 1388, "migrated_total": 1388, "explained_delta": 0,
    "reconciles_exactly": true, "content_preserved": true, "all_lines_parse": true,
    "verification_passed": true, "week_count": 15
  },
  "events": {
    "original_total": 9018, "migrated_total": 9018, "explained_delta": 0,
    "reconciles_exactly": true, "content_preserved": true, "all_lines_parse": true,
    "verification_passed": true, "week_count": 15
  },
  "tools": {
    "original_total": 180292, "migrated_total": 184206, "explained_delta": 3914,
    "reconciles_exactly": true, "content_preserved": true, "all_lines_parse": true,
    "verification_passed": true, "week_count": 14
  }
}
```
(`tools`'s `explained_delta` of 3,914 is the live current-week `agent-monitoring/data/2026-W36/
tools.jsonl` content already written by child 1's cutover before this migration ran — correctly
merged via Case B, migrated-first. `runs`/`events` had no live current-week content yet at run time,
matching investigation's own time-sensitivity note.) **`verification_passed: true` for all 3 sources
confirmed before Step 7's `git rm` ran** — zero data loss.

## Files Changed
- `tools/agent-monitoring/migrate_monitoring_data.py` (new)
- `tests/tools/test_migrate_monitoring_data.py` (new)
- `tests/tools/test_migrate_tools_shards.py` (1 assertion flipped)
- `tests/integrity/test_merge_union_gitattributes.py` (2 test functions rewritten/renamed)
- `.gitattributes` (3 lines removed)
- `docs/agent-monitoring/schema.md` (3 sections updated)
- `agent-monitoring/runs.jsonl` (removed, `git rm`)
- `agent-monitoring/events.jsonl` (removed, `git rm`)
- `agent-monitoring/tools/` (removed, `git rm -r`, 14 shard files)
- `agent-monitoring/data/2026-W23/` through `2026-W36/` and `agent-monitoring/data/unknown-week/`
  (new/updated `runs.jsonl`/`events.jsonl`/`tools.jsonl` per-week files — migration output)
- `tickets/inprogress/TCK-20260903-MONITORING-DATA-MIGRATION.md` (this file)
- `staging_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/plan.md` (new "Deviations" section
  appended)
- `staging_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/investigation.md`,
  `staging_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/test_plan.md` (pre-existing from this
  run's own Investigate/Plan phases — not rewritten during Implement, listed here per ticket-hygiene
  convention since they are part of this run's own changeset)

## Completion Summary

Implemented `migrate_monitoring_data.py`, generalizing the prior epic's single-source
`migrate_tools_shards.py` to 3 sources via 2 genuinely distinct strategies (per-line field-priority
re-bucketing for `runs`/`events`; pure filename-based relocation for `tools`), sharing the same
rename-aside + `write_lines()` write primitive and full-corpus verification primitive. Ran the
migration for real against the actual historical corpus (1,388 `runs` + 9,018 `events` + 180,292
`tools` lines); zero-data-loss verification passed for all 3 sources before retiring
`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and `agent-monitoring/tools/` via
`git rm`, updating `.gitattributes` and `docs/agent-monitoring/schema.md` to match. Discovered and
documented (not silently worked around) a broader-than-anticipated collateral test-breakage surface
in 3 consumer test files that read the real corpus directly — an accepted, documented gap matching
the plan's own already-ratified `ingest.py` dashboard-gap precedent, left for children 3/4 to close.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently confirmed the 7-test regression is genuinely out-of-scope (2 of 3 affected consumer
modules are explicitly named in child 1's own Out of Scope list) and re-derived the zero-data-loss
verification counts from the real corpus itself, matching the captured report exactly.
Architecture-Verify (architecture-reviewer): **APPROVED** — verify-before-retire ordering confirmed
with real evidence, the 2 migration strategies confirmed genuinely separated (not collapsed), no
scope creep, no recurring automation added. Added an explicit note to
`TCK-20260903-MONITORING-DATA-CONSUMERS-CORE.md` naming the 3 affected test files so they aren't
missed. Verify (done-checker): **READY FOR FINALIZE** — 8/8 conditions checked PASS, including an
independent broad regression sweep confirming no undiscovered failures beyond the documented 7 (plus
1 pre-existing, unrelated timeout).
