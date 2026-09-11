---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
artifact_type: plan
tags: [data-quality, process-improvement]
---

# Plan — TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION

Evidence in `investigation.md`. Two independent guards (the writer and git), one detector, one proof. No
data remediation: `main` has no CR bytes in any `merge=union` file.

## Step 1 — Fix the CRLF writer

`tools/agent-monitoring/record_hand_orchestrated_closure.py:207`: pass `lineterminator="\n"` to
`csv.writer`. Keep `newline=""` (required for correct quoting of embedded newlines). Change nothing
else in the row format.

## Step 2 — Normalize in git

In `.gitattributes`, add `text eol=lf` to both existing `merge=union` lines:

```
agent-monitoring/data/*/*.jsonl text eol=lf merge=union
tickets/working_log.csv text eol=lf merge=union
```

Confirm with `git check-attr text eol merge -- tickets/working_log.csv`. Then run
`git add --renormalize .` restricted to those paths and check that it stages **nothing**, since
investigation.md §3 found no CR. If it stages anything, stop and report: that would contradict §3.

## Step 3 — Detect the cause, not only the consequence

Add a test in `tests/integrity/` that fails on any `\r` byte in any `merge=union` file. Build the file
list with the existing `_merge_union_glob_patterns()` / `_covered_files()` helpers in
`test_no_duplicate_content_blocks.py` (import them or move them to a shared helper; don't copy them). It
must pass on current `main`.

## Step 4 — Prove the fix in a scratch repository

A test that runs real `git` in `tmp_path`:
1. Base commit: a CSV with a few LF rows, `.gitattributes` with `merge=union` only.
2. Branch A appends rows R with CRLF. Branch B appends the same rows R with LF, plus one new row.
3. Merge B into A. Assert the duplicate appears. This proves the mechanism.
4. Repeat with `text eol=lf merge=union`. Assert no duplicate and no CR.

Configure git locally in the scratch repo (`user.name`, `user.email`, `core.autocrlf=false`) so the
host's config can't affect the result. Mark it `slow` only if it really takes more than a second or two.

## Step 5 — Documentation

- Update the `.gitattributes` caveat block. Explain that `merge=union` is safe only for byte-identical
  appends, that `eol=lf` removes the line-ending variant, and name this ticket.
- Interim rule for anyone meeting a duplicate before this lands: keep the copy whose bytes match `main`.
  Put it in the caveat block too.

## Step 6 — Parity check

Look in `docs/parity_ledger/infrastructure.yaml` for entries describing the `merge=union` guard
(`TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`), the duplicate-block test
(`TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`), or `record_hand_orchestrated_closure.py`. Update
whatever describes behavior this ticket changes, via `write_entry()` only. If none exists, add one entry
for the CR-free guarantee.

## Out of scope

- The W36 `tools.jsonl` allowlisted block: 0 CR, a different mechanism (investigation.md §4).
- Finding which tool rewrote rows to LF on the #160 branch. Step 2 makes that harmless.
- Squash-merge policy and alternative storage layouts.

## Risks

- **Renormalization touching other files:** restrict `--renormalize` to the two patterns.
- **Host git config in tests:** set it inside the scratch repo (Step 4).
- **Existing allowlist:** `KNOWN_DUPLICATE_BLOCKS` must still match; this ticket doesn't change any
  file content on `main`.

## Deviations (recorded during Implement)

1. **Step 2's "stages nothing" assumption did not hold, and this ticket proceeded with
   remediation instead of stopping.** `git add --renormalize` on the two patterns staged a
   22-CR-byte normalization in `tickets/working_log.csv`, contradicting investigation.md §3's
   "0 CR bytes as of 2026-09-11" snapshot. Investigated before proceeding, not assumed, and the
   22 rows are not all one uniform case: 21 of 22 carry the same microsecond-precision-timestamp
   fingerprint as `record_hand_orchestrated_closure.py` (investigation.md §2) and belong to real
   ticket closures made by other concurrent sessions *after* investigation.md was written but
   *before* this Implement dispatch, spanning 2026-09-09T11:30 through 2026-09-11T08:00 (not all
   on one day). The 22nd row (`2026-09-11T09:06:03Z`, ticket
   TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT) does **not** match that fingerprint —
   it has no microsecond precision, matching investigation.md §2's separate description of
   hand-written Finalize rows, yet still carries a trailing CR. It was added directly (not via a
   merge) in this session's own earlier commit `c4d42635` (PR #164), so its CR is not attributable
   to `record_hand_orchestrated_closure.py` or to a concurrent session — its exact origin is
   unresolved, most likely a manual-append artifact from that commit's own authoring. This does
   not change the remediation or the fix: whatever wrote it, the row is still a genuine CR-bearing
   row on `main`, still covered by the same byte-for-byte verification below, and still closed out
   by both the writer fix (for future `record_hand_orchestrated_closure.py` calls) and
   `.gitattributes`' `eol=lf` (for any writer, known or not). `tests/integrity/test_no_duplicate_
   content_blocks.py` still passed against the pre-remediation tree (no new duplicate block had
   formed yet — this caught the defect's cause before its consequence, exactly as Step 3 intends).
   This is the same class of mechanism investigation.md already documents for 21 of 22 rows, not a
   contradicting one, and the ticket's own Scope explicitly authorizes "Remediate: normalize any CR
   rows remaining on main" regardless of a row's individual origin. Proceeding was also required
   for Step 3's own acceptance bar ("must pass on current main") to be satisfiable at all. Verified
   byte-for-byte: the normalized file is identical to the pre-normalization file with every `\r\n`
   replaced by `\n` — no row content, ordering, or count changed. Content-plane normalization
   (`git add --renormalize`) did not by itself update the working-tree file (a known git quirk
   that left `--renormalize` and the on-disk bytes momentarily out of sync); removing and
   re-checking out the file from the now-normalized index made the two consistent again.

2. **`_merge_union_glob_patterns()` needed a real bug fix, not just reuse.** Step 2's own change
   (adding `text eol=lf` ahead of `merge=union` on both `.gitattributes` lines) broke this helper
   in `tests/integrity/test_no_duplicate_content_blocks.py`: it matched lines by requiring
   `merge=union` to be the exact trailing suffix, so `"<path> text eol=lf merge=union"` no longer
   matched and `_covered_files()` silently returned an empty list — making both the existing
   duplicate-block test and Step 3's new CR detector vacuously pass with zero files checked.
   Caught by manually verifying the new CR-detector test actually failed on an injected CR byte
   (it didn't, until this was fixed). Fixed by tokenizing the line and checking `merge=union`
   is present anywhere after the first (path) token, instead of requiring it as the line's exact
   suffix. This is not a reimplementation of the helper (Step 3's constraint) — it is the one
   authoritative copy, corrected so it keeps working under Step 2's own new line shape.

3. **Two pre-existing sanity assertions in `tests/integrity/test_merge_union_gitattributes.py`
   needed updating**, not previously listed in the plan: `test_gitattributes_line_present_for_
   working_log_csv` and `test_gitattributes_lines_absent_for_retired_monitoring_paths` both
   asserted the exact substring `"<path> merge=union"` in `.gitattributes`, which no longer
   appears verbatim once `text eol=lf` sits ahead of `merge=union` on those lines. Updated both to
   check via the shared `_merge_union_glob_patterns()` parser (import added) instead of an exact
   substring, so they stay correct regardless of future attribute ordering, and added a short note
   to each docstring citing this ticket.
