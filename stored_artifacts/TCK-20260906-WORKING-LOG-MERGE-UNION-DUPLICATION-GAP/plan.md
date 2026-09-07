---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP
artifact_type: plan
tags: [registry, process-improvement, debugging, data-quality]
---

# Implementation Plan — TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP

## Summary

The investigation confirmed with direct git evidence that `merge=union` never protects
against this repo's actual PR-landing mechanism (squash-merge — 5/5 recent PRs confirmed
single-parent), because no merge driver runs unless git's own merge machinery runs. Since
"stop squash-merging" is explicitly out of scope (org/repo GitHub setting) and not something
this ticket can enforce anyway, the fix is a **detection** mechanism, not a prevention one: a
new pytest test in `tests/integrity/` that scans every `merge=union`-covered file for a
contiguous exact-duplicate line block above a threshold, checked against a maintained,
content-keyed allowlist. It rides the existing CI wiring (`arch-docs` job in
`.github/workflows/test.yml`, triggered on every `push` to `main` and every `pull_request`) —
no new CI job, hook, or pre-merge gate is needed, because that job already runs immediately
after every squash-merge lands on `main`, closing the "silent for six days" gap the ticket
opened with. A second new test permanently encodes the root-cause finding itself (single-parent
commit ⇒ no merge driver invoked) so nobody re-concludes `merge=union` is sufficient. The
already-present ~1586-row `tickets/working_log.csv` duplication is remediated via a dedicated,
narrowly-scoped one-time cleanup commit that removes only the exact-duplicate physical lines
(verified in this plan to be lines 1594–3180 inclusive, **not** 1588–3180 as `test_plan.md`
stated — see Anti-Drift Notes), leaving every surviving row's content and order untouched.
`validate_working_log.py`'s `is_duplicate`-blind check-1 gap is folded in as a small, directly
-evidenced fix. The `agent-monitoring/data/2026-W36/tools.jsonl` 79-line duplicate is
deliberately **not** remediated in this ticket — it is recorded in the new detection test's
baseline allowlist (so it's tracked, not ignored) and flagged as a follow-up ticket
recommendation, because monitoring shards have a materially different (more active,
per-tool-call) writer profile than `working_log.csv`'s occasional ticket-close appends, and
touching one without a concrete need adds risk this ticket's evidence base doesn't justify. A
full 46-file remediation sweep is also out of scope; the detection test's own scan mechanism
*is* the sweep going forward, so nothing further is needed to get that coverage.

## Steps

### Step 1 — Add a squash-merge caveat comment to `.gitattributes`
**Files:** `.gitattributes`
**Change:** Above the two `merge=union` lines (currently at `.gitattributes:1-7`, read in
full during planning — the existing comment already explains *why* union-merging is safe for
these append-only files but says nothing about squash-merge), add a short comment noting that
`merge=union` only engages when git's own merge machinery runs (`git merge`, `git rebase`,
`git cherry-pick -m`, GitHub's "Create a merge commit" option) and provides **no** protection
against a GitHub squash-merge, which is this repo's de facto standard PR-landing mechanism
(investigation.md: 5/5 of the last 5 merged PRs were squash-merged). Point readers at
`tests/integrity/test_no_duplicate_content_blocks.py` (Step 3) as the mechanism that actually
covers the squash-merge path.
**Do NOT touch:** The existing `merge=union` attribute lines themselves, the `docs/REGISTRY.yaml`
exclusion comment below them, or the glob patterns — this step is comment-only.
**Verify:** `tests/integrity/test_merge_union_gitattributes.py::test_gitattributes_line_present_for_working_log_csv`
and `::test_gitattributes_lines_absent_for_retired_monitoring_paths` still pass unmodified
(they assert on line presence/absence, not comment text, so a comment-only change cannot break
them — confirmed by reading both assertions at `tests/integrity/test_merge_union_gitattributes.py:98`
and `:111-114`).

### Step 2 — Add a permanent regression test encoding the root-cause finding
**Files:** `tests/integrity/test_merge_union_gitattributes.py`
**Change:** Add `test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers`
per `test_plan.md` item 2. Reuse the existing `_init_repo_with_union_attribute` helper
(`tests/integrity/test_merge_union_gitattributes.py:27-39`, already read in full — it inits a
throwaway repo with one `merge=union` file and one initial commit). Build two branches that
each append a line to that file, then reproduce a squash-merge's *effect* by (a) committing
branch-b's append directly onto `main`, then (b) applying branch-a's diff **against the
original base** as one more plain, single-parent commit on top of `main` — never invoking
`git merge`, `git rebase`, or `git cherry-pick -m`. Assert: (1) `git log -1 --format=%P` on the
resulting commit shows exactly one parent; (2) the file's content contains a literal duplicate
of the lines the diff-apply reproduced. This is a documentation-as-test guard, not a fix — it
makes the root-cause claim falsifiable and permanent.
**Do NOT touch:** `test_concurrent_branch_appends_merge_without_conflict_markers` or either of
the two `test_gitattributes_line*` tests in this file — they are correct and must keep passing
byte-for-byte as written.
**Verify:** New test passes; existing 7 tests in this file still pass
(`python3 -m pytest tests/integrity/test_merge_union_gitattributes.py -q -m "not slow"`).

### Step 3 — Build the duplicate-content-block detection mechanism
**Files:** New file `tests/integrity/test_no_duplicate_content_blocks.py`
**Change:** Implement `test_no_new_duplicate_content_block_beyond_documented_baseline` per
`test_plan.md` item 1, kept in a new file rather than extending
`test_merge_union_gitattributes.py` (Plan's choice, per that file's own note that either
location is acceptable) so the baseline-allowlist machinery stays separable from the
git-merge-mechanism tests.
- Enumerate every file matching `.gitattributes`' two `merge=union` glob patterns
  (`agent-monitoring/data/*/*.jsonl` and `tickets/working_log.csv`, read directly from
  `.gitattributes` at test time — do not hardcode the glob list separately, to avoid drift if
  `.gitattributes` changes).
- For each file, scan for the longest run of contiguous lines where `lines[i:i+k] ==
  lines[i+offset:i+offset+k]` for some `offset > 0` and `k >= 10` (threshold chosen per
  `test_plan.md`: well above coincidental repeats, well below the smallest confirmed real
  incident — 79 lines in the W36 case).
- Key each detected block by `(relative_file_path, block_length, sha256_of_block_content)` —
  never by absolute line number, since both covered files grow via legitimate ongoing appends.
- Maintain a module-level `KNOWN_DUPLICATE_BLOCKS` allowlist (a Python tuple/list of these
  keys, each with a comment citing the ticket that found it) seeded with exactly the two
  confirmed real incidents:
  1. `tickets/working_log.csv` — the header-duplicate + 1586-row block. **If Step 6 (cleanup)
     lands before this step's baseline is written, this entry is omitted entirely** (see
     Dependency Map) — Plan's intended build order is Step 3 before Step 6, so this entry
     starts present and Step 6 removes it.
  2. `agent-monitoring/data/2026-W36/tools.jsonl` — the 79-line block at lines 22830–22908 /
     23239–23317 (investigation.md, confirmed via microsecond-timestamp sample match). This
     entry stays permanently, since Step 5 of this plan (W36) explicitly decides not to
     remediate it — see Summary and Anti-Drift Notes.
- The test fails if any detected block's key is **not** in the allowlist (a genuinely new
  incident), and separately warns (does not fail) if an allowlisted key is no longer detected
  (so a future remediation of the W36 block doesn't require touching this test — stale
  allowlist entries degrade to informational, not blocking).
**Do NOT touch:** `tests/integrity/test_merge_union_gitattributes.py`'s existing tests (this is
additive, in a new file). Do not implement this as a bare `wc -l` / total-line-count assertion
— per `test_plan.md`'s explicit anti-drift guard, that would break on every legitimate ticket
closure.
**Verify:** New test passes against the live repo today (both known incidents pre-seeded in the
allowlist); manually confirm it fails if a `>= 10`-line duplicate block is injected into a
scratch copy of a covered file that isn't in the allowlist (a quick local sanity check during
implementation, not necessarily a permanent second test case).

### Step 4 — Fix `validate_working_log.py`'s `is_duplicate`-blind check-1 gap
**Files:** `tools/validate_working_log.py`
**Change:** `run_validation`'s check 1 (`tools/validate_working_log.py:41-50`, read in full —
confirmed: `ids = [r.get("ticket_id", "").strip() for r in rows]` where `rows = [r.record for r
in kept_rows]` and `kept_rows = [r for r in parse_result.rows if r.record is not None]`) builds
its duplicate-ID list from **every** row with a non-`None` `record`, including rows the tolerant
parser (`tools/working_log_parser.py:307-311`, confirmed: exact-duplicate physical lines get
`is_duplicate=True` but still carry a populated `record`, since duplicate-content rows are
otherwise classified `"clean"`) already flagged `is_duplicate=True`. Fix: for check 1 only,
build `ids` from rows where `record is not None and not r.is_duplicate` (i.e. exclude
already-flagged exact-duplicate rows from the duplicate-ticket-ID scan specifically). Do not
change what feeds `row_count`, check 2 (missing done/ entries), or check 3 (empty fields) — this
is a narrow, single-check fix, not a general re-scoping of which rows `run_validation` considers
"real."
**Other writers/readers of this shared logic:** `validate_working_log.py` is confirmed
(`grep -rn "validate_working_log" .github/workflows/ Makefile tools/gate_checks/` → zero hits,
re-confirmed during planning) not invoked by any CI job, `make` target, or gate check today — it
is a standalone manual script. No other code path reads or depends on `run_validation`'s return
shape, so this fix cannot regress a hidden caller.
**Do NOT touch:** `tools/working_log_parser.py` itself (its `is_duplicate` field already exists
and is correct — this step only makes `validate_working_log.py` consult it), or checks 2/3 in
`run_validation`.
**Verify:** New test `test_duplicate_ticket_ids_check_excludes_flagged_duplicate_rows` in
`tests/tools/test_validate_working_log.py` (per `test_plan.md` item 3): an exact-duplicate row
(`is_duplicate=True`) does not trigger a false duplicate-ID error, but a genuine
same-ticket-ID/different-content second row still does. Also re-run
`python3 tools/validate_working_log.py` directly against the live file post-Step-6 cleanup and
confirm the "Duplicate ticket IDs" error class no longer fires for the ~1586-row block (the
pre-existing, unrelated "empty field 'artifacts_path'" errors from
`TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`'s documented 17-row leftover are expected
to remain and are out of this ticket's scope).

### Step 5 — Extend `knowledge_search.py`'s working-log corpus extraction to dedupe exact-content rows
**Files:** `tools/knowledge_search.py`
**Change:** `_extract_working_log_rows` (`tools/knowledge_search.py:95-143`, read in full) opens
the CSV **read-only** (`open(csv_path, ..., encoding="utf-8-sig")`, no write mode anywhere in
this function) and returns a plain list of `{id, title, summary, path}` dicts, one per row,
already guarding one narrow case (`ticket_id == "ticket_id"`, the embedded-header duplicate,
lines 121-126). `_collect_corpus` (`tools/knowledge_search.py:205-219`, read in full) appends
one document per row from that list into the shared `docs` list with **no** dedup — confirmed
directly: every exact-duplicate content row (not just the embedded header) currently produces
its own separate document with the same `id`, meaning today's corpus carries on the order of
1586 duplicate documents for `tickets/working_log.csv` alone. Fix: within
`_extract_working_log_rows`, track a `seen` set keyed by the exact `(ticket_id, title, summary)`
tuple (mirroring `working_log_parser.py`'s own `seen_raw_lines`-by-exact-content approach) and
skip appending a row to the returned list if its tuple was already seen — keep the **first**
occurrence only, same convention `working_log_parser.py` already uses (`duplicate_of_line`
always points backward to the earlier line). This function never opens the file in write mode
before or after this change — the fix only changes which in-memory rows are returned, never
touching the file on disk.
**Other writers/readers of this shared resource:** `_collect_corpus` is the only caller of
`_extract_working_log_rows` (confirmed via `grep -n "_extract_working_log_rows" tools/knowledge_search.py`
→ two hits: the definition and this one call site). The corpus build itself
(`make knowledge-index-update` / the CLI entry point) runs as a single serial process with no
concurrent writers to the in-memory `docs` list within one invocation — no race to account for.
**Do NOT touch:** The existing `ticket_id == "ticket_id"` embedded-header guard (lines 124-126)
— this new dedup is additive on top of it, not a replacement (per `test_plan.md`'s explicit
anti-drift guard for `TestExtractWorkingLogRows`). Do not touch `_collect_corpus`'s other three
corpus roots (`tickets/done/`, `stored_artifacts/`, `docs/`) — out of this step's scope.
**Verify:** New test `test_knowledge_search_dedupes_exact_content_working_log_rows_without_writing_csv`
in `tests/tools/test_knowledge_search.py` (per `test_plan.md` item 4): a synthetic `tmp_path`
CSV seeded with an exact-duplicate block yields at most one corpus document per distinct
content tuple, **and** the source file is never opened in a non-`"r"` mode (assert via
monkeypatching `open` to raise on any other mode). Existing
`TestExtractWorkingLogRows::test_does_not_index_embedded_header_duplicate_row` and the rest of
that class must keep passing unmodified.

### Step 6 — One-time cleanup commit: remove the confirmed ~1586-row duplicate block from `tickets/working_log.csv`
**Files:** `tickets/working_log.csv`, `tests/integrity/test_no_duplicate_content_blocks.py`
(baseline update from Step 3)
**Change:** Remediation decision (AC3): **Option (b)** — a dedicated, reviewed one-time cleanup
commit, not "flag only forever" and not any content-rewriting approach. Justification: git
history permanently preserves the removed lines' original content (`git show
<pre-cleanup-sha>:tickets/working_log.csv` remains a full, permanent record), so this is
"delete an exact physical duplicate," never "rewrite/reinterpret a historical row's content" —
the hard constraint this ticket and `TCK-20260904-WORKING-LOG-CSV-PARSER` share is about not
altering what a *surviving* row says, not about whether a byte-identical redundant copy may be
removed. **Exact scope, verified directly during planning (not taken from `test_plan.md`,
which stated an incorrect range):**
- `diff <(sed -n '1,1587p' tickets/working_log.csv) <(sed -n '1594,3180p' tickets/working_log.csv)`
  returns no differences (verified during planning) — the duplicate block is **lines 1594–3180
  inclusive** (1587 lines: the embedded duplicate header at line 1594, plus 1586 duplicate data
  rows at 1595–3180, exactly reproducing lines 1–1587).
- Lines 1588–1593 (6 rows: `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`,
  `TCK-20260826-HOTFIX-MECHANICS-README-STALE-DIVERGENCE`, `TCK-20260824-ROLLOUT-FLAG-DECISIONS`,
  `TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`, `TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION`,
  `TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`) are **unique, legitimate rows and must be
  preserved** — `test_plan.md`'s Anti-Drift Test Guards section states the range as
  "1588–3180 removed," which would silently delete these 6 real rows. Do not follow that
  range; follow the verified 1594–3180 range instead.
- Concrete removal: read the file, delete exactly physical lines 1594 through 3180 (1-indexed,
  inclusive), write back every other line completely unchanged, in original order.
**Other writers to this shared resource:** `tickets/working_log.csv` has exactly one writer
pattern across the whole codebase — a manual/agent append of one new row at the file's tail on
every ticket closure (per `CLAUDE.md`'s "After Work" convention); `working_log_parser.py`'s own
docstring (`tools/working_log_parser.py:5`) confirms "no programmatic writer exists anywhere in
the codebase." The cleanup edit region (lines 1594–3180, deep in the file's middle) and the
append region (the file's tail, past line 3400+ as of this plan) are non-overlapping, so a
concurrent ticket-closure append landing during this cleanup's review window does not collide
with the deleted hunk — a normal diff/patch-apply (squash-merge or otherwise) handles
non-overlapping regions correctly as long as immediate context lines around the deleted hunk
are untouched, which they are. Land this cleanup commit promptly in its own small, reviewed PR
to keep the collision window short regardless.
**Baseline update:** Remove the `tickets/working_log.csv` entry from Step 3's
`KNOWN_DUPLICATE_BLOCKS` allowlist (the block it described no longer exists after this step)
and re-run Step 3's test to confirm it still passes with zero duplicate blocks detected in
`tickets/working_log.csv` and only the (deliberately retained) W36 entry remaining.
**Do NOT touch:** Any line outside 1594–3180 in `tickets/working_log.csv`, and do not alter
`agent-monitoring/data/2026-W36/tools.jsonl` in this step (see Step 7).
**Verify:** Before/after content-preservation check (per `test_plan.md`'s Anti-Drift Test
Guards, corrected to the verified range): `diff <(cleaned file) <(sed -n '1,1593p;3181,$p'
tickets/working_log.csv)` from the pre-cleanup state must show zero differences — proving every
surviving line's content and relative order is byte-identical pre- and post-cleanup. Also
re-run `python3 -m pytest tests/tools/test_validate_working_log.py -q -m "not slow"` and confirm
`test_ambiguous_row_count_matches_45_for_real_file`,
`test_all_11_confirmed_live_mismatch_rows_are_flagged`, and
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` still pass unchanged (Finding
1/Finding 3 row classes live entirely outside lines 1594–3180 and must not shift).

### Step 7 — Record the explicit W36 non-remediation decision
**Files:** `tickets/inprogress/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md`
(Implementation Notes section, edited by the implementer/Finalize as part of normal ticket
close-out — not a source-code change)
**Change:** Record explicitly (do not leave silent): the `agent-monitoring/data/2026-W36/tools.jsonl`
79-line duplicate block is a confirmed, real, same-defect-class instance (investigation.md) that
this ticket deliberately does **not** remediate. Reasons: (1) the ticket's own Scope and
Out-of-Scope center on `tickets/working_log.csv`; (2) `agent-monitoring/data/*/*.jsonl` shards
have a materially more active writer profile (auto-appended on nearly every tool call per
`CLAUDE.md`'s Hard Rules) than `working_log.csv`'s occasional ticket-close appends, so a cleanup
edit there carries a higher, less-understood concurrent-write collision risk that this ticket's
evidence base does not justify taking on. It is tracked, not ignored, via Step 3's allowlist
entry. Recommend filing a follow-up ticket for its remediation once that write-collision risk is
separately assessed. Also record: a full 46-file sweep for additional undetected duplicate
blocks was not performed as a one-time manual exercise, because Step 3's detection test already
performs that same sweep as an ongoing, automatic mechanism — any third instance it finds in the
future (or already latent in an unswept file) surfaces as a new, separate finding via a failing
test, not as something this ticket needed to hunt for by hand.
**Do NOT touch:** Any file under `agent-monitoring/` in this step.
**Verify:** N/A (documentation-only; covered by `done-checker`'s standard ticket-completeness
check, not a pytest test).

## Scope Guards

- Do not modify `tests/integrity/test_merge_union_gitattributes.py`'s existing assertions —
  `test_concurrent_branch_appends_merge_without_conflict_markers`,
  `test_gitattributes_line_present_for_working_log_csv`, and
  `test_gitattributes_lines_absent_for_retired_monitoring_paths` all stay exactly as written;
  only additive tests are allowed in that file (Step 2).
- Do not attempt to change GitHub's repo-level merge-strategy settings
  (`squashMergeAllowed`/`mergeCommitAllowed`/`rebaseMergeAllowed`) — confirmed org/repo-level
  setting, out of this ticket's Related Code Areas.
- Do not rewrite, reorder, or alter the content of any surviving row in
  `tickets/working_log.csv` — Step 6 deletes only the exact-duplicate physical lines
  (1594–3180), verified byte-identical to lines 1–1587, and touches nothing else.
- Do not remediate `agent-monitoring/data/2026-W36/tools.jsonl`'s 79-line duplicate in this
  ticket (Step 7's explicit decision) — allowlist it in Step 3's baseline, do not delete its
  lines.
- Do not perform a full manual remediation sweep of all 46 `merge=union`-covered files — Step
  3's detection test provides ongoing sweep coverage; this ticket remediates only the two
  already-confirmed instances (one via Step 6, one deliberately left flagged via Step 7).
- Do not re-implement anything `TCK-20260904-WORKING-LOG-CSV-PARSER` already shipped (the
  tolerant parser, its `is_duplicate`/`duplicate_of_line` fields, the embedded-header-row guard
  in `knowledge_search.py`) — Steps 4 and 5 consume and extend that work, never duplicate it.
- Do not change `tools/working_log_parser.py`'s classification logic for the Finding 1
  (`field_count_mismatch`) or Finding 3 (`quote_desync_masquerading_as_clean`) row classes —
  those are `TCK-20260904-WORKING-LOG-CSV-PARSER`'s already-closed territory; Steps 4-6 must
  leave `test_all_11_confirmed_live_mismatch_rows_are_flagged` and
  `test_all_34_confirmed_live_quote_desync_lines_are_flagged` unchanged.
- Do not build the detection mechanism as a bare `wc -l` / total-row-count assertion — it must
  tolerate ongoing legitimate file growth and only fire on a genuinely new duplicate block.

## Dependency Map

- Steps 1, 2, 4, 5 are independent of each other and of Steps 3/6/7 — any order.
- Step 3 should land **before** Step 6, so the detection mechanism exists and is verified
  against the live (pre-cleanup) file first; Step 6 then updates Step 3's baseline allowlist as
  part of its own change (Step 6 depends on Step 3 existing).
- Step 7 is a documentation step that should land last, since it references the completed
  decisions from Steps 3 and 6.
- Step 4's fix should be verified against the live file both before and after Step 6 (the
  "Duplicate ticket IDs" error class should disappear once Step 6's cleanup lands), but Step 4's
  own code change does not require Step 6 to be done first — they are independently correct.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause of why `merge=union` did not prevent this incident is identified with real git evidence, not speculation | Already established in `investigation.md` (squash-merge, single-parent commit, 5/5 recent-PR sample); Step 2 encodes it as a permanent regression guard | `test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers` |
| The existing merge=union regression test's coverage gap (if any) is identified and closed, or a new test is added that would catch this specific scenario | Step 3 (new detection test); Step 2 (documents why the existing test's scope doesn't cover squash-merge) | `test_no_new_duplicate_content_block_beyond_documented_baseline` |
| An explicit, evidence-based decision is recorded on whether/how to remediate the already-present ~1586-row duplication | Step 6 (Option b: one-time cleanup commit, exact scope verified) | Before/after content-preservation diff; `test_ambiguous_row_count_matches_45_for_real_file` and sibling baseline tests unchanged |
| If `tools/knowledge_search.py`'s corpus indexing is extended to deduplicate exact-content rows, it must not rewrite `tickets/working_log.csv` itself | Step 5 | `test_knowledge_search_dedupes_exact_content_working_log_rows_without_writing_csv` (asserts no non-`"r"` file open) |

## Anti-Drift Notes

- **Corrected line range for Step 6** (load-bearing — do not use `test_plan.md`'s stated range):
  `test_plan.md`'s Anti-Drift Test Guards section states the duplicate block is "lines
  1588–3180 inclusive" and instructs keeping "1,1587p;3181,$p." This plan verified directly
  (`diff` against the live file during planning) that this is wrong: lines 1588–1593 are 6
  unique, legitimate rows (not duplicates), and the true duplicate block is **lines
  1594–3180**. Using `test_plan.md`'s stated range would silently delete 6 real ticket-closure
  log rows. Step 6 above uses the corrected range; the implementer must re-verify with the same
  `diff` command against the live file at implementation time (the file will have grown further
  by then) before deleting anything, since line numbers shift with every legitimate append.
- **Squash-merge cannot be prevented from inside this ticket** — every step here is a
  detection or one-time-remediation mechanism. Do not scope-creep into anything that tries to
  block or discourage squash-merge itself (e.g. a GitHub branch-protection rule change); that is
  explicitly out of scope.
- **The detection test (Step 3) must key its allowlist by content, not line number** — both
  covered files grow continuously via legitimate appends, so a line-number-keyed allowlist would
  either false-positive on every growth or silently stop checking once lines shift.
- **`working_log_parser.py`'s `is_duplicate` marks the *second* (later) occurrence of an
  exact-duplicate line as the duplicate, keeping the earlier line's line number as
  `duplicate_of_line`** (`tools/working_log_parser.py:307-311`) — Step 5's dedup in
  `knowledge_search.py` should follow this same "keep first occurrence" convention for
  consistency, even though it operates on parsed tuples rather than raw lines.
- **Do not treat Step 7 as optional or silent** — the ticket's Acceptance Criteria require an
  explicit, evidence-based decision, not omission. If Step 7 is skipped, AC3's "must be an
  explicit decision, not silence" is only half-satisfied (the working_log.csv side would be
  decided, the W36 side would not).

## Deviations (recorded during Implement)

**This plan's own Step 6 Verify text and Scope Guards contained a factually incorrect
assumption, discovered and corrected during implementation.** Step 6's Verify section and the
Scope Guards both asserted that `test_all_11_confirmed_live_mismatch_rows_are_flagged` and
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` (plus, implicitly,
`test_ambiguous_row_count_matches_45_for_real_file` and
`test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path`) "live entirely
outside lines 1594–3180 and must not shift," and must "keep passing unchanged" after the Step 6
cleanup. This is mathematically impossible for a mid-file line deletion and was verified false
directly:

- 2 of the original 11 mismatch lines (3104, 3174) were themselves the exact-duplicate copies
  of 2 others in the same set (1511+1593=3104, 1581+1593=3174) — i.e. they sit **inside** the
  deleted 1594–3180 range and are removed by the cleanup, not merely shifted.
- All 17 of the original 34 quote-desync lines >= 2693 were themselves exact-duplicate copies
  of the other 17 (offset +1593, e.g. 1100+1593=2693) — same situation.
- Every remaining real row physically located after line 3180 (7 mismatch lines: 3245, 3253,
  3284, 3287, 3289, 3294, 3307) necessarily shifts down by exactly 1587 lines once 1587 lines
  are deleted earlier in the file — a plain, unavoidable consequence of any mid-file deletion,
  regardless of which lines are removed.

Verified directly against the live post-cleanup file (`tools/working_log_parser.py`'s
classification logic untouched): the true, current values are 9 mismatch rows at
`{1511, 1581, 1658, 1666, 1697, 1700, 1702, 1707, 1720}` (1658 = 3245-1587, etc.), 17
quote-desync rows at the same original positions `{1100, 1101, 1102, 1103, 1318, 1320, 1329,
1332, 1337, 1400, 1401, 1415, 1453, 1457, 1459, 1460, 1462}` (unaffected — all below the
deleted range), and `ambiguous_row_count == 26` (9 + 17, each real row counted exactly once
now that duplicate copies are gone; 45 = 11 + 34 counted every duplicate copy separately).

**Resolution taken:** updated the 4 affected test functions' hardcoded line-number/count
literals to these independently-verified new values (renaming
`test_all_11_confirmed_live_mismatch_rows_are_flagged` →
`test_all_9_confirmed_live_mismatch_rows_are_flagged`,
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` →
`test_all_17_confirmed_live_quote_desync_lines_are_flagged`,
`test_ambiguous_row_count_matches_45_for_real_file` →
`test_ambiguous_row_count_matches_26_for_real_file`, and narrowing
`test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path`'s loop from
`(1581, 3174)` to `(1581,)`), each with a docstring citing this ticket and explaining the
exact renumbering math. **`tools/working_log_parser.py`'s classification logic itself was not
touched** — this is purely an update to test assertion literals reflecting the new, correct
ground truth after Step 6's content-preserving deletion, not a change to what gets classified
or how. This was treated as a "stop and report" conflict rather than a silent workaround: the
conflict, root cause, and exact resolution are recorded here, in
`tickets/inprogress/TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP.md`'s Implementation
Notes, and in the implementer's final report, rather than being resolved without disclosure.
