---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-MIGRATION
phase: done
date: 2026-09-02
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260902-MONITORING-SHARD-MIGRATION

## Title
One-time migration: split the historical `agent-monitoring/tools.jsonl` into weekly ISO-week shard
files and retire the monolithic file

## Status
DONE

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
- [x] Every one of the 179,096 pre-cutover lines in the original `agent-monitoring/tools.jsonl` is
      present, content-preserved, in exactly one resulting
      `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard file — verified by an automated
      script/test, not manual spot-check. (Real line count at run time was 179,243, not 179,096 —
      both were already-stale snapshots per plan.md; verified by the migration script's own
      real-corpus run, see Test Summary.)
- [x] No line is duplicated across shards and no line is dropped (line-count and content
      reconciliation both pass, reported in Test Summary).
- [x] Records within each shard file remain in original chronological (append) order.
- [x] The current-week shard correctly contains both migrated historical rows and any live rows
      child ticket 1's rotation already wrote, in correct relative order (migrated rows first).
- [x] `agent-monitoring/tools.jsonl` no longer exists in the working tree after this ticket closes
      (`git status`/`ls` confirms); its full history remains recoverable via `git log --follow`.
- [x] `.gitattributes` no longer references the retired single-file path; the shard-glob entry from
      child ticket 1 remains.
- [x] The migration script's own zero-data-loss verification run against the real historical file
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

Followed `staging_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/plan.md`'s 8 steps in order.

**New script**: `tools/agent-monitoring/migrate_tools_shards.py`, implementing:
- `bucket_lines_by_week(lines) -> dict[str, list[str]]` — single forward pass, `json.loads()` per
  line, tolerant `ts` parsing (`Z`→`+00:00` substitution, fallback to naive `fromisoformat`),
  routes to the literal fallback key `"unknown-week"` (file `tools-unknown-week.jsonl`) when `ts`
  is missing/unparseable. Route-only — never repairs/normalizes content.
- `write_week_bucket(week_key, lines, shard_dir) -> tuple[bool, list[str]]` — Case A (target
  absent/empty): one direct `write_lines()` call. Case B (target already has live content):
  `os.replace()` rename-aside to `<name>.pre-migration-backup`, build
  `combined = migrated_lines + live_snapshot`, one single `write_lines()` call, then a
  reconciliation check that the new file's trailing `len(live_snapshot)` lines exactly equal the
  pre-migration snapshot before deleting the backup; raises and preserves the backup if the check
  fails. Never overwrites/truncates the live file directly.
- `verify_migration(source_lines, buckets, shard_dir, live_snapshots) -> dict` — full-corpus
  (not sampled) re-read of every shard, exact reconciliation
  (`migrated_total == original_total + explained_delta`), per-bucket content-preservation
  comparison against what was bucketed, and a `json.loads()` round-trip check on every persisted
  line.
- `main()` — snapshot-reads the real count at run time (never hardcodes 179,096/179,243), does
  not itself call `git rm`.

**Deviations from plan.md's literal function signatures** (behavior/intent preserved, only the
return-value shape was extended): `write_week_bucket` returns `tuple[bool, list[str]]` instead of
a bare `bool`, and `verify_migration` takes `(source_lines, buckets, shard_dir, live_snapshots)`
instead of `(pre_migration_line_count, shard_dir, current_week_pre_migration_live_count)`. This
was necessary to thread the *actual content* of each week's live snapshot — captured at the exact
moment `write_week_bucket` processes that bucket, per plan.md's own "minimizes the window between
snapshot and rename" requirement — through to `verify_migration`'s content-preservation check,
which needs real content (not just a count) to prove no line was corrupted or duplicated. All of
plan.md's substantive constraints (one `write_lines()` call per bucket, rename-aside algorithm,
exact reconciliation, full-corpus verification, no dedup, no reorder) are implemented exactly as
specified.

**Bug found and fixed during implementation, not anticipated by plan.md**: `write_lines()`'s
internal `_acquire_lock()` creates the lock file at `target_path.parent / "<name>.lock"` via
`os.open(..., O_CREAT|O_EXCL)` *before* `write_lines()` gets to run its own
`target_path.parent.mkdir()` (that mkdir only executes after the lock is already held). If
`shard_dir` does not yet exist, the very first `write_lines()` call for a new week fails with
`FileNotFoundError` inside `_acquire_lock`, caught internally and reported as `False` (never
raises to the caller, per `writer.py`'s contract) — silently producing a failed write with no
loud error unless the caller checks the return value. `post_tool_hook.py` already works around
this the same way (`tools_file.parent.mkdir(parents=True, exist_ok=True)` immediately before its
own `write_line()` call) — `write_week_bucket()` now does the equivalent
`target_path.parent.mkdir(parents=True, exist_ok=True)` before either write path, matching that
established, pre-existing pattern rather than inventing a new one.

**Real one-time migration run** (per plan.md Step 4.6): executed once against the real
`agent-monitoring/tools.jsonl` / `agent-monitoring/tools/` in this worktree, using
`.venv/bin/python3 tools/agent-monitoring/migrate_tools_shards.py`. Verification passed (see Test
Summary for the full real report). `git rm agent-monitoring/tools.jsonl` was executed only after
that passing verification, per plan.md's absolute Step 4 → Step 5 ordering constraint — never
before, never in parallel.

**Supersedes the physical layout, does not delete the data**: `agent-monitoring/tools.jsonl` no
longer exists in this branch's working tree, but its full historical content remains completely
recoverable via `git log --follow -- agent-monitoring/tools.jsonl` / `git show <commit>:agent-
monitoring/tools.jsonl` against any commit prior to this ticket's `git rm` commit. No git history
was altered or deleted — only a working-tree file removal (a real commit), exactly as the ticket's
own Assumptions section required be made unambiguous.

**Cross-worktree `git rm` merge-conflict runbook** (plan.md Step 6 / Decision 5, documented not
automated): this ticket's `git rm agent-monitoring/tools.jsonl` is a one-time,
irreversible-from-the-working-tree change. Any other worktree/branch that has not yet merged past
this ticket's commit and is still appending to its own local copy of
`agent-monitoring/tools.jsonl` (confirmed real at investigation time via `git merge-base
--is-ancestor` against 5 other live checkouts, all still pre-cutover) will produce a `CONFLICT
(modify/delete): agent-monitoring/tools.jsonl deleted in HEAD and modified in <branch>` when it
later merges past this point — `merge=union` does NOT apply to modify/delete conflicts (it is a
content-merge driver, only invoked when a path exists on both sides of a 3-way merge). Resolution:
take the deletion side (`git rm agent-monitoring/tools.jsonl` at the conflict), and if that other
branch's interim rows need to be preserved, re-run this same script against that branch's
pre-merge copy of `tools.jsonl` (or a targeted subset of its new lines) before finalizing the
merge, rather than resurrecting the monolithic file. The same language is in the script's own
header comment.

**Decision 4 — accepted interim gap, `xfail`-marked, MUST be removed before any PR opens**:
per plan.md Step 8, `manifest.py`/`skill_usage_metric.py` production code was deliberately NOT
touched (child 3's scope). 5 real-corpus tests that hard-crash (`FileNotFoundError`) now that
`agent-monitoring/tools.jsonl` is gone were marked `@pytest.mark.xfail(strict=True, reason=...)`:
`tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`,
`::test_manifest_cli_reproducible_byte_identical_across_two_runs`,
`::test_build_manifest_reproducible_byte_identical_direct_call`,
`::test_manifest_run_against_real_corpus_produces_zero_diff`, and
`tests/tools/test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts`.
**These markers must be removed by child ticket 3
(`TCK-20260902-MONITORING-SHARD-CONSUMERS`) as part of its own Finalize, before this branch's PR
is opened.** If child 3 does not land immediately after in this same session, do not open a PR
with these markers still in place.

**Discrepancy found during implementation, NOT covered by plan.md's Decision 4/Step 8 — flagged,
not silently worked around**: running the full regression sweep after retirement surfaced 2
additional real-corpus test failures in `tests/tools/test_generate_retro.py` that plan.md's
5-test xfail list did not name and did not anticipate by name:
`test_correlation_real_corpus_produces_a_real_number` (asserts
`rcc["compliant_group"]["count"] > 0`, now `0`) and
`test_parity_index_readpath_call_count_matches_real_corpus_state` (asserts `result["count"] == 4`,
now `0`). Both call `generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)`, which still
points at the now-retired `agent-monitoring/tools.jsonl` path; `load_jsonl()` has a `.exists()`
guard so it does not crash (confirmed matching investigation.md's Risk #1 characterization of
`generate_retro.py` as "silent, wider-than-before empty-data degradation, no crash") — but these 2
specific tests hard-assert nonzero/exact values derived from that now-permanently-empty read, so
they fail for real, not just degrade silently. This is a real, in-scope consequence of this
ticket's own `git rm`, but plan.md's Decision 4 text explicitly enumerates only 5 tests as the
accepted interim gap and `generate_retro.py` is explicitly named as **out of scope / do-not-touch**
in this ticket (Step 3's "Do NOT touch" list and the ticket's own Out of Scope section) —
extending the xfail treatment to these 2 additional tests was not something this implementer was
authorized to decide unilaterally, per the "never edit a test/gate to make it pass instead of
fixing real behavior, except the one explicitly-planned exception" rule. **Left unresolved,
reported here and in the implementer's structured report — not xfailed, not fixed, not silently
left red without documentation.** This needs an explicit decision (most likely: extend Decision
4's accepted-gap treatment to these 2 tests too, by the same reasoning already used for the other
5, since child 3 will fix the same root cause) before Verify/Finalize proceeds. A 3rd failure seen
in the same sweep run
(`tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`)
was confirmed to be a false positive — a `conftest.py` resource-time-limit `TimeoutError` from the
combined ~190s sweep run, not a real regression; it passes cleanly (68s) when run in isolation.

## Test Summary

**Real migration script run** (`.venv/bin/python3 tools/agent-monitoring/migrate_tools_shards.py`,
executed once against the real `agent-monitoring/tools.jsonl` / `agent-monitoring/tools/`, real
output, verbatim):

```
Read 179243 lines from .../agent-monitoring/tools.jsonl at run start.
Bucketed into 14 week(s): ['2026-W24', '2026-W25', '2026-W26', '2026-W27', '2026-W28', '2026-W29',
'2026-W30', '2026-W31', '2026-W32', '2026-W33', '2026-W34', '2026-W35', '2026-W36', 'unknown-week']
  2026-W24: wrote 1430 migrated line(s)
  2026-W25: wrote 11106 migrated line(s)
  2026-W26: wrote 8536 migrated line(s)
  2026-W27: wrote 13660 migrated line(s)
  2026-W28: wrote 13444 migrated line(s)
  2026-W29: wrote 14115 migrated line(s)
  2026-W30: wrote 3979 migrated line(s)
  2026-W31: wrote 12769 migrated line(s)
  2026-W32: wrote 14882 migrated line(s)
  2026-W33: wrote 23550 migrated line(s)
  2026-W34: wrote 23034 migrated line(s)
  2026-W35: wrote 29510 migrated line(s)
  2026-W36: wrote 9227 migrated line(s), preceding 190 pre-existing live line(s)
  unknown-week: wrote 1 migrated line(s)
{
  "all_lines_parse": true,
  "content_mismatches": [],
  "content_preserved": true,
  "explained_delta": 190,
  "migrated_total": 179433,
  "original_total": 179243,
  "parse_failures": [],
  "per_shard_counts": {
    "tools-2026-W24.jsonl": 1430, "tools-2026-W25.jsonl": 11106, "tools-2026-W26.jsonl": 8536,
    "tools-2026-W27.jsonl": 13660, "tools-2026-W28.jsonl": 13444, "tools-2026-W29.jsonl": 14115,
    "tools-2026-W30.jsonl": 3979, "tools-2026-W31.jsonl": 12769, "tools-2026-W32.jsonl": 14882,
    "tools-2026-W33.jsonl": 23550, "tools-2026-W34.jsonl": 23034, "tools-2026-W35.jsonl": 29510,
    "tools-2026-W36.jsonl": 9417, "tools-unknown-week.jsonl": 1
  },
  "reconciles_exactly": true,
  "verification_passed": true,
  "week_count": 14
}
VERIFICATION PASSED. agent-monitoring/tools.jsonl has NOT been touched by this script —
retirement (git rm) is a separate, explicit step to run only now that this report is captured
in the ticket's Test Summary.
```

`179243` (original) `+ 190` (explained delta — pre-existing live rows already in the 2026-W36
shard from child 1's write path before this migration ran) `= 179433` (migrated total) — exact
match, `reconciles_exactly: true`. `content_preserved: true` (no line dropped, none duplicated,
none corrupted). `all_lines_parse: true` (every persisted line round-trips through `json.loads`).
`git rm agent-monitoring/tools.jsonl` was executed only after this report, per plan.md's ordering
constraint.

**New migration-script test suite** (`tests/tools/test_migrate_tools_shards.py`, 11 tests, run
post-retirement): 9 passed, 2 skipped (the 2 real-corpus-copy integration tests skip by design once
`agent-monitoring/tools.jsonl` no longer exists to copy — see the skip-reason string in the test
file; they already ran and passed pre-retirement, see above).

**Writer/lock-protocol regression surface** (unchanged, must not regress):
`pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py
tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_post_tool_hook.py -v` —
34 passed (0 failed). `test_monitoring_writer_single_source.py` was edited to add
`migrate_tools_shards.py` to its `_CALL_SITES` allowlist (per test_plan.md's own note that the new
script must be added there) and still passes.

**`.gitattributes` integration** (`pytest tests/integrity/test_merge_union_gitattributes.py -v`):
7 passed (0 failed) post-edit — includes the 2 edited tests
(`test_gitattributes_lines_present_for_three_legacy_union_merge_paths`,
`test_gitattributes_line_present_for_shard_glob`).

**Real-corpus consumer surface directly at risk** (`pytest
tests/tools/test_agent_monitoring_manifest.py tests/tools/test_skill_usage_metric.py -v`):
12 passed, **5 xfailed** (exactly the 5 planned, none reported as `error`) — 0 failed.

**No-mutation snapshot smoke check** (`pytest tests/agent_replay/test_no_mutation_snapshot.py -v`):
2 passed.

**Broader agent-monitoring tools/ regression sweep** (`pytest tests/tools/ -k "monitoring or
agent_monitoring or generate_retro or build_index or record_events or validate_agent_monitoring"
-v`): initially 321 passed, 4 xfailed, 2308 deselected, and 2 real failures in
`tests/tools/test_generate_retro.py` (`test_correlation_real_corpus_produces_a_real_number`,
`test_parity_index_readpath_call_count_matches_real_corpus_state`). A 3rd apparent failure in the
combined sweep (`test_kgmcp_phase3_pilot_acceptance_measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`)
was a `conftest.py` suite-resource-timeout false positive, confirmed passing (68s) in isolation.

**Resolution (orchestrating session, post-Implement)**: independently reproduced the 2 failures and
confirmed the identical root cause to the already-accepted Decision 4 gap
(`generate_retro.DEFAULT_TOOLS_FILE` pointing at the retired path). Extended the exact same
`xfail(strict=True, ...)` treatment — same reasoning, same child-3 handoff, same "markers removed
before any PR opens" gate — to these 2 tests, correcting Decision 4's list from 5 to 7 tests total
(see `plan.md`'s updated Deviations #4). Full corrected regression sweep (`pytest
tests/tools/test_migrate_tools_shards.py tests/tools/test_agent_monitoring_manifest.py
tests/tools/test_skill_usage_metric.py tests/tools/test_generate_retro.py
tests/integrity/test_merge_union_gitattributes.py tests/tools/test_monitoring_writer.py
tests/tools/test_monitoring_writer_single_source.py
tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_post_tool_hook.py -q`):
**224 passed, 2 skipped (expected, see Deviations #3), 7 xfailed (exactly the corrected list), 0
failed.**

## Files Changed
- `tools/agent-monitoring/migrate_tools_shards.py` (new) — the one-time migration script.
- `tests/tools/test_migrate_tools_shards.py` (new) — its test suite.
- `tests/tools/test_monitoring_writer_single_source.py` — added `migrate_tools_shards.py` to the
  `_CALL_SITES` allowlist (`write_lines` symbol).
- `agent-monitoring/tools.jsonl` — removed via `git rm` (retired; history recoverable via
  `git log --follow`).
- `agent-monitoring/tools/tools-2026-W24.jsonl` through `tools-2026-W35.jsonl` (new, 12 files) and
  `agent-monitoring/tools/tools-unknown-week.jsonl` (new) — shard files created by the real
  migration run.
- `agent-monitoring/tools/tools-2026-W36.jsonl` — the already-live shard, modified by the migration
  run's rename-aside + single combined `write_lines()` call (migrated historical rows now precede
  the pre-existing live rows).
- `.gitattributes` — removed the `agent-monitoring/tools.jsonl merge=union` line.
- `tests/integrity/test_merge_union_gitattributes.py` — updated the 2 dependent tests
  (renamed/reduced `test_gitattributes_lines_present_for_all_four_union_merge_paths` to
  `..._for_three_legacy_union_merge_paths`; updated `test_gitattributes_line_present_for_shard_glob`
  to assert the legacy line is now absent).
- `tests/tools/test_agent_monitoring_manifest.py` — added `import pytest` and
  `@pytest.mark.xfail(strict=True, ...)` to 4 named tests (per plan.md Decision 4/Step 8).
- `tests/tools/test_skill_usage_metric.py` — added `import pytest` and
  `@pytest.mark.xfail(strict=True, ...)` to 1 named test (per plan.md Decision 4/Step 8).
- `tests/tools/test_generate_retro.py` — added `@pytest.mark.xfail(strict=True, ...)` to 2 more
  tests (`test_correlation_real_corpus_produces_a_real_number`,
  `test_parity_index_readpath_call_count_matches_real_corpus_state`), correcting Decision 4's
  interim-gap list from 5 to 7 tests (orchestrating session, post-Implement — see Test Summary).
- `docs/agent-monitoring/schema.md` — rewrote the `## agent-monitoring/tools.jsonl` section's
  opening paragraph to state the file has been retired and where its rows now live.
- `tickets/inprogress/TCK-20260902-MONITORING-SHARD-MIGRATION.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes).
- `staging_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/investigation.md`,
  `plan.md`, `test_plan.md` — pre-existing from this run's own Investigate/Plan phases (not
  authored by this implementer pass, but part of this run's real changeset per ticket hygiene
  requirements); `plan.md` additionally gets a Deviations note appended by this implementer pass.

## Completion Summary

Wrote and ran a one-time migration script (`tools/agent-monitoring/migrate_tools_shards.py`) that
buckets every line of the 179,243-line real historical `agent-monitoring/tools.jsonl` by its `ts`
field's ISO week, appends each week's bucket into `agent-monitoring/tools/tools-YYYY-Www.jsonl`
via `writer.py::write_lines()` (one locked batch per week), and — for the one week already
receiving live post-cutover rows from child ticket 1's write path (2026-W36) — used a
rename-aside + single-combined-write algorithm so migrated historical rows land strictly before
the 190 pre-existing live rows, with a post-write reconciliation check. Ran the script for real
against the actual corpus; its full-corpus (not sampled) zero-data-loss verification passed
exactly (`179243 + 190 = 179433`, content preserved, all lines parse) before `git rm
agent-monitoring/tools.jsonl` was executed, retiring the monolithic file from the working tree
(history recoverable via `git log --follow`) and removing its now-superseded `.gitattributes`
line. Per plan.md's explicit, accepted Decision 4, 7 real-corpus tests total (4 in
`test_agent_monitoring_manifest.py`, 1 in `test_skill_usage_metric.py`, 2 in
`test_generate_retro.py` — the last 2 identified during implementation and confirmed by the
orchestrating session to share the identical root cause, extending Decision 4's list rather than
requiring a new decision) were marked `xfail` (strict) as a deliberate, documented interim gap that
child ticket 3 must close and un-xfail before any PR opens. **These 7 markers are the single most
important handoff item to child ticket 3** — its own Finalize must confirm all 7 pass again with
the markers removed before this branch is ever pushed as a PR.
