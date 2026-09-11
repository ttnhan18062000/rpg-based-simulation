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
