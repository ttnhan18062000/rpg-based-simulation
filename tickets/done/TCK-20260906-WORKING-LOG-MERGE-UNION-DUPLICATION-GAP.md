---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP
phase: done
date: 2026-09-06
tags: [registry, process-improvement, debugging, data-quality]
---

# TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP

## Title
merge=union .gitattributes protection did not prevent a ~1586-row whole-block duplication in tickets/working_log.csv

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260904-WORKING-LOG-CSV-PARSER`'s investigation discovered (as an out-of-scope side finding, "Finding 2") that `tickets/working_log.csv` physical lines 2-1587 (1586 data rows) are byte-for-byte identical, in the same relative order, to physical lines 1595-3180 — a whole-block duplication, plus a duplicate embedded copy of the header row itself at line 1594. Root-caused with high confidence to commit `5993cac3` (PR #90, "M1 Quick Wins & Housekeeping...", merged 2026-08-31), which shows a pure +1640/-0 insertion for this file. `.gitattributes` already declares `tickets/working_log.csv merge=union` (added by `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` on 2026-08-26, five days before this incident, with its own claimed "git-level regression test proving the shipped merge=union .gitattributes behavior actually resolves concurrent-branch appends") — but that protection did not prevent this specific incident. This is a real, confirmed gap in that prior ticket's own verified guarantee, not a hypothetical risk.

Direct production impact already live: `tools/knowledge_search.py::_extract_working_log_rows` indexed the bogus embedded header row (line 1594) as a real corpus document (`id="ticket_id"`) until `TCK-20260904-WORKING-LOG-CSV-PARSER` added a narrow guard against that one specific symptom (not this root cause). A naive "row count per ticket_id > 1 ⇒ reopened ticket" signal would report ~1586 false positives today if built without accounting for this duplication.

## Scope
- Investigate why the existing `merge=union` .gitattributes protection (from `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`) did not prevent this specific incident — was it a long-lived branch merged before that protection existed on that branch, a squash-merge losing the attribute's effect, a rebase/fast-forward path that bypasses merge drivers entirely, or something else? Root-cause with real git evidence (`git log`, `git show`, testing the actual merge scenario), not speculation.
- Determine whether the existing `merge=union` regression test (from `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`) has a real coverage gap that let this class of incident through, and if so, close it or add a new test that would have caught this specific scenario.
- Decide whether/how to address the already-present ~1586-row duplication in the live file: this ticket's own scope must NOT rewrite any historical row in `tickets/working_log.csv` (same hard constraint as `TCK-20260904-WORKING-LOG-CSV-PARSER`) — investigate whether any safe remediation exists (e.g., a documented, reviewed one-time cleanup commit with full before/after audit trail) or whether the correct answer is "flag only, forever" the same way `TCK-20260904-WORKING-LOG-CSV-PARSER`'s `is_duplicate` mechanism already does.
- Consider whether `tools/knowledge_search.py`'s corpus-indexing should also generically deduplicate exact-content working-log rows (beyond the one narrow embedded-header-row guard already shipped), given ~1586 real duplicate documents are indexed today.

## Out of Scope
- Rebuilding or duplicating anything `TCK-20260904-WORKING-LOG-CSV-PARSER` already shipped (the tolerant parser, `validate_working_log.py`'s adoption of it, the narrow embedded-header-row guard in `knowledge_search.py`) — this ticket is about the git-merge root cause and the still-open ~1586-row duplication, not the field-parsing problem that ticket already solved.
- Any change to `tickets/working_log.csv`'s append-only convention itself beyond what's needed to close this specific merge-mechanics gap.

## Acceptance Criteria
- [x] Root cause of why `merge=union` did not prevent this specific incident is identified with real git evidence, not speculation
- [x] The existing merge=union regression test's coverage gap (if any) is identified and closed, or a new test is added that would catch this specific scenario
- [x] An explicit, evidence-based decision is recorded on whether/how to remediate the already-present ~1586-row duplication (may be "flag only, do not rewrite," but must be an explicit decision, not silence)
- [x] If `tools/knowledge_search.py`'s corpus indexing is extended to deduplicate exact-content rows, it must not rewrite `tickets/working_log.csv` itself

## Related Tickets
- TCK-20260904-WORKING-LOG-CSV-PARSER
- TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Related Docs
- stored_artifacts/TCK-20260904-WORKING-LOG-CSV-PARSER/investigation.md (Finding 2's full evidence)

## Related Stored Artifacts
None.

## Related Code Areas
- tickets/working_log.csv
- .gitattributes
- tools/knowledge_search.py
- tools/working_log_parser.py

## Assumptions / Open Questions
- Whether this was a squash-merge, a long-lived branch predating the .gitattributes fix, or a rebase/fast-forward bypass is unresolved and must be determined with real evidence during Investigate, not guessed
- Whether any safe remediation of the existing duplication is possible without violating the "never rewrite historical rows" constraint both this and the parser ticket share

## Implementation Notes

Implemented all 7 steps of the approved plan (`staging_artifacts/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP/plan.md`).

1. **`.gitattributes`** — added a squash-merge caveat comment above the two `merge=union`
   lines, explaining that the attribute only engages when git's own merge machinery runs
   and pointing at the new detection test.
2. **`tests/integrity/test_merge_union_gitattributes.py`** — added
   `test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers`, which
   reproduces a squash-merge's mechanics (never calling `git merge`/`rebase`/
   `cherry-pick -m`) and asserts the resulting commit is single-parent and that branch-b's
   concurrent append is silently lost — proving `merge=union` gave it no protection. The 3
   pre-existing tests in this file were not touched; all 8 tests in the file pass.
3. **New file `tests/integrity/test_no_duplicate_content_blocks.py`** — implements the
   ongoing duplicate-content-block detection sweep: reads `.gitattributes`' own
   `merge=union` glob patterns (no hardcoded file list), scans every covered file for a
   contiguous exact-duplicate line block >= 10 lines (keyed by
   `(relative_path, block_length, sha256_of_content)`, never by absolute line number), and
   fails on any block not already in `KNOWN_DUPLICATE_BLOCKS`. Seeded initially with both
   confirmed incidents (`tickets/working_log.csv`'s block and
   `agent-monitoring/data/2026-W36/tools.jsonl`'s 79-line block); the `tickets/working_log.csv`
   entry was removed once Step 6's cleanup landed (see below). Manually verified the
   detection algorithm correctly flags an injected unknown duplicate block in a synthetic
   scratch array (not committed as a permanent second test, per plan/test_plan's own
   "not necessarily a permanent second test case" note).
4. **`tools/validate_working_log.py`** — check 1 (duplicate ticket IDs) now excludes rows
   the tolerant parser already flagged `is_duplicate=True` from its scan. Checks 2 (missing
   `done/` entries) and 3 (empty fields) still consume the original, unfiltered `ids`/
   `kept_rows` — verified by keeping a separate `ids` list for those checks and a new
   `non_duplicate_ids` list solely for check 1.
5. **`tools/knowledge_search.py`** — `_extract_working_log_rows` now dedupes on the exact
   `(ticket_id, title, summary)` content tuple, keeping only the first occurrence (same
   convention as `working_log_parser.py`'s own `seen_raw_lines`). Still opens the CSV
   read-only (`open(csv_path, newline="", encoding="utf-8-sig")`, no mode argument, i.e.
   `"r"`); a test asserts this via a monkeypatched `open` that raises on any non-`"r"` mode.
6. **One-time cleanup commit (`tickets/working_log.csv`)** — independently re-derived the
   duplicate range at implementation time (file was still 3400 physical lines, unchanged
   since investigation): `diff <(sed -n '1,1587p' tickets/working_log.csv) <(sed -n
   '1594,3180p' tickets/working_log.csv)` returned zero differences, confirming plan.md's
   corrected range (1594-3180 inclusive, 1587 lines) — not test_plan.md's stated
   1588-3180. Manually confirmed lines 1588-1593 (6 legitimate rows) are untouched.
   Deleted exactly physical lines 1594-3180; before/after content-preservation diff (`diff
   <(cleaned file) <(sed -n '1,1593p;3181,$p' <pre-cleanup file>)`) showed **zero
   differences**, confirmed against both a local pre-edit copy and the git-tracked HEAD
   version independently. File went from 3400 to 1813 lines. Updated
   `test_no_duplicate_content_blocks.py`'s `KNOWN_DUPLICATE_BLOCKS` to remove the
   `tickets/working_log.csv` entry; re-ran the test — passes with zero blocks detected in
   `tickets/working_log.csv` and only the W36 entry remaining.
7. **W36 non-remediation decision** — recorded explicitly below and in plan.md; not
   remediated in this ticket, tracked via the detection test's allowlist.

**Deviation discovered and resolved during Step 6 (documented in full, with root cause and
exact resolution math, in `staging_artifacts/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP/plan.md`'s
new "Deviations" section):** plan.md's own Step 6 Verify text and Scope Guards asserted
`test_all_11_confirmed_live_mismatch_rows_are_flagged` and
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` (plus, implicitly,
`test_ambiguous_row_count_matches_45_for_real_file` and
`test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path`) would "keep
passing unchanged" post-cleanup because their rows "live entirely outside lines
1594-3180." This was verified false: 2 of the 11 mismatch lines (3104, 3174) and all 17 of
the "extra" 34 quote-desync lines (>= 2693) were themselves the exact-duplicate copies of
other rows in the same sets (offset +1593) and are removed by the cleanup, not merely
shifted; every genuinely unique row physically located after line 3180 necessarily shifts
down by exactly 1587 — an unavoidable consequence of any mid-file deletion, not something
any version of Step 6 could have avoided. Recomputed and independently verified the true
post-cleanup values directly against the live file (`tools/working_log_parser.py`'s
classification logic itself untouched): 9 mismatch rows at
`{1511, 1581, 1658, 1666, 1697, 1700, 1702, 1707, 1720}`, 17 quote-desync rows at the
original (unshifted) `{1100, 1101, 1102, 1103, 1318, 1320, 1329, 1332, 1337, 1400, 1401,
1415, 1453, 1457, 1459, 1460, 1462}`, and `ambiguous_row_count == 26` (9 + 17, vs. the old
45 = 11 + 34 which double-counted every duplicate copy). Updated the 4 affected test
functions' hardcoded literals to these verified values, with docstrings citing this
ticket and the exact renumbering math, renaming
`test_all_11_confirmed_live_mismatch_rows_are_flagged` →
`test_all_9_confirmed_live_mismatch_rows_are_flagged`,
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` →
`test_all_17_confirmed_live_quote_desync_lines_are_flagged`, and
`test_ambiguous_row_count_matches_45_for_real_file` →
`test_ambiguous_row_count_matches_26_for_real_file`. This was treated as a "stop and
report" conflict — flagged explicitly here and in the implementer's final report — rather
than a silent workaround; no classification logic in `tools/working_log_parser.py` was
touched, only test assertion literals reflecting new, correct ground truth.

**W36 non-remediation decision (Step 7):** `agent-monitoring/data/2026-W36/tools.jsonl`'s
confirmed 79-line duplicate block (physical lines 22831-22909 byte-identical to
23240-23318) is the same defect class (squash-merge bypassing `merge=union`) as the
`tickets/working_log.csv` incident, but is **deliberately not remediated** in this ticket.
Reasons: (1) this ticket's Scope and Out-of-Scope center on `tickets/working_log.csv`
specifically; (2) `agent-monitoring/data/*/*.jsonl` shards are auto-appended on nearly
every tool call (a materially more active writer profile than `working_log.csv`'s
occasional ticket-close appends per `CLAUDE.md`'s Hard Rules), so a cleanup edit there
carries a higher, less-understood concurrent-write collision risk than this ticket's
evidence base justifies taking on. It is tracked, not ignored, via
`test_no_duplicate_content_blocks.py`'s `KNOWN_DUPLICATE_BLOCKS` allowlist entry. A
follow-up ticket is recommended to remediate it once that collision risk is separately
assessed. A full 46-file manual sweep for additional undetected duplicate blocks was not
performed — `test_no_duplicate_content_blocks.py`'s scan itself is now the ongoing sweep
mechanism; any further latent instance will surface as a new failing test, not something
this ticket needed to hunt for by hand.

## Test Summary

Scoped commands run (via `.venv/bin/python3 -m pytest ... -m "not slow"`):
- `tests/integrity/test_merge_union_gitattributes.py` — 8 passed (7 pre-existing + 1 new).
- `tests/integrity/test_no_duplicate_content_blocks.py` — 1 passed (new file).
- `tests/tools/test_validate_working_log.py` — 19 passed (18 pre-existing, incl. the 4
  renamed/recomputed ones, + 1 new: `test_duplicate_ticket_ids_check_excludes_flagged_duplicate_rows`).
- `tests/tools/test_knowledge_search.py` — 83 passed, 28 deselected (`-m "not slow"`);
  includes 1 new test in `TestExtractWorkingLogRows`.
- `tests/tools/test_parity_index.py` — 40 passed (unrelated sanity check per test_plan.md's
  Regression Surface, all still green).
- Combined single run of the first 4 files above: **111 passed**, 0 failed.
- `python3 tools/validate_working_log.py` run directly against the live post-cleanup file:
  the "Duplicate ticket IDs" error class no longer includes any of the ~1586 formerly-
  duplicated ticket IDs — only 16 genuine duplicate ticket IDs remain (pre-existing,
  unrelated to this ticket). The pre-existing "empty field 'artifacts_path'" errors (17
  rows, `TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`'s documented leftover) and the
  pre-existing "164 ticket(s) in done/ with no working_log entry" errors remain — confirmed
  present in the pre-cleanup file too via a direct before/after comparison, i.e. unrelated
  to and unchanged by this ticket's work.

## Files Changed

- `.gitattributes` — squash-merge caveat comment (Step 1)
- `tests/integrity/test_merge_union_gitattributes.py` — new additive regression test (Step 2)
- `docs/agent-monitoring/schema.md` — Document-Update phase: added a new "Known Limitations"
  subsection documenting the confirmed 2026-W36/tools.jsonl 79-line squash-merge duplicate block
  (root cause, the explicit non-remediation decision/rationale, the `KNOWN_DUPLICATE_BLOCKS`
  allowlist tracking mechanism), matching this file's existing pattern of documenting comparable
  real-corpus data-quality anomalies for this same file family.
- `tests/integrity/test_no_duplicate_content_blocks.py` — new file (Step 3)
- `tools/validate_working_log.py` — check-1 `is_duplicate` exclusion fix (Step 4)
- `tests/tools/test_validate_working_log.py` — new test (Step 4) + 4 tests renamed/recomputed
  after Step 6's line-shift (deviation, see Implementation Notes)
- `tools/knowledge_search.py` — `_extract_working_log_rows` exact-content dedup (Step 5)
- `tests/tools/test_knowledge_search.py` — new test in `TestExtractWorkingLogRows` (Step 5)
- `tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md` — added a dated "Correction"
  paragraph to its own Completion Summary (matching the exact precedent format established by
  commit `609f0823`'s correction of `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX.md`), correcting
  that ticket's own claim that the shipped `merge=union` behavior "resolves concurrent-branch
  appends" — true for a real `git merge`, but not for this repo's actual squash-merge PR-landing
  convention, which this ticket's investigation confirmed is systemic. Architecture-Verify found
  the Document-Update agent's initial claim of "no precedent for amending a DONE ticket" was
  itself factually wrong (a real precedent exists); this correction was added once that was
  verified, rather than recording the omission as a deliberate scope choice.
- `tickets/working_log.csv` — one-time cleanup commit, physical lines 1594-3180 deleted,
  every surviving line byte-identical and in original order (Step 6)
- `staging_artifacts/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP/plan.md` —
  added "Deviations" section documenting the Step 6 test-shift conflict and resolution
- `tickets/inprogress/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md` — this file
  (Implementation Notes / Test Summary / Files Changed / Completion Summary / Status /
  Acceptance Criteria, Step 7)

## Completion Summary

Root-caused (with direct git evidence: single-parent commit, GitHub-recorded merge SHA,
concatenated squash-merge commit message, 5/5 recent-PR sample) why `merge=union` did not
prevent the ~1586-row `tickets/working_log.csv` duplication: GitHub squash-merge — this
repo's de facto standard PR-landing mechanism — never invokes git's merge machinery, so no
merge driver of any kind runs. Closed the coverage gap with a permanent root-cause
regression test and a new ongoing duplicate-content-block detection test (riding the
existing `arch-docs` CI job, no new wiring needed) that would have caught this incident
(and the second, previously-undetected 79-line `agent-monitoring/data/2026-W36/tools.jsonl`
instance) automatically. Remediated the confirmed `tickets/working_log.csv` duplication via
a one-time, content-preservation-verified cleanup commit (deleting exactly the duplicate
physical lines, rewriting nothing); explicitly decided, and recorded, not to remediate the
W36 instance in this ticket (tracked via allowlist, follow-up recommended). Fixed
`validate_working_log.py`'s `is_duplicate`-blind duplicate-ticket-ID check, and extended
`knowledge_search.py`'s corpus extraction to dedupe exact-content rows without ever writing
to the CSV. One real deviation from the plan was discovered, fully investigated, and
resolved: the plan's Step 6 Verify text incorrectly assumed 4 pre-existing line-number-
based tests would be unaffected by the cleanup, which is physically impossible for any
mid-file deletion; those 4 tests were updated (assertion literals only, not classification
logic) to their independently-verified correct post-cleanup values, documented in full in
this ticket and in plan.md's new Deviations section.

A second, unrelated real finding surfaced during Finalize: `tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md`'s own frontmatter reads `status: active`/`phase: open` despite sitting in `tickets/done/` — confirmed present since that ticket's original 2026-08-26 closure commit, not something introduced by this ticket's own edit (a body-only correction paragraph). A repo-wide check found this is not isolated: 227 of 1850 `tickets/done/*.md` files carry the same mismatch, uncaught by `validate_frontmatter.py` because each field is individually valid — the missing check is cross-field (phase/status vs. physical directory) consistency. Filed as a separate follow-up ticket, `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`, rather than fixed here (out of this ticket's own scope).
