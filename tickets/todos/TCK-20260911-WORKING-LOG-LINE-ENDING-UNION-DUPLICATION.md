---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
phase: open
date: 2026-09-11
tags: [data-quality, process-improvement]
---

# TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION

## Title
Mixed CRLF/LF writers make `merge=union` duplicate `tickets/working_log.csv` blocks on most batch merges

## Status
OPEN

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
- [ ] The mechanism is confirmed or refuted for Batch A and Batch C, with evidence recorded (not assumed
      from #160).
- [ ] Every writer of a `merge=union` file produces LF; the closure script's fix has a unit test.
- [ ] `.gitattributes` enforces LF for the `merge=union` paths, verified by committing a CRLF row in a
      scratch repo or fixture and observing normalization.
- [ ] An integrity test fails on any `\r` in a `merge=union` file and passes on current `main`.
- [ ] A reproduction test shows that two branches rewriting the same appended rows with different line
      endings no longer produce a duplicate block after the fix.
- [ ] The W36 `tools.jsonl` allowlisted block is either remediated or explicitly shown to be a different
      mechanism.

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

## Test Summary

## Files Changed

## Completion Summary
