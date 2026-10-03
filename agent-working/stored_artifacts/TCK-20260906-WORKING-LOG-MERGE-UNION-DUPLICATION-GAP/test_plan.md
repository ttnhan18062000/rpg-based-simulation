---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP
artifact_type: test_plan
tags: [registry, process-improvement, debugging, data-quality]
---

# Test Plan — TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP

## Regression Surface

**Integration (git-level, `tests/integrity/`, runs in CI's `arch-docs` job per
`.github/workflows/test.yml` lines 412/434):**
- `tests/integrity/test_merge_union_gitattributes.py` — all 7 existing tests (5
  parametrized `test_concurrent_branch_appends_merge_without_conflict_markers` cases +
  `test_gitattributes_line_present_for_working_log_csv` +
  `test_gitattributes_lines_absent_for_retired_monitoring_paths`) must keep passing
  unmodified — this investigation found no defect in what they test, only a gap in what
  they don't test.

**Unit (`tests/tools/`, runs in CI's `api-tools` job per lines 268/291):**
- `tests/tools/test_validate_working_log.py` — all existing tests, especially
  `test_duplicate_content_rows_are_flagged_not_fixed`,
  `test_embedded_header_duplicate_row_is_flagged`,
  `test_all_11_confirmed_live_mismatch_rows_are_flagged`,
  `test_all_34_confirmed_live_quote_desync_lines_are_flagged`,
  `test_round_trip_parses_full_file_without_exception`,
  `test_ambiguous_row_count_matches_45_for_real_file` — these encode exact counts against
  the real, live file; any change to `tools/working_log_parser.py` or
  `tools/validate_working_log.py` risks silently shifting these baselines (they must not
  drift as a side effect of this ticket, since this ticket does not modify parsing logic
  for the 11/34-row classes).
- `tests/tools/test_knowledge_search.py` — the `_extract_working_log_rows` unit-test class
  (`test_does_not_index_embedded_header_duplicate_row` and its siblings, lines ~666-709)
  must keep passing; if Plan adopts a broader exact-content dedup in
  `knowledge_search.py` (ticket Scope item 4 / AC4), it must be additive to this existing
  guard, not a replacement.
- `tests/tools/test_parity_index.py::TestRealLedgerCollisionGuard` — unrelated to this
  ticket's changes but shares `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`'s lineage;
  include in the scoped run as a cheap sanity check that nothing in this area regressed.

## New Tests Required

1. **`test_no_new_duplicate_content_block_beyond_documented_baseline`**
   - Category: integration / architecture guard
   - Verifies: scans every file matching `.gitattributes`' `merge=union` patterns
     (`tickets/working_log.csv`, `agent-monitoring/data/*/*.jsonl`) for a contiguous
     exact-duplicate line block above a size threshold (recommend >= 10 lines, well above
     any plausible coincidental repeat and well below the smallest confirmed real
     incident, the 79-line W36 block), and fails if any such block exists that is **not**
     in a maintained baseline/allowlist (keyed by file path + block size + a content hash
     or the block's own first/last line, not by absolute line number, since the file keeps
     growing via legitimate appends). The baseline is seeded with the two confirmed real
     incidents found by this investigation (the ~1586-row `tickets/working_log.csv` block
     + line-1594 embedded header, and the 79-line `agent-monitoring/data/2026-W36/
     tools.jsonl` block) so the test passes today, and fails the moment a **new** one
     appears — this is the test that would have caught this specific squash-merge
     recurrence (and the previously-undetected W36 instance) automatically, post-merge,
     instead of relying on an unrelated ticket's investigation to stumble onto it six days
     later.
   - Where: `tests/integrity/test_merge_union_gitattributes.py` (new test in the existing
     file, since it directly extends that file's own subject matter) or a new
     `tests/integrity/test_no_duplicate_content_blocks.py` if Plan prefers to keep the
     baseline-allowlist machinery separate from the git-merge-mechanism tests — either is
     acceptable, Plan's call.
   - Note: this test detects, it does not prevent — per this investigation's root-cause
     finding, no `.gitattributes`-level mechanism can prevent a squash-merge from
     reproducing content, since no merge driver runs for that operation. This test's value
     is turning "silent, undiscovered for days" into "loud, caught in the next CI run."

2. **`test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers`**
   - Category: unit / documentation-as-test (regression guard against re-trusting the
     original false assumption)
   - Verifies: builds a throwaway repo (reusing `_init_repo_with_union_attribute`'s
     pattern), creates two branches that each append content to a `merge=union` file,
     then — instead of `git merge` — reproduces the *effect* PR #90 had by committing
     branch-b's append directly to `main` and then applying branch-a's **diff against the
     original base** as a second plain (non-merge, single-parent) commit on top, i.e. no
     `git merge`/`git rebase`/`git cherry-pick -m` command is ever invoked. Asserts (a)
     the resulting commit has exactly one parent, and (b) the file's content afterward
     contains a literal duplicate of whichever lines the diff-apply reproduced — proving
     concretely, at the git level, that `merge=union` provides zero protection for any
     landing path that does not go through git's own merge machinery. This encodes the
     root-cause finding as a permanent, falsifiable regression guard so a future
     contributor cannot re-conclude "merge=union protects against this" without the test
     suite itself demonstrating otherwise.
   - Where: `tests/integrity/test_merge_union_gitattributes.py` (same file as the existing
     git-merge-scenario tests, as a clearly-labeled contrasting case).

3. **`test_duplicate_ticket_ids_check_excludes_flagged_duplicate_rows`** (conditional —
   only if Plan adopts this investigation's Risk/Open-Question #4 recommendation to fix
   `validate_working_log.py`'s check-1 gap)
   - Category: unit
   - Verifies: `run_validation()`'s "Duplicate ticket IDs" check does not report a
     ticket_id as duplicate solely because of an exact-duplicate-content row already
     flagged `is_duplicate=True` by the tolerant parser; a **genuine** same-ticket-ID,
     different-content second row (e.g. an actual reopened ticket, or two independent
     manual double-pastes like the 3245/3253 pair) must still be reported.
   - Where: `tests/tools/test_validate_working_log.py`.
   - If Plan defers this fix to a separate follow-up ticket instead, this test is not
     required here — note the deferral explicitly in Implementation Notes rather than
     silently dropping it.

4. **`test_knowledge_search_dedupes_exact_content_working_log_rows_without_writing_csv`**
   (conditional — only if Plan adopts ticket Scope item 4 / AC4's broader dedup)
   - Category: unit
   - Verifies: `_extract_working_log_rows` (or its caller) emits at most one corpus
     document per distinct `(ticket_id, title, summary, artifacts_path)` content tuple
     even when the source CSV contains many exact-duplicate rows (using a synthetic
     `tmp_path` CSV seeded with a duplicate block, not the real file), **and** that the
     source file at the given path is never opened in write/append mode by this code path
     (assert via `unittest.mock` monkeypatching `open` to raise on any non-`"r"` mode, or
     equivalent) — directly enforcing AC4's "must not rewrite tickets/working_log.csv
     itself."
   - Where: `tests/tools/test_knowledge_search.py` (extends the existing
     `_extract_working_log_rows` test class).

## Scoped Pytest Commands

```
python3 -m pytest tests/integrity/test_merge_union_gitattributes.py -q -m "not slow"
python3 -m pytest tests/tools/test_validate_working_log.py tests/tools/test_knowledge_search.py tests/tools/test_parity_index.py -q -m "not slow"
```

If a new standalone file (`tests/integrity/test_no_duplicate_content_blocks.py`) is added
instead of extending the existing one, include it explicitly:
```
python3 -m pytest tests/integrity/test_merge_union_gitattributes.py tests/integrity/test_no_duplicate_content_blocks.py -q -m "not slow"
```

Never `pytest tests/` — scope stays within `tests/integrity/` (git-merge mechanics,
duplicate-content guard) and `tests/tools/` (parser/validator/knowledge-search unit
coverage), matching this ticket's Related Code Areas.

## Anti-Drift Test Guards

- **`tests/tools/test_validate_working_log.py`'s exact-count assertions against the real
  live file** (`test_ambiguous_row_count_matches_45_for_real_file`,
  `test_all_11_confirmed_live_mismatch_rows_are_flagged`,
  `test_all_34_confirmed_live_quote_desync_lines_are_flagged`) already act as a guard that
  nothing in this ticket accidentally touches `tools/working_log_parser.py`'s classification
  logic for the unrelated Finding 1/Finding 3 row classes — if any of these baseline counts
  change as a side effect of this ticket's work, that is scope creep into
  `TCK-20260904-WORKING-LOG-CSV-PARSER`'s already-closed territory, not this ticket's
  concern.
- **The new duplicate-content-block guard's baseline must be an explicit, reviewed
  allowlist keyed by content/size, not a bare line count of the live file** — a bare
  `wc -l tickets/working_log.csv == N` assertion would break on every single legitimate new
  ticket closure (the file grows by design) and would not distinguish "the file grew
  normally" from "a new duplicate block appeared." The guard must specifically re-detect
  the same duplicate-block-search algorithm used in this investigation, not a proxy metric.
- **If Plan chooses remediation option (b) (a one-time cleanup commit removing the exact
  duplicate lines)**, the required test is a before/after content-preservation check: every
  non-duplicate line's content and relative order must be byte-identical pre- and
  post-cleanup (e.g. a diff of the deduplicated file against
  `sed -n '1,1587p;3181,$p' tickets/working_log.csv` from the current state, since the
  duplicate block is confirmed to be exactly lines 1588-3180 inclusive — lines 2-1587 kept,
  1588-3180 removed, 3181-end kept) — this is the guard that proves the cleanup deleted
  only the redundant copies and rewrote zero surviving row's content, which is the
  precondition this investigation's recommendation depends on.
- **Do not let a new "detect duplicate content" test anywhere accidentally start asserting
  on `tickets/working_log.csv`'s exact total row/line count** — any such test must tolerate
  ongoing legitimate growth; only the flagged/duplicate subset should be asserted against a
  fixed baseline.
