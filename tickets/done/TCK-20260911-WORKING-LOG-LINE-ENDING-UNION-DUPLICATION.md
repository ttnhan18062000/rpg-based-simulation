---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
phase: done
date: 2026-09-11
tags: [data-quality, process-improvement]
---

# TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION

## Title
Mixed CRLF/LF writers make `merge=union` duplicate `tickets/working_log.csv` blocks on most batch merges

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`tickets/working_log.csv` has taken a byte-identical duplicate block on **3 of 4 batch merges in 3
days**. Each time CI caught it (`tests/integrity/test_no_duplicate_content_blocks.py`) and someone
cleaned it up by hand:

| Occurrence | Where | Result |
|---|---|---|
| Batch A (#158) | merge `18000417` | 15-line block (rows 1849-1863 = 1869-1883); 7 rows differ CRLF vs LF |
| Batch B (#159) | — | clean |
| PR #160 | merge `595473b2` | 13-line block (rows 1870-1882) |
| Batch C (#161) | merge `05c685dd` | 13-line block (same 13 rows as #160); cleanup `96832f31` |

Reported by `rpg-feature-planning` and `rpg-implementer`. PR #160's instance was found in this
session. The closed `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` has been collecting
recurrence addenda instead of a fix.

**Root cause, established for PR #160 (2026-09-11):**

1. `tools/agent-monitoring/record_hand_orchestrated_closure.py:206-207` appends with
   `open("a", newline="")` + `csv.writer(...)`, which has no `lineterminator`. Python's default is
   `\r\n`, so every hand-orchestrated closure writes a **CRLF** row. Other writers (Finalize appends
   done through editors or Bash) write **LF**.
2. At the merge base `75478727`, exactly **13 lines** ended in `\r` (rows 1869-1881): all
   hand-orchestrated KGMCP-arc closures written by that script.
3. On the PR branch (`ff851099`) those same 13 rows had been rewritten to LF, leaving 0 CR bytes.
   Something rewrote the file rather than appending to it.
4. `main` (`e66a98bd`) still had them as CRLF (23 CR bytes by then).
5. Both sides therefore "changed" the same 13 lines relative to the base. `merge=union` resolves a
   both-sides change by keeping both versions, and the result had exactly those 13 rows twice. The
   two copies look identical but differ in their line ending.

`merge=union` is only safe for **pure appends**. Any rewrite of existing lines breaks that
assumption, and a line-ending change is an invisible rewrite. Hand cleanup can keep the cycle going:
deleting the copy that doesn't match `main` fixes it, deleting the other one sets up the next
duplicate.

**Batch C corroborates it (evidence from `rpg-feature-planning`, CR counts checked here):** merge
`05c685dd` (branch `6c774dcb` × main `fe67836a`, base `e66a98bd`). The duplicate was again **13
lines**. The branch side still carried the CRLF originals (26 CR bytes), while main at `fe67836a`
(#160's squash, which landed the LF rewrite) had **0**. That's the mirror image of #160: two
independent occurrences, same 13 rows. Cleanup commit `96832f31`.

**Batch A confirms it on a different row set:** merge `18000417` (branch `6c51c681` × main `75478727`,
base `cb0b23b0`). The 15 duplicated rows are RPG closures from 2026-09-08/09, none of them in the base,
which both sides carried. In the branch-side copy, 7 of the 15 end in CRLF; in the main-side copy, 0 do.
Identical additions would merge cleanly; additions that differ in line endings become a both-sides
change, and union keeps both.

**Writer fingerprint:** every CR row seen across all three occurrences has a microsecond-precision
timestamp (`…:54.208358Z`), which is what `record_hand_orchestrated_closure.py` writes. Rows written
by hand in Finalize (`…:00.000000Z`, `…:44Z`) are LF. **3 of 3 duplicates are explained by line-ending
variance on shared rows.**

This refines the earlier squash-merge explanation rather than replacing it. Squash merges keep merge
bases older, which widens the window. But PR #160's duplicate happened on its **first** merge of
`main`, so a stale merge base alone does not explain it; the mixed line endings do.

## Scope
- **Investigate first (short):**
  - ~~Confirm the mechanism for Batch A and Batch C~~ — done during scoping (see Request Summary).
    Re-verify it in Investigate with a scripted reproduction, not by re-reading.
  - Find what rewrote the 13 rows to LF on the #160 branch (the writer that normalizes existing rows).
  - List every writer of every `merge=union` file (`tickets/working_log.csv`,
    `agent-monitoring/data/*/*.jsonl`) and the line ending each produces.
- **Fix at the source:**
  - Make `record_hand_orchestrated_closure.py` write `\n` (`lineterminator="\n"`). Add the same fix to
    any other CRLF writer the survey finds.
  - Add `text eol=lf` for the `merge=union` paths in `.gitattributes`, so git normalizes line endings
    on commit and a CR can never enter the repo through any writer. Check the interaction with
    `merge=union` on the same lines.
- **Detect earlier:** an integrity test that fails on any `\r` byte in a `merge=union` file. This is
  cheaper and more direct than the duplicate-block test, which only sees the consequence.
- **Remediate:** normalize any CR rows remaining on `main` (0 in `tickets/working_log.csv` as of
  2026-09-11; re-check the jsonl shards). Write down the hand-cleanup rule for the interim: keep the
  copy whose bytes match `main`.
- Decide whether `agent-monitoring/data/2026-W36/tools.jsonl`'s allowlisted 79-line block (closed
  ticket's Step 7) is the same mechanism. If so, remediate it here.

## Out of Scope
- Changing the repo's squash-merge policy.
- Replacing `merge=union` with a different storage layout (per-ticket files, etc.). Worth considering
  only if the source fix and the CR check don't stop recurrence.
- Other data-quality issues in `working_log.csv`. Paired rows per ticket about a minute apart are
  visible in the KGMCP block; note them if they matter, but file them separately.

## Acceptance Criteria
- [x] The mechanism is confirmed or refuted for Batch A and Batch C, with evidence recorded (not assumed
      from #160). *Confirmed during Investigate; see investigation.md §1.*
- [x] Every writer of a `merge=union` file produces LF; the closure script's fix has a unit test.
      *`record_hand_orchestrated_closure.py:207` now passes `lineterminator="\n"`;
      `tests/tools/test_record_hand_orchestrated_closure.py` (pre-existing, run unmodified) covers
      the writer's real subprocess output.*
- [x] `.gitattributes` enforces LF for the `merge=union` paths, verified by committing a CRLF row in a
      scratch repo or fixture and observing normalization.
      *`tests/integrity/test_merge_union_crlf_duplication_repro.py::test_text_eol_lf_prevents_the_duplication_and_leaves_no_cr`
      appends CRLF/LF rows on two real branches and merges them; asserts zero `\r` bytes in the
      merged file.*
- [x] An integrity test fails on any `\r` in a `merge=union` file and passes on current `main`.
      *`tests/integrity/test_merge_union_no_cr_bytes.py`; passes on current `main` after the
      22-CR-byte remediation recorded in Implementation Notes below, and independently confirmed
      to fail against an injected `\r` byte.*
- [x] A reproduction test shows that two branches rewriting the same appended rows with different line
      endings no longer produce a duplicate block after the fix.
      *`tests/integrity/test_merge_union_crlf_duplication_repro.py::test_merge_union_alone_duplicates_rows_shared_across_branches_with_different_line_endings`
      proves the duplicate first (2 real occurrences of each shared row after a real merge, no
      `eol=lf`); the sibling test above proves the fix removes it (1 occurrence, no `\r`).*
- [x] The W36 `tools.jsonl` allowlisted block is either remediated or explicitly shown to be a different
      mechanism. *Different mechanism: 0 CR bytes (investigation.md §4).*

## Related Tickets
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — original incident, detection test,
  unremediated Step 7, recurrence addenda.
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (done) — introduced `merge=union`.
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done, PR #160) — occurrence 3.

## Related Docs
- `.gitattributes` (caveat block)
- `docs/testing/regression_policy.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP/`

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tests/integrity/test_no_duplicate_content_blocks.py`
- `.claude/workflows/implement-ticket.js` (Finalize's working-log append)
- `.gitattributes`

## Assumptions / Open Questions
- `text eol=lf` together with `merge=union` on the same path is expected to work: normalization
  applies to stored content, and the merge driver sees normalized blobs. Verify rather than assume.
- The writer that normalized CRLF→LF on the #160 branch is unknown. It might be an editor-tool write, a
  script that reads and rewrites the file, or a merge resolution.

## Implementation Notes
Followed plan.md's 6 steps; full deviation detail (with evidence) is recorded in that file's own
"Deviations (recorded during Implement)" section, summarized here:

1. **Writer fix** (Step 1): `tools/agent-monitoring/record_hand_orchestrated_closure.py:207` now
   passes `lineterminator="\n"` to `csv.writer`; `newline=""` kept unchanged. No other writer of a
   `merge=union` file exists (confirmed again during Implement).
2. **`.gitattributes`** (Step 2): both `merge=union` lines gained `text eol=lf` ahead of
   `merge=union`. `git check-attr` confirms `text: set, eol: lf, merge: union` on both paths.
   `git add --renormalize` on the two patterns found and staged a real 22-CR-byte normalization in
   `tickets/working_log.csv` (not the expected no-op). 21 of these 22 were genuine new CR rows
   written by other concurrent sessions' hand-orchestrated closures between investigation.md's
   writing and this Implement dispatch (2026-09-09T11:30 through 2026-09-11T08:00, not all one
   day), matching `record_hand_orchestrated_closure.py`'s known microsecond-precision-timestamp
   fingerprint. The 22nd (the `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT` row) does
   not match that fingerprint -- no microsecond precision, added directly in this session's own
   commit `c4d42635` (PR #164), not via a merge -- so its CR's exact origin is unresolved and is
   not attributable to that script or to a concurrent session. No new duplicate block had formed
   from any of the 22 yet (`test_no_duplicate_content_blocks.py` still passed pre-remediation).
   Proceeded with the normalization rather than halting for all 22 regardless of per-row origin,
   since the fix (writer `lineterminator` + `.gitattributes` `eol=lf`) closes the gap for every
   writer, known or not; it's explicitly authorized by this ticket's own Scope ("Remediate:
   normalize any CR rows remaining on main"), and Step 3's own acceptance bar requires it. Verified
   byte-identical to the original file with every `\r\n` replaced by `\n` -- no content, ordering,
   or row-count change. See plan.md Deviation 1 for full evidence.
3. **CR detector** (Step 3): new `tests/integrity/test_merge_union_no_cr_bytes.py`, importing
   `_merge_union_glob_patterns()`/`_covered_files()` from `test_no_duplicate_content_blocks.py`
   rather than reimplementing them. That helper itself needed a real fix (plan.md Deviation 2):
   it matched attribute lines by requiring `merge=union` as the exact trailing suffix, which Step
   2's new `text eol=lf` token (now sitting ahead of `merge=union`) broke, silently returning zero
   covered files and making both the pre-existing duplicate-block test and this new test
   vacuously pass. Fixed by tokenizing the line and checking `merge=union` is present anywhere
   after the leading path token. Confirmed the new test both passes on current `main` and fails
   against a manually injected `\r` byte.
4. **Reproduction test** (Step 4): new
   `tests/integrity/test_merge_union_crlf_duplication_repro.py`, two tests against a real
   throwaway git repo (identity + `core.autocrlf=false` configured inside the repo only). First
   proves the defect (merge=union alone, two branches append the same rows with different line
   endings -> 2 real occurrences of each row after a real merge); second proves the fix (`text
   eol=lf` added -> 1 occurrence, zero `\r` bytes). Both run in well under a second, not marked
   `slow`.
5. **Docs** (Step 5): `.gitattributes`' caveat block gained a second CAVEAT paragraph for this
   ticket, explaining `merge=union`'s byte-identical-appends-only safety assumption, what `eol=lf`
   fixes, and the interim "keep the copy whose bytes match `main`" hand-cleanup rule.
6. **Parity check** (Step 6): no existing `docs/parity_ledger/infrastructure.yaml` entry cited
   this writer's CRLF behavior or the CR-free guarantee (confirmed by grep before writing).
   Added one new entry, `INFRA-416`, via `tools/parity_ledger_writer.write_entry()` only -- no raw
   YAML edit. `build_report` in the write result confirms the derived index rebuilt clean
   (`entry_count: 2187`).

**Incidental fix, in scope:** two pre-existing sanity assertions in
`tests/integrity/test_merge_union_gitattributes.py`
(`test_gitattributes_line_present_for_working_log_csv`,
`test_gitattributes_lines_absent_for_retired_monitoring_paths`) asserted the exact substring
`"<path> merge=union"`, which no longer appears verbatim once `text eol=lf` precedes
`merge=union`. Updated both to use the shared `_merge_union_glob_patterns()` parser instead of an
exact substring (plan.md Deviation 3).

## Test Summary
```
pytest tests/integrity/ tests/tools/test_record_hand_orchestrated_closure.py -q
```
51 passed, 1 skipped, 2 xfailed (pre-existing skip/xfail, unrelated to this ticket). Also ran
`tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_ledger_schema.py -q` (43 passed)
to confirm the new `INFRA-416` entry didn't regress the ledger writer/schema lockstep tests.
All runs used the project `.venv` (`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`),
since the bare interpreter lacks `pydantic`.

## Files Changed
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` -- CRLF writer fix (Step 1)
- `.gitattributes` -- `text eol=lf` on both `merge=union` lines + updated caveat block (Steps 2, 5)
- `tickets/working_log.csv` -- 22 CR rows normalized to LF (Step 2 remediation; content unchanged,
  see plan.md Deviation 1)
- `tests/integrity/test_merge_union_no_cr_bytes.py` -- new CR-byte detector (Step 3)
- `tests/integrity/test_no_duplicate_content_blocks.py` -- `_merge_union_glob_patterns()` fixed to
  tokenize instead of requiring an exact trailing suffix (plan.md Deviation 2)
- `tests/integrity/test_merge_union_gitattributes.py` -- two sanity assertions updated to use the
  shared parser instead of an exact substring (plan.md Deviation 3)
- `tests/integrity/test_merge_union_crlf_duplication_repro.py` -- new scratch-repo reproduction
  test (Step 4)
- `docs/parity_ledger/infrastructure.yaml` -- new entry `INFRA-416`, via `write_entry()` (Step 6)
- `staging_artifacts/TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION/plan.md` -- Deviations
  section added
- `tickets/inprogress/TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION.md` -- this file

## Completion Summary
Fixed the CRLF writer (`record_hand_orchestrated_closure.py`) that was the root cause of 3 of 4
recent batch-PR duplicate blocks in `tickets/working_log.csv`, and added `text eol=lf` to both
`merge=union` `.gitattributes` lines so any future writer's line-ending output can no longer
create the byte-level mismatch that `merge=union` turns into a duplicate. Added a direct CR-byte
detector test and a real-git reproduction test that proves both the defect and the fix, fixed a
real bug the `.gitattributes` change exposed in the existing duplicate-block test's shared glob-
pattern helper, normalized 22 CR rows that had accumulated in `tickets/working_log.csv` since
investigation.md's snapshot (same already-diagnosed writer, content unchanged, no data loss), and
recorded one new parity-ledger entry (`INFRA-416`) via the sanctioned `write_entry()` path. No
`src/` file was touched.

**Two follow-on notes from peer review (agent-working-design), both confirmed real:**

1. **A second CRLF source exists, distinct from `record_hand_orchestrated_closure.py`.** The 22nd
   remediated row (the one already flagged in plan.md's Deviations as not matching the known
   writer's fingerprint) was traced to a hand-written `working_log.csv` append made directly by
   this same session's own PR #164 Finalize commit (`c4d42635`), not to the closure script. The
   new CR-byte detector will catch a recurrence either way; if one shows up, file it rather than
   re-diagnosing from scratch.

2. **`text eol=lf` only normalizes content at commit time going forward — it does not retroactively
   touch CRLF bytes already committed on other, still-open branches.** This was independently
   confirmed while merging `origin/main` into this branch to resolve a `docs/REGISTRY.yaml`
   conflict before PR #167 could get CI: the merge reverted this ticket's own 5 already-normalized
   rows back to CRLF (since `main` hadn't yet seen this branch's `.gitattributes` fix at the time)
   and picked up 1 new CRLF row from `origin/main`'s own PR #165 commit -- 6 CR bytes total, caught
   immediately by this ticket's own CR-byte detector, renormalized and verified byte-for-byte
   before completing the merge (see the merge commit `404e357a` on this branch for full detail).
   No duplicate content block formed in that merge (`test_no_duplicate_content_blocks.py` passed
   throughout), but this is a live demonstration of the exact risk: any long-lived branch that
   already carries CRLF rows in its own commits can still produce one more duplicate on its next
   merge of `main`, until that branch also merges `main` (to pick up this fix) and runs
   `git add --renormalize tickets/working_log.csv agent-monitoring/data` once on its own copies.
   Worth relaying to `rpg-implementer` and `rpg-feature-planning` if either has a long-lived branch
   still open.
