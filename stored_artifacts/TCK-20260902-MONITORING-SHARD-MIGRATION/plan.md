---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-MIGRATION
artifact_type: plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Implementation Plan — TCK-20260902-MONITORING-SHARD-MIGRATION

## Summary

Write a one-time migration script, `tools/agent-monitoring/migrate_tools_shards.py`, that reads
`agent-monitoring/tools.jsonl` (real corpus, 179,243 lines / 64MB as of 2026-09-02 — the implementer
must re-derive this count at run time, never hardcode it), buckets every line by its `ts` field's
ISO week (`%G-W%V`), routes the single `ts`-less line to a dedicated
`agent-monitoring/tools/tools-unknown-week.jsonl` fallback shard, and writes each week's bucket into
its shard file via exactly one `write_lines()` call per week — including a special merge path for
whichever week is already receiving live post-cutover rows from child ticket 1's write path (as of
this writing, `2026-W36`), which must land migrated historical rows *before* the already-present
live rows without violating write_lines()'s append-only, single-call-per-batch contract. A strict,
full-corpus (not sampled) zero-data-loss verification pass must run and pass before the script (or a
second, explicitly gated step) performs `git rm agent-monitoring/tools.jsonl` and removes the
now-superseded `.gitattributes` line. Three explicit decisions are recorded and executed as part of
this plan (see Anti-Drift Notes): the fallback-bucket filename, an accepted interim test-failure gap
for `manifest.py`/`skill_usage_metric.py` (deferred to child 3, guarded with `xfail`, not silently
red), and a documented (not automated) runbook for the cross-worktree `git rm` modify/delete merge
conflict this migration will eventually produce elsewhere.

## Steps

### Step 1 — Bucketing logic: read source file, parse `ts`, group by ISO week preserving order

**Files:** `tools/agent-monitoring/migrate_tools_shards.py` (new)

**Change:** Implement a pure function `bucket_lines_by_week(lines: list[str]) -> dict[str, list[str]]`
(keys are ISO-week strings `%G-W%V`, plus the literal fallback key documented below; values are the
original raw line strings — not re-serialized — in original list order):
- For each line, `json.loads()` it to extract `ts`. Confirmed by investigation.md (full-corpus scan,
  179,243 lines, 0 `json.loads` failures) that every line is syntactically valid JSON, so a bare
  `json.loads()` without a broad `except` around the parse itself is safe — but wrap field *access*
  (`record.get("ts")`) defensively since 1 line (line 1, the `implement-epic` summary record,
  confirmed in investigation.md "Current Behavior") has no `ts` key at all.
- Parse `ts` with a tolerant parser, not a single rigid `strptime` format string — investigation.md
  confirmed 3 shape variants across the real file: `%Y-%m-%dT%H:%M:%S.%fZ` (179,240 lines),
  a bare no-timezone/no-fraction `%Y-%m-%dT%H:%M:%S` (2 lines), and missing entirely (1 line).
  Implementation: `ts.replace("Z", "+00:00")` then `datetime.fromisoformat(...)`, falling back to
  `datetime.fromisoformat(ts)` directly if the first raises (covers the naive no-`Z` variant) —
  matches investigation.md's own recommended parser shape exactly ("`Z` → `+00:00` substitution,
  falling back to naive parsing when no explicit offset is present").
- Compute the ISO week via `f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"` (equivalent to
  `%G-W%V`) — same format `generate_retro.py::iso_week()` and child 1's write path already use, per
  investigation.md and the ticket's own Scope text.
- If `ts` is missing OR unparseable by both attempts above, route the line to the literal fallback
  key `"unknown-week"` (see the fallback-bucket decision in Anti-Drift Notes — this is the *key* used
  internally; Step 2 maps this key to the file `agent-monitoring/tools/tools-unknown-week.jsonl`).
- Append order within each bucket must be **the original line order in the source file**, never
  re-sorted by `ts` or any other key — this is a hard AC (ticket AC 3) and has a dedicated test
  (`test_within_week_bucket_preserves_original_append_order`). Do this by iterating the source lines
  once, in file order, appending to `dict[key].append(line)` — never building an intermediate
  `ts`-sorted structure.
- Do not repair, coerce, or normalize content of the 2 known off-schema lines (missing `tool`,
  missing `run_id`/`seq` — confirmed exact instances: line 21,117 and line 55,124 in
  investigation.md) or the 1 `ts`-less line — route-only, content-preserving, per ticket's Out of
  Scope and investigation.md's Anti-Drift Hazards.

**Do NOT touch:** `docs/agent-monitoring/schema.md`'s Known Limitations wording about the 2
off-schema rows (Step 6 handles doc updates, and even there only the `tools.jsonl` physical-location
paragraph changes, not the off-schema-row caveat itself, which remains accurate and unmodified).

**Verify:** `test_within_week_bucket_preserves_original_append_order`,
`test_malformed_and_off_schema_rows_route_without_erroring`,
`test_missing_ts_row_routes_to_documented_fallback_bucket`,
`test_ts_format_variants_all_bucket_to_correct_week` (all new, synthetic-fixture unit tests per
test_plan.md, in `tests/tools/test_migrate_tools_shards.py`).

### Step 2 — Per-week write logic via `write_lines()`, including the live-current-week merge path

**Files:** `tools/agent-monitoring/migrate_tools_shards.py`

**Change:** Confirmed contract read in full at `tools/agent-monitoring/writer.py:137-162`:
`write_lines(target_path: Path, lines: list[str]) -> bool` opens the target in `"a"` (append) mode,
acquires the lock **once** for the whole batch, writes every line inside that single lock window,
releases once, never raises (returns `bool`, writes a diagnostic sidecar on failure). This is the
**only** function this script's line-writing goes through — never a bare `open(path, "a")` loop, per
the ticket's explicit requirement and `test_migration_uses_write_lines_one_lock_per_week_batch`.

Implement `write_week_bucket(week_key: str, lines: list[str], shard_dir: Path) -> bool`:
- Resolve `target_path` = `shard_dir / f"tools-{week_key}.jsonl"` for a normal ISO-week key, or
  `shard_dir / "tools-unknown-week.jsonl"` for the `"unknown-week"` fallback key.
- **Case A — `target_path` does not exist, or exists but is empty (0 bytes):** call
  `write_lines(target_path, lines)` directly, exactly once. This covers every week bucket except
  whichever week(s) child 1's write path has already started populating (confirmed: as of this
  investigation only `2026-W36` has live content — 96+ lines — but the script must check
  `target_path.exists()` at run time, not hardcode `"2026-W36"`, since the actual week at
  implementation time may differ).
- **Case B — `target_path` exists and is non-empty (a live, actively-written shard for the
  in-progress week):** this is the hard case the ticket's AC 4 and
  `test_current_week_shard_migrated_rows_precede_existing_live_rows` require: final file content
  must be `[migrated historical lines for that week] + [pre-existing live lines, byte-identical,
  untouched]`, in that order, produced through **exactly one** `write_lines()` call for this week
  bucket (the dedicated test asserts write_lines() is called exactly once per week bucket — two
  separate append calls, one to write historical-only and a second to re-append the live suffix,
  would satisfy final byte order but fail that call-count assertion and would also leave a real race
  window where a third writer could interleave between the two calls). Algorithm:
  1. Read `target_path`'s current lines as a snapshot (`readlines()`, one pass, `rstrip("\n")` each
     so they compose correctly with `write_lines()`'s own `line + "\n"` writing) — call this
     `live_snapshot`.
  2. `os.replace(target_path, target_path.with_name(target_path.name + ".pre-migration-backup"))` —
     an atomic filesystem rename, not a `write_lines()` call and not a content mutation; moves the
     live content aside intact. This does not require or take `write_lines()`'s internal lock (it is
     a rename, not an append), and is the only way to make `target_path` "not yet exist" for the
     single combined `write_lines()` call in step 3, which is what makes the append-only contract
     produce historical-before-live ordering.
  3. `combined = lines + live_snapshot` (historical first, live second — this list order becomes the
     file's final line order once appended to the now-absent path).
  4. `ok = write_lines(target_path, combined)` — the single, required call for this week bucket;
     because `target_path` no longer exists after step 2, `write_lines()`'s `open(path, "a")`
     creates it fresh and writes `combined` as one locked, contiguous block.
  5. **Reconciliation check (must run before declaring this week bucket done):** re-read
     `target_path`'s new content and confirm its **last `len(live_snapshot)` lines exactly equal
     `live_snapshot`** (content and count). This proves the pre-existing live rows were never lost or
     reordered by this operation, regardless of what (if anything) landed in the narrow rename→write
     window from a genuinely concurrent writer (see Anti-Drift Notes for the documented, bounded
     residual race). If the check passes, delete the `.pre-migration-backup` file. If it fails, do
     **not** delete the backup file — abort the entire migration run immediately (raise, non-zero
     exit), print the backup file's path as the manual-recovery source, and do not proceed to Step 3
     verification or Step 5 retirement for *any* week, not just this one.

**Do NOT touch:** `writer.py` itself (reused unmodified, confirmed already satisfies "one lock per
batch" for every call site including this new one) and `_acquire_lock`/`_release_lock`/
`_lock_path_for` (private; this design deliberately avoids reaching into them — the rename-aside step
needs no lock of its own since it never mutates JSONL content, only relocates an intact file).

**Verify:** `test_migration_uses_write_lines_one_lock_per_week_batch`,
`test_current_week_shard_migrated_rows_precede_existing_live_rows` (both new, per test_plan.md).

### Step 3 — Full-corpus zero-data-loss verification (not sampled)

**Files:** `tools/agent-monitoring/migrate_tools_shards.py`

**Change:** Implement `verify_migration(pre_migration_line_count: int, shard_dir: Path,
current_week_pre_migration_live_count: int) -> dict` that:
- Re-reads every shard file this run touched (all week buckets plus the fallback file) and sums
  their line counts.
- Reports `original_total`, `migrated_total` (sum across shards), and
  `explained_delta = current_week_pre_migration_live_count` (the count of live rows that were
  already in the current week's shard *before* this migration ran, captured in Step 2's
  `live_snapshot` length) — asserts `migrated_total == original_total + explained_delta` **exactly**,
  never approximately, matching the ticket's own AC 7 wording ("report this distinction explicitly
  rather than diffing raw totals").
- Re-parses every line in every shard via `json.loads()` and confirms it round-trips to content
  identical (modulo trailing newline) to its source line in the original bucketing pass — full
  corpus, not sampled. Investigation.md's own timing measurement (0.552s to `json.loads` all 179,243
  real lines) is the direct evidence backing this "full-corpus is cheap enough, do it" decision
  (investigation.md Risk/Recommendation #4) — this plan adopts that recommendation as-is; no further
  justification needed.
- Confirms no line appears in two shards (a per-line identity check — e.g. a `(source_line_index)`
  tag carried through bucketing internally, verified unique across all output, discarded before
  writing since the ticket requires content-preservation, not an added tracking field).
- Returns a structured report dict this script prints and the implementer pastes into the ticket's
  Test Summary section verbatim (real run, real numbers, per ticket AC 7: "captured in Test Summary
  before the file is retired").

**Do NOT touch:** No production reader code (`generate_retro.py`, `validate.py`, `build_index.py`,
`query.py`) — this verification reads only the migration's own output shards, never routes through
or modifies any consumer's read path. That is child 3's exclusive scope per the ticket's Out of
Scope and investigation.md's Anti-Drift Hazards.

**Verify:** `test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved`,
`test_full_corpus_verification_reports_exact_not_approximate_counts` (both new, per test_plan.md).

### Step 4 — CLI entrypoint: orchestrate Steps 1-3 against the real corpus, strict ordering

**Files:** `tools/agent-monitoring/migrate_tools_shards.py`

**Change:** Implement `main()`:
1. Snapshot-read `agent-monitoring/tools.jsonl` once (`readlines()`), recording the exact count at
   that instant — never hardcode 179,096 or 179,243 (both already stale per investigation.md); the
   real count captured at this run's start is what gets reported and reconciled against.
2. For each week's `live_snapshot` needed by Step 2 Case B, capture it inside `write_week_bucket`
   itself at the moment that bucket is processed (not earlier) — minimizes the window between
   snapshot and rename.
3. Call `bucket_lines_by_week()` (Step 1), then `write_week_bucket()` once per resulting bucket key
   (Step 2) — if any bucket's write or reconciliation fails, abort immediately (see Step 2's failure
   path), do not proceed further.
4. Call `verify_migration()` (Step 3) against the just-written shard files.
5. Print the verification report. **This script does not itself call `git rm`** — retirement (Step 5)
   is a separate, explicit, human-run command gated on this script's verification report showing a
   pass, per this ticket's own explicit ordering requirement ("the zero-data-loss check must run and
   pass BEFORE `git rm` is executed, never after or in parallel" — never automate the two into one
   unreviewable action for a one-time, effectively-irreversible-from-the-working-tree step).
6. Run this script for real, once, against the actual `agent-monitoring/tools.jsonl` and
   `agent-monitoring/tools/` in this worktree. Capture its full stdout report — this is the ticket
   AC 7 evidence, pasted into the ticket's Test Summary section at Finalize.

**Do NOT touch:** No Make target, no cron/scheduled re-run mechanism — ticket Scope explicitly
requires this stays a manually-invoked one-time script (`python3
tools/agent-monitoring/migrate_tools_shards.py`), unlike `build_index.py`'s repeatable `make
agent-monitoring-index`.

**Verify:** Real run output captured for Test Summary; re-run
`pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py
tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_post_tool_hook.py -v` to
confirm the writer/lock-protocol and write-path regression surfaces are untouched (per
test_plan.md's Scoped Pytest Commands).

### Step 5 — Retirement: `git rm`, `.gitattributes`, and its 2 dependent test edits

**Files:** `agent-monitoring/tools.jsonl` (removed), `.gitattributes`,
`tests/integrity/test_merge_union_gitattributes.py`

**Change:** Only after Step 4's real run reports a passing verification (exact reconciliation, no
content mismatch, no aborted week):
- `git rm agent-monitoring/tools.jsonl`. Confirmed by investigation.md and ticket Out of Scope: this
  is a working-tree change only — `git log --follow -- agent-monitoring/tools.jsonl` continues to
  recover full history from prior commits; no git history is altered or deleted. Record this
  "supersedes the physical layout, does not delete the data" distinction explicitly in the ticket's
  Implementation Notes section (ticket file, at Finalize), per the ticket's own Assumptions section
  requiring it be unambiguous.
- Edit `.gitattributes` (read in full at investigation.md's "Current Behavior" section): remove the
  line `agent-monitoring/tools.jsonl merge=union`; keep `agent-monitoring/runs.jsonl merge=union`,
  `agent-monitoring/events.jsonl merge=union`, `agent-monitoring/tools/*.jsonl merge=union` (already
  added by child 1), and `tickets/working_log.csv merge=union` untouched.
- Edit `tests/integrity/test_merge_union_gitattributes.py`:
  `test_gitattributes_lines_present_for_all_four_union_merge_paths` — drop the `tools.jsonl`
  expectation from its path tuple (reduce to the 3 remaining legacy-file lines + confirm it no longer
  claims "four"; rename or adjust its docstring/name if the test scans a literal count).
  `test_gitattributes_line_present_for_shard_glob` — drop the assertion that the legacy
  `agent-monitoring/tools.jsonl merge=union` line is still present (its own docstring, per
  investigation.md's citation of `tests/integrity/test_merge_union_gitattributes.py:100-104`, already
  names this exact ticket as the one that retires that line — update the docstring to say it has now
  happened, past tense). Leave
  `test_concurrent_branch_appends_merge_without_conflict_markers` untouched (throwaway-repo based,
  unaffected).

**Do NOT touch:** Any other `.gitattributes` line; any other test in this file beyond the 2 named
above.

**Verify:** `test_tools_jsonl_removed_from_working_tree_after_migration`,
`test_gitattributes_no_longer_references_retired_tools_jsonl_path` (both new, per test_plan.md), plus
re-running the full `tests/integrity/test_merge_union_gitattributes.py -v` to confirm all pass
post-edit.

### Step 6 — Document the cross-worktree `git rm` merge-conflict runbook (decision 5)

**Files:** `tools/agent-monitoring/migrate_tools_shards.py` (header comment),
`tickets/inprogress/TCK-20260902-MONITORING-SHARD-MIGRATION.md` (`## Implementation Notes` section)

**Change:** Decision recorded (see Anti-Drift Notes for full rationale): this is a **documented, not
automated** runbook, mirroring this repo's own established precedent for exactly this class of
problem — `docs/REGISTRY.yaml`'s no-merge-driver situation, resolved by a documented `make
docs-registry` regeneration step rather than new tooling. Add:
- A short comment block at the top of `migrate_tools_shards.py` (near the module docstring) stating:
  this script performs a one-time, irreversible-from-the-working-tree `git rm` of
  `agent-monitoring/tools.jsonl`; any other worktree/branch that has not yet merged past this
  ticket's commit and is still appending to its own local copy of that file will produce a `CONFLICT
  (modify/delete)` when it later merges past this point (confirmed via `git merge-base
  --is-ancestor` against all other live worktrees at investigation time — `merge=union` does not
  apply to modify/delete conflicts). Resolution: take the deletion side (`git rm
  agent-monitoring/tools.jsonl` at the conflict), and if that other branch's interim rows need to be
  preserved, re-run this same script against that branch's pre-merge copy of `tools.jsonl` (or a
  targeted subset of its new lines) before finalizing the merge, rather than resurrecting the
  monolithic file.
- The same guidance, phrased for a ticket reader (not a script maintainer), added verbatim to this
  ticket's own `## Implementation Notes` section at Finalize.

**Do NOT touch:** Do not build automated multi-worktree coordination tooling (e.g. a pre-merge hook
that detects this specific conflict) — out of proportion for a one-time structural migration;
matches the `docs/REGISTRY.yaml` precedent of "document the recovery step," not "prevent the
scenario."

**Verify:** No automated test for this step (it is documentation) — manual review that both the
script comment and the ticket's Implementation Notes contain the runbook language before Finalize.

### Step 7 — Update `docs/agent-monitoring/schema.md`'s `tools.jsonl` section

**Files:** `docs/agent-monitoring/schema.md`

**Change:** The `## agent-monitoring/tools.jsonl` section's opening paragraph (confirmed at
investigation.md's "Docs Requiring Update", sourced from the file read at line ~341) currently reads:
*"The historical `agent-monitoring/tools.jsonl` (pre-cutover rows) remains present and unchanged,
frozen — it receives no further appends, pending a future migration ticket."* Rewrite this sentence
to state: the file has been retired from the working tree by this ticket; all its rows now live in
`agent-monitoring/tools/tools-YYYY-Www.jsonl` shard files (plus the `tools-unknown-week.jsonl`
fallback shard for the single record that carried no `ts`); its full history remains recoverable via
`git log --follow -- agent-monitoring/tools.jsonl`. Leave the per-record schema (the JSON example
block immediately following) unchanged — this ticket does not alter the record shape, only where
records physically live.

**Do NOT touch:** `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`,
`docs/ai/system_overview.md` §6 — investigation.md explicitly confirmed all three are deferred to
child 3 (they describe read-path semantics or high-level architecture, not this ticket's
write-side/physical-layout change); do not edit them in this ticket.

**Verify:** No automated test; manual read-through confirming the sentence no longer claims the file
"remains present."

### Step 8 — Accept and guard the interim `manifest.py`/`skill_usage_metric.py` breakage (decision 4)

**Files:** `tests/tools/test_agent_monitoring_manifest.py`, `tests/tools/test_skill_usage_metric.py`

**Change:** Decision recorded (full rationale in Anti-Drift Notes): **option (b)** — defer the fix to
child 3 (`TCK-20260902-MONITORING-SHARD-CONSUMERS`), do not modify `manifest.py` or
`skill_usage_metric.py` production code in this ticket. To satisfy test_plan.md's explicit
requirement that a deferred fix "must then be explicitly skipped/xfailed with a comment pointing at
child 3, not left to fail silently in CI," add `@pytest.mark.xfail(reason="agent-monitoring/
tools.jsonl retired by TCK-20260902-MONITORING-SHARD-MIGRATION; manifest.py/skill_usage_metric.py
not yet updated to read the shard directory — tracked by
TCK-20260902-MONITORING-SHARD-CONSUMERS (child 3), landing immediately after in this same batch per
SEQUENCE.md", strict=True)` directly above these 5 tests (confirmed exact names by reading both
files in full):
  - `tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`
  - `tests/tools/test_agent_monitoring_manifest.py::test_manifest_cli_reproducible_byte_identical_across_two_runs`
  - `tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call`
  - `tests/tools/test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`
  - `tests/tools/test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts`

`strict=True` so that if these tests unexpectedly *pass* (e.g. someone fixes the underlying issue
early), CI flags that as worth noticing rather than silently masking it.
`test_manifest_source_never_calls_full_file_read_methods` (confirmed by reading
`tests/tools/test_agent_monitoring_manifest.py` in full: a static-analysis/AST test, no file I/O) is
**not** in this list — it is unaffected by the file's removal and must keep passing unmodified.

**Do NOT touch:** `tools/agent-monitoring/manifest.py`, `tools/agent-monitoring/skill_usage_metric.py`
— confirmed by reading `manifest.py` in full (`_FILES_BY_SOURCE` hardcodes `"tools.jsonl"`,
`_scan_file()` does an unconditional `open(path, "rb")`) that these are child 3's exclusive fix
surface, not this ticket's. Do not touch `weight_sensitivity_check.py` or `record_events.py` either —
investigation.md confirmed these degrade silently (empty-data, not a crash) via existing
`.exists()` guards and are also child 3's scope, not requiring an `xfail` since they do not fail any
existing test.

**Verify:** `pytest tests/tools/test_agent_monitoring_manifest.py tests/tools/test_skill_usage_metric.py -v`
reports all 5 as `xfail` (not `error`, not `failed` uncaught), full command exits 0.

## Scope Guards

- Do not touch `query.py`, `generate_retro.py`, `validate.py`, `build_index.py`'s read paths — child
  3's exclusive scope, and this ticket's own Out of Scope.
- Do not repair, normalize, or coerce content of the 2 known off-schema lines or the 1 `ts`-less
  line beyond routing them to a correct bucket — route-only, content-preserving.
- Do not dedupe or re-key by `(run_id, seq)` — known historical `seq` collisions exist; the only
  ordering key is original append position within each `ts`-derived week bucket.
- Do not overwrite or truncate `agent-monitoring/tools/tools-2026-W36.jsonl` (or whichever week is
  live at run time) — append-only via the rename-aside + single `write_lines()` design in Step 2,
  never a destructive rewrite.
- Do not add a `docs/parity_ledger/` entry for this migration — established precedent (this
  investigation's own check and child 1's) is that pure agent-monitoring tooling tickets do not
  receive parity-ledger entries.
- Do not add a Make target or scheduled/cron re-run mechanism for this script — explicitly a
  one-time, manually-invoked operation per ticket Scope.
- Do not modify `manifest.py`, `skill_usage_metric.py`, `weight_sensitivity_check.py`,
  `record_events.py` — accepted as child 3's scope per decision 4 (Step 8).
- Do not build automated multi-worktree merge-conflict tooling — accepted as a documented runbook
  only per decision 5 (Step 6).
- Do not alter or delete git history — retirement is a working-tree `git rm` + commit only.
- Do not edit `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`,
  `docs/ai/system_overview.md` §6 — explicitly deferred to child 3 by investigation.md.

## Dependency Map

- Step 1 → Step 2 (write logic consumes the bucketing function's output).
- Step 2 → Step 3 (verification reads back what Step 2 wrote).
- Step 3 → Step 4 (orchestrator wires 1-3 together and is the vehicle for the real run).
- Step 4 → Step 5 (retirement is strictly gated on Step 4's real run reporting a verified pass — this
  is the ticket's single hardest ordering constraint; never reorder).
- Step 5 → Step 6 (the runbook note describes the consequence of Step 5's `git rm`; write it once
  Step 5 has actually happened, so the language is accurate, not speculative).
- Step 5 → Step 7 (the schema.md rewrite states the file "has been retired" — must follow, not
  precede, the actual retirement).
- Step 5 → Step 8 (the 5 `xfail`-marked tests only actually fail once `tools.jsonl` is gone; adding
  `xfail` before Step 5 would make them incorrectly report `xpass` since the file would still be
  present and the tests would still succeed for real).
- Steps 6, 7, 8 are independent of each other (all depend only on Step 5, not on one another) and may
  be done in any order once Step 5 is complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Every pre-cutover line present, content-preserved, in exactly one shard | Steps 1, 2, 3 | `test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved` |
| No duplication, no drop (line-count + content reconciliation) | Steps 1, 2, 3 | `test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved`, `test_full_corpus_verification_reports_exact_not_approximate_counts` |
| Records within each shard remain original chronological (append) order | Step 1 | `test_within_week_bucket_preserves_original_append_order` |
| Current-week shard has migrated historical rows before live rows, correct relative order | Step 2 | `test_current_week_shard_migrated_rows_precede_existing_live_rows` |
| `agent-monitoring/tools.jsonl` no longer exists in working tree; history recoverable via `git log --follow` | Step 5 | `test_tools_jsonl_removed_from_working_tree_after_migration` |
| `.gitattributes` no longer references retired path; shard-glob line remains | Step 5 | `test_gitattributes_no_longer_references_retired_tools_jsonl_path` |
| Zero-data-loss verification run against the real historical file captured in Test Summary before retirement | Steps 3, 4 | `test_full_corpus_verification_reports_exact_not_approximate_counts` + real-run transcript pasted into ticket Test Summary |

## Anti-Drift Notes

**Verification-before-retirement ordering is absolute.** Step 4's real migration run and its
verification report must complete and show a passing reconciliation **before** Step 5's `git rm` is
executed — never after, never in parallel, never assumed-to-pass-and-fixed-up-later. This is a
64MB/179,243-line file that, once removed from the working tree, is only recoverable via git history
inspection (`git log --follow`, `git show`) — not a casual `git checkout` of a currently-tracked
path. If Step 4's verification fails for any reason (a week bucket's reconciliation check fails, a
content mismatch is found, an exception is raised), **stop** — do not proceed to Step 5 under any
circumstance, including "it's probably just the fallback bucket" or "I'll fix .gitattributes anyway
since that part's independent." The whole point of the strict Step 4 → Step 5 dependency is that
retirement is the one step in this ticket that cannot be cheaply undone by re-running the script.

**The current-week shard merge (Step 2 Case B) is the single highest-risk piece of this ticket.**
Re-read Step 2's algorithm before implementing: `write_lines()` is append-only and the ticket
requires exactly one `write_lines()` call per week bucket, which together force the
rename-aside-then-single-combined-append design — do not "simplify" this into two separate
`write_lines()` calls (one for historical, one to restore the live suffix) because that both fails
`test_migration_uses_write_lines_one_lock_per_week_batch`'s exact-once assertion and reopens a real
race window between the two calls. Do not skip the post-write reconciliation check in step 5 of that
algorithm — it is the only thing that guarantees the pre-existing live rows (this session's own
already-recorded tool-call history) were not lost, and its failure path (keep the backup file, abort
before Step 3/5) is load-bearing, not optional cleanup.

**Bounded, documented residual race (do not attempt to fully eliminate it):** in the narrow window
between Step 2's `os.replace()` (rename-aside) and its subsequent `write_lines()` call, a genuinely
concurrent writer to the *same* current-week shard path (a different, simultaneously-running Claude
Code session in a *different* worktree already past child 1's cutover, mid-tool-call in the exact
same UTC ISO week) could create a new file at that path before this script's `write_lines()` call
runs, causing that writer's row to land ahead of the migrated historical block rather than
chronologically after it. This is accepted as a narrow, documented limitation (not solved with a
second nested lock, which would risk a reentrant-deadlock against `write_lines()`'s own internal
lock acquisition for the same path) precisely because: (a) this migration runs once, deliberately, in
a single session controlling its own timing; (b) the reconciliation check guarantees no *data loss*
occurs even in this scenario, only a possible ordering edge case for that one concurrent row; (c)
investigation.md's own Risk #5 already frames this class of race as an accepted "snapshot as of this
moment" limitation, not a hard correctness requirement to engineer away.

**Decision 3 — fallback bucket for the single `ts`-less line: `agent-monitoring/tools/
tools-unknown-week.jsonl`, accepted as investigation.md recommended.** This reuses the
already-established, same-codebase convention (`generate_retro.py::iso_week()`'s documented
fail-to-`"unknown"` pattern) as a dedicated shard filename rather than inventing a new fallback (e.g.
file-mtime-based week inference, rejected because it would fabricate false-precision week data for a
genuinely un-dated record). With real data this bucket holds exactly 1 row.

**Decision 4 — `manifest.py`/`skill_usage_metric.py` interim breakage: option (b), deferred to
child 3, recorded as an explicit `xfail`, not silently accepted.** Chosen over option (a) (expanding
this ticket's scope to patch `manifest.py`'s `_FILES_BY_SOURCE`) because: (1) child 1's own ticket
text (`tickets/done/TCK-20260902-MONITORING-SHARD-WRITE-PATH.md:82-83`, read verbatim) already
establishes and uses this exact reasoning and this exact phrase for a related gap — *"until child
ticket 3 lands — acceptable because child tickets 2/3 land immediately after per SEQUENCE.md, not as
a standalone release"* — this ticket is not inventing a new precedent, it is following one the
project already set one ticket ago in the same batch; (2) `SEQUENCE.md`
(`tickets/todos/agent-monitoring-weekly-sharding/SEQUENCE.md`, read verbatim) formally encodes child
3 as depending on this ticket and landing immediately after; (3) confirmed operationally: all 3
child tickets are being implemented back-to-back in this same session, on this same branch
(`worktree-monitoring-tools-weekly-sharding`), before any PR is opened — the interim red-test window
exists only inside this session's local working tree, never reaches CI or a reviewer; (4) patching
`manifest.py` here, even narrowly, still means touching consumer-migration code that the ticket's own
Related Code Areas and Out of Scope sections do not name, which is exactly the kind of "fix the glob
while I'm in here" scope creep investigation.md's own Anti-Drift Hazards warns against resisting.
**The 5 exact tests expected to fail in the interim** (all real-corpus tests hitting the now-missing
file) are listed in Step 8 verbatim; they must be re-verified passing again (with the `xfail` markers
removed) as part of child 3's own Finalize, before this branch's PR is opened. If, for any reason,
child 3 does not land immediately after in this same session, **do not open a PR** with these `xfail`
markers still in place — that would ship the interim gap externally, which this decision explicitly
does not authorize.

**Decision 5 — cross-worktree `git rm` modify/delete conflict: documented runbook, not automated
tooling.** Confirmed real (investigation.md's `git merge-base --is-ancestor` check against all 5
other live checkouts, none past child 1's cutover commit) — this is not hypothetical. Resolved the
same way this repo already resolves the structurally identical `docs/REGISTRY.yaml` no-merge-driver
situation: a documented recovery step (Step 6's script comment + ticket Implementation Notes), not
new automated coordination tooling. Do not silently assume this risk away, and do not over-build a
solution disproportionate to a one-time structural migration.

**Line count is a moving target — never hardcode it.** Both the ticket (179,096) and this
investigation (179,243) are already-stale snapshots by the time an implementer runs the script.
Step 4's `main()` must read the real count at its own run time and report that real number, not
either number written down in any prior document, including this plan.

## Deviations

Recorded during implementation (`tickets/inprogress/TCK-20260902-MONITORING-SHARD-MIGRATION.md`'s
Implementation Notes has the full text; summarized here):

1. **Function-signature extension (behavior/intent preserved).** `write_week_bucket()` returns
   `tuple[bool, list[str]]` instead of the plan's sketched bare `bool`, and `verify_migration()`
   takes `(source_lines, buckets, shard_dir, live_snapshots)` instead of
   `(pre_migration_line_count, shard_dir, current_week_pre_migration_live_count)`. Necessary to
   thread the actual live-snapshot *content* (not just a count), captured at the exact moment each
   bucket is processed, through to a real content-preservation check — the plan's own "minimizes
   the window between snapshot and rename" requirement implies this content needs to flow
   somewhere. Every substantive constraint (one `write_lines()` call per bucket, rename-aside
   algorithm, exact reconciliation, full-corpus verification, no dedup, no reorder) is implemented
   exactly as the plan specified.

2. **Bug found and fixed, not anticipated by the plan.** `write_lines()`'s `_acquire_lock()`
   creates the lock file before `write_lines()`'s own internal `mkdir()` runs, so the shard
   directory must already exist before the *first* call for a brand-new week — otherwise
   `write_lines()` returns `False` silently (per its own never-raise contract) instead of writing.
   `write_week_bucket()` now does `target_path.parent.mkdir(parents=True, exist_ok=True)` up front,
   matching the same pre-existing pattern `post_tool_hook.py` already uses ahead of its own
   `write_line()` call. This is a real, necessary fix, not scope creep — the script would not have
   functioned without it.

3. **Two new integration tests in `tests/tools/test_migrate_tools_shards.py`
   (`test_every_pre_cutover_line_lands_in_exactly_one_shard_content_preserved`,
   `test_full_corpus_verification_reports_exact_not_approximate_counts`) now skip (`pytest.skip`)
   once `agent-monitoring/tools.jsonl` no longer exists**, rather than asserting against it forever.
   Their design (per test_plan.md) assumed the real historical file would remain available to copy
   from at test-run time; after this same ticket's own retirement step, that premise is
   permanently false by design, not a regression. Skipping (not xfail, not deletion) keeps this
   documented and visible rather than silently vanishing; they already ran and passed for real,
   pre-retirement (captured in the ticket's Test Summary).

4. **Discrepancy flagged by the implementer instead of silently worked around — now resolved by the
   orchestrating session, post-Implement.** plan.md's Decision 4/Step 8 named exactly 5 tests as the
   accepted interim `xfail` gap (`manifest.py`/`skill_usage_metric.py`'s real-corpus tests).
   Post-retirement testing surfaced 2 additional real-corpus test failures in
   `tests/tools/test_generate_retro.py` (`test_correlation_real_corpus_produces_a_real_number`,
   `test_parity_index_readpath_call_count_matches_real_corpus_state`), independently reproduced and
   confirmed to share the identical root cause: `generate_retro.DEFAULT_TOOLS_FILE` points at the
   now-retired single-file path; `load_jsonl()` gracefully returns `[]` (no crash) but these 2
   specific tests hard-assert nonzero/exact values derived from that empty read. `generate_retro.py`
   itself remains untouched (still out-of-scope/child-3's-job) — only the 2 test functions gained
   the exact same `xfail(strict=True, ...)` pattern as the original 5, with a reason string citing
   the same `TCK-20260902-MONITORING-SHARD-MIGRATION` → `TCK-20260902-MONITORING-SHARD-CONSUMERS`
   handoff. **Decision 4's accepted-interim-gap list is hereby corrected from 5 to 7 tests total** —
   the additional 2 are covered by the exact same rationale already recorded above (same root cause,
   same "child 3 fixes it, markers removed before any PR opens" gate), not a new decision, just a
   scoping gap in the original investigation/test_plan's real-corpus test enumeration. The full
   corrected list of 7:
   - `tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`
   - `tests/tools/test_agent_monitoring_manifest.py::test_manifest_cli_reproducible_byte_identical_across_two_runs`
   - `tests/tools/test_agent_monitoring_manifest.py::test_build_manifest_reproducible_byte_identical_direct_call`
   - `tests/tools/test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`
   - `tests/tools/test_skill_usage_metric.py::test_live_corpus_matches_independently_derived_counts`
   - `tests/tools/test_generate_retro.py::test_correlation_real_corpus_produces_a_real_number`
   - `tests/tools/test_generate_retro.py::test_parity_index_readpath_call_count_matches_real_corpus_state`

   All 7 must have their `xfail` markers removed by child ticket 3 before any PR from this branch
   opens — same hard gate as before, just a corrected count.
