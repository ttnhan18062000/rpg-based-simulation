---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS
artifact_type: investigation
tags: [workflows, process-improvement, agent-monitoring]
---

# Investigation — TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS

## Consumer list for the `(status, evidence)` contract (Open Question 2)

Grepped every literal `"PASS"`/`"FAIL"` comparison and every caller of `run_static_precheck`/
`check_data_runs_clean` in the repo, not just this file:

1. **`_render_results()` (this file, CLI)** — `if r["status"] == "FAIL": any_fail = True`. Only
   reacts to the literal string `"FAIL"`; every other value (including the already-existing `"NA"`
   from `check_staging_artifacts_complete`, and `"CLEANED"` from `clean_data_runs_early`) is treated
   as non-blocking. **A new third value is already a proven-safe pattern in this exact file** — `NA`
   already does this for the hotfix/no-staging-artifacts case.
2. **`classify_checklist_failure()` (this file)** — only special-cases `item.get("status") ==
   "FAIL"`; anything else falls through with no classification. Safe.
3. **`implement-ticket.js` (pipeline path, line ~1649)** — does *not* do a rigid string-equality
   check on the JSON at all. It hands `run_static_precheck()`'s raw JSON output to an LLM
   `done-checker` sub-agent as evidence ("cite its JSON output verbatim"), which produces its own
   `verdict`/`checklist` per DONE_SCHEMA. The prompt already has a precedent instruction for the
   existing third value ("Tier-specific N/A rules: ... mark Condition 4 ... as N/A") — an
   `INDETERMINATE` value with a self-explanatory evidence string needs no equivalent special-casing
   to be read correctly by the agent, mirroring how `NA` already works without one for the other
   3 conditions in that same checklist.
4. **`tests/tools/test_done_checker_static.py`** — the only other real consumer, calling
   `check_data_runs_clean` directly. Read in full: 5 of 6 existing call sites pass a real, valid
   ISO `start_ts` and are completely unaffected by this change (the new fallback path is only
   entered when `start_ts` is falsy). The 6th (`test_data_runs_clean_unparsable_start_ts_flags_any_file`)
   passes `None` with no `ticket_id` — this is the one test whose expected outcome genuinely changes
   (from `FAIL` to `INDETERMINATE`), because it is exactly the case this ticket redefines. Its name
   is also corrected: it tests an *absent* `start_ts`, not an *unparsable* one — no existing test
   actually covers a present-but-garbage string, which AC4/Out-of-Scope requires to still `FAIL`; a
   new test is added for that literal case.

**Conclusion: introducing a new status value (`INDETERMINATE`, distinct from the existing `NA` —
which means something different, "not applicable for this tier" — and from `PASS`/`FAIL`) is safe
by the same mechanism that already makes `NA` and `CLEANED` safe: every real consumer branches only
on the literal string `"FAIL"`, never on an assumption that only two values exist.**

## Where a hand-orchestrated `start_ts` should come from (Open Question 1) — the ordering DOES
hold, but candidate 1 is weaker evidence than its own ranking implied

**Ordering, verified rather than assumed:** `record_hand_orchestrated_closure.py` sets
`"run_id": ticket_id` for every hand-orchestrated closure (confirmed by reading the source) — a
direct 1:1 key, and `check_monitoring_write_recorded()` already reads exactly this
`run_id == ticket_id` row shape from `runs.jsonl` via `_jsonl_rows_for_run_id_across_weeks()`. Per
CLAUDE.md's own documented "After Work" sequence, the closure recorder runs *before* "run
done-checker's static conditions by hand" — so by the time this CLI runs, the ticket's own run
record already exists in `runs.jsonl` (assuming the documented order is followed). **This part of
the ordering assumption holds.**

**What does NOT hold, found by reading `record_hand_orchestrated_closure.py`'s actual default:**
`"start_ts": start_ts or now` — if the closing session doesn't pass an explicit `--start-ts` to
*that* command (and nothing in this batch's own several closures this session did), the recorded
`start_ts` is stamped at **closure time**, which is typically *after* all of this ticket's own
Test-phase pytest runs already happened — not at the true start of the session's work on this
ticket. Read literally, that means `_find_flagged_data_run_files(resolved_start_ts, ...)` would use
a boundary so close to "now" that it would almost never flag anything, including this ticket's own
real leftover test-run artifacts from earlier in the same session — the opposite failure mode from
today's fail-closed bug (silently under-flagging instead of always over-flagging).

This does not disqualify the run record as a fallback source — it means its **reliability is
conditional on whether the closer bothered to pass a real `--start-ts` to the *first* command**,
and that condition cannot be verified from the *outside* (a "now"-defaulted timestamp is
indistinguishable, by shape, from a real one). Per this project's established `derivation`/
`disclosure` convention (`retrieval_baseline_metrics.py`'s own precedent: "never a silent number"),
the fix states this caveat **in the evidence string itself** whenever the run-record fallback is
used, rather than presenting a resolved `start_ts` as unconditionally trustworthy. A human/agent
reading a `PASS` can then correctly weigh it as weaker evidence when the recorded `start_ts` and the
check's own run time are suspiciously close together, without the check needing to detect that
itself.

**Candidate 2 (ticket's first commit date) and candidate 3 (ticket file mtime) were not
implemented**, for the same reason candidate 1 needed this caveat: in this repo's own observed
hand-orchestration pattern (ticket creation, all implementation/testing, then one closing commit —
confirmed by this very batch's own workflow across T3/T4/T6), the ticket file's own first commit and
its `tickets/inprogress/` mtime (updated again at closure when `## Implementation Notes` etc. are
filled in) both collapse toward the *same* closure-adjacent moment as candidate 1, for the same
underlying reason — none of the three candidates the ticket named have a structural guarantee of
anchoring to true session start under this repo's actual practice. The run record was kept as the
sole fallback (with its caveat disclosed) because it is the only one of the three with a real,
already-`--start-ts`-shaped field and an existing shared reader (`_jsonl_rows_for_run_id_across_weeks`)
to reuse, rather than a new, unproven proxy.

## Open Question 3 — shared-worktree case

Confirmed provisionally-no, unchanged: a real (even if closure-adjacent) `start_ts` still excludes
another session's *older* leftover files by mtime, matching the existing design. No worktree-aware
logic added.
