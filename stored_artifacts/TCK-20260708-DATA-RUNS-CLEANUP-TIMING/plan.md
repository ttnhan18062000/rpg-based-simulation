---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-DATA-RUNS-CLEANUP-TIMING
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260708-DATA-RUNS-CLEANUP-TIMING

## Summary

Insert a deterministic, orchestrator-run cleanup checkpoint for `data/runs/*` and
`reports/release_proof/*` immediately after the Test phase and before the Parity phase in
`.claude/workflows/implement-ticket.js` — the exact point where the investigation traced the real
defect (Verify's `check_data_runs_clean`, phase 8, runs before Finalize's cleanup, phase 9, and Test
phase, phase 6, via `test-scoper`'s own pytest execution, is the actual generator of the artifacts
Verify then flags). The checkpoint is a plain Python function
(`clean_data_runs_early`, added to `tools/gate_checks/done_checker_static.py`) invoked via `bash()`
directly by the orchestrator — never an agent-prompt instruction — so it cannot be silently skipped
and is unit-testable. It reuses `check_data_runs_clean`'s exact mtime-`>=`-`start_ts` definition of
"this session's own file" via a new shared private helper, `_find_flagged_data_run_files`, which
`check_data_runs_clean` is refactored to call internally (identical external behavior — all four
existing tests must pass unmodified, this is the proof the refactor is behavior-preserving). The
checkpoint's primary behavior is auto-clean-and-log; a new blocking status,
`DATA_RUNS_CLEAN_FAILED`, is introduced only as a fail-fast fallback for the rare case where
deletion itself raises (e.g. a permission/lock error) — never for the common "found and cleaned"
case. Both the Finalize-phase prose cleanup (step 6, line 994) and `done_checker_static.py`'s
Verify-phase `check_data_runs_clean` / `run_static_precheck` stay in place unmodified as backstops.

## Decisions on the Investigation's Two Flagged Open Questions

**1. Insertion point — adopted: post-Test, pre-Parity, orchestrator-run `bash()` call.**
Neither of the ticket's two literal candidates (Implement-phase prompt addition, pre-Test
precondition) closes the actual ordering gap: Implement never runs tests/simulations (confirmed in
investigation.md by reading `implementer.md` in full), and a pre-Test precondition only catches
stale *prior*-session debris, not Test-phase's own just-generated output — the dominant failure mode
per the retro's 139/44/37/19 evidence. The insertion point that directly targets the generator is
immediately after Test phase completes (after line 688, before the `// Phase 7: Parity` comment at
line 690), mirroring the `TCK-20260705-WORKFLOW-PARITY-SKIP` precedent's shape (orchestrator runs
`bash()` directly, no new `agent()` call). Adopted as-is per investigation's recommendation — this is
explicitly permitted by the ticket's own Assumptions section ("materially different and better
insertion point... in scope").

**2. Auto-clean vs. fail-fast — adopted: auto-clean-and-log as primary, fail-fast fallback only on
deletion error.** Matches the retro's own stated goal (cut first-pass DoD failure rate without
touching real gap conditions) and AC #3's explicit "either... or" wording. A brand-new blocking
status for the *common* case (artifacts found, cleaned) would recreate exactly the friction this
ticket exists to remove. `DATA_RUNS_CLEAN_FAILED` is introduced solely for the deletion-itself-fails
case (permission error, file lock) — visible and human-actionable, never silently swallowed, per the
investigation's Anti-Drift Hazards ("do not silently swallow a new precondition/cleanup failure").
Adopted as-is per investigation's recommendation.

## Steps

### Step 1 — Extract shared flagging primitive, refactor `check_data_runs_clean` to use it
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:** Add a new private helper immediately above `check_data_runs_clean` (currently lines
92-118):

```python
def _find_flagged_data_run_files(
    start_ts: str | None,
    runs_dir: Path,
    proof_dir: Path,
) -> list[Path]:
    """Shared primitive: the canonical definition of "this session's own file" under
    data/runs/ and reports/release_proof/. A missing/unparsable start_ts is not evidence of
    cleanliness — flags any file found rather than silently passing.

    check_data_runs_clean (PASS/FAIL reporting, Verify-phase backstop) and
    clean_data_runs_early (auto-clean, post-Test checkpoint) both call this exact function so
    the two can never diverge on what counts as flaggable. Do not duplicate this walk anywhere
    else (TCK-20260708-DATA-RUNS-CLEANUP-TIMING).
    """
    start_epoch = None
    if start_ts:
        try:
            start_epoch = datetime.fromisoformat(start_ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            start_epoch = None

    flagged = []
    for directory in (runs_dir, proof_dir):
        if not directory.exists():
            continue
        for f in directory.rglob("*"):
            if not f.is_file():
                continue
            if start_epoch is None or f.stat().st_mtime >= start_epoch:
                flagged.append(f)
    return flagged
```

Then rewrite `check_data_runs_clean`'s body to call it, preserving the exact same signature and
exact same return strings:

```python
def check_data_runs_clean(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
    flagged = _find_flagged_data_run_files(start_ts, runs_dir, proof_dir)
    if flagged:
        return (
            "FAIL",
            f"File(s) at/after start_ts (or start_ts unparsable): "
            f"{', '.join(str(f) for f in flagged)}",
        )
    return ("PASS", f"{runs_dir} and {proof_dir} clean of this session's artifacts")
```

This is a behavior-preserving refactor, not a change to the mtime/`start_ts` definition itself — the
Out-of-Scope clause forbids changing *what counts as clean*, not sharing the walk between two
callers. The existing four `check_data_runs_clean` tests are the proof: they must pass byte-for-byte
unmodified after this step (see Verify below).
**Do NOT touch:** `check_ticket_location`, `check_working_log_no_row_yet`,
`check_frontmatter_valid`, `run_static_precheck`'s check ordering/aggregation, `run_finalize_selfcheck`,
or any Part B (post-Finalize) function (lines 230-294) — none of these are in scope.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — all four existing
`check_data_runs_clean`-specific tests
(`test_data_runs_clean_empty_dirs_passes`, `test_data_runs_clean_file_before_start_ts_passes`,
`test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path`,
`test_data_runs_clean_unparsable_start_ts_flags_any_file`) and both `run_static_precheck` tests must
pass with zero changes to their own test code.

### Step 2 — Add `clean_data_runs_early`
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:** Add immediately after `check_data_runs_clean` (i.e. after the refactored function from
Step 1, still within the "Part A" section, before `check_ticket_location`):

```python
def clean_data_runs_early(
    start_ts: str | None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
) -> tuple[str, str]:
    """Auto-clean this session's own data/runs/ + reports/release_proof/ artifacts immediately
    after Test phase, before Parity/Verify ever see them.

    Built for TCK-20260708-DATA-RUNS-CLEANUP-TIMING: closes the ordering gap where
    check_data_runs_clean (Verify, phase 8) ran before Finalize (phase 9, the only prior cleanup
    step) had a chance to remove anything Test phase (test-scoper) had just generated via its own
    pytest run. Invoked directly by the orchestrator (bash() call in implement-ticket.js) between
    Test and Parity — not from within an agent prompt — so it cannot be silently skipped the way
    Finalize step 6's prose cleanup instruction has been.

    Reuses _find_flagged_data_run_files's exact mtime>=start_ts / None-is-flagged definition (the
    same primitive check_data_runs_clean uses) so the two functions can never diverge on what
    counts as "this session's own file." Never a blind rm -rf: only deletes paths that definition
    flags. This guarantees only that artifacts from a session that STARTED BEFORE this session's
    start_ts are left untouched (mtime lower-bound only) — it does NOT protect against a second
    session that is concurrently/overlapping in progress at the moment this checkpoint fires,
    since data/runs/ and reports/release_proof/ have no session/PID partitioning; a file that
    other session writes with mtime >= this session's start_ts is indistinguishable from this
    session's own output and will be deleted. See "Residual Risk: Concurrent-Session Overlap
    Window" in the Anti-Drift Notes below — this is a documented, accepted tradeoff, not a
    mitigated one.

    Returns ("PASS", ...) if nothing needed cleaning, ("CLEANED", "<n> file(s) removed: ...") on
    successful auto-clean, or ("FAIL", "<error>") if deletion itself raised (e.g. permission
    error) — the one case the orchestrator escalates to a new blocking status
    (DATA_RUNS_CLEAN_FAILED) instead of silently continuing.
    """
    flagged = _find_flagged_data_run_files(start_ts, runs_dir, proof_dir)
    if not flagged:
        return ("PASS", f"{runs_dir} and {proof_dir} already clean of this session's artifacts")

    removed = []
    try:
        for f in flagged:
            f.unlink()
            removed.append(str(f))
    except OSError as e:
        remaining = [str(f) for f in flagged if str(f) not in removed]
        return (
            "FAIL",
            f"Auto-clean failed after removing {len(removed)}/{len(flagged)} file(s): {e}. "
            f"Remaining flagged: {', '.join(remaining)}",
        )
    return ("CLEANED", f"{len(removed)} file(s) removed: {', '.join(removed)}")
```

**Do NOT touch:** `run_static_precheck` — `clean_data_runs_early` is a new, separately-invoked
function; it must NOT be added to the `run_static_precheck` aggregation tuple (that stays exactly 5
checks, unchanged, per Out of Scope and per `run_static_precheck`'s own docstring "Does not collapse
to a single boolean — per-check detail must survive").
**Verify:** New unit tests from Step 3 (`test_clean_data_runs_early_*`), plus a repeat run of Step
1's regression command to confirm no accidental interference.

### Step 3 — Add new tests
**Files:** `tests/tools/test_done_checker_static.py`
**Change:** Add tests near the existing `check_data_runs_clean` test block (lines 135-193), following
the existing `tmp_path` + `os.utime()` fixture pattern:

1. `test_clean_data_runs_early_detects_and_removes_leftover_artifacts` — create files under a
   `tmp_path`-rooted `runs_dir`/`proof_dir` with `mtime >= start_ts`; call
   `clean_data_runs_early(start_ts, runs_dir, proof_dir)`; assert status `"CLEANED"`, files no
   longer exist on disk, and a subsequent `check_data_runs_clean(start_ts, runs_dir, proof_dir)`
   call now returns `"PASS"`.
2. `test_clean_data_runs_early_preserves_files_older_than_start_ts` — create a file with
   `mtime < start_ts` (simulating an artifact from a session that STARTED BEFORE this session's
   `start_ts`); call `clean_data_runs_early`; assert status `"PASS"` (nothing flagged) and the file
   still exists on disk (not deleted). Mirrors `test_data_runs_clean_file_before_start_ts_passes`
   exactly — this is the earlier-started-session safety guard test_plan.md calls "not optional."
   Note: this test covers only the mtime-lower-bound guarantee (earlier `start_ts`); it does not
   and cannot exercise the concurrent-overlap case where another session is still actively writing
   at the moment this checkpoint fires — see "Residual Risk: Concurrent-Session Overlap Window"
   below.
3. `test_clean_data_runs_early_reuses_check_data_runs_clean_definition` — build one `tmp_path`
   fixture with a mix of before/at/after-`start_ts` files; call both `check_data_runs_clean` and
   `clean_data_runs_early` against the *same* fixture (call `check_data_runs_clean` first, on a
   copy/before deletion, to capture its flagged-file list from the FAIL evidence string count, or
   more directly: call `_find_flagged_data_run_files` once and assert both public functions agree
   with it) — assert equivalent PASS/FAIL-vs-PASS/CLEANED agreement on which files are flagged, per
   test_plan.md item 3.
4. `test_clean_data_runs_early_returns_fail_on_deletion_error` — using `monkeypatch` to make
   `Path.unlink` raise `OSError` for one flagged file (or by making a file read-only / directory
   unwritable, platform-permitting), assert status `"FAIL"` and evidence mentions the error and any
   partially-removed count. Covers the new `DATA_RUNS_CLEAN_FAILED` fail-fast path.
5. `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` — new small test
   asserting the string `DATA_RUNS_CLEAN_FAILED` appears in
   `docs/ai/ticket-lifecycle.md`'s Failure Recovery Reference table (simple substring/row-shape
   check, matching test_plan.md item 4's doc-guard pattern). Add to the same test file (no separate
   `test_ticket_lifecycle_doc.py` needed for a single-status check — confirm via
   `grep -rl "ticket-lifecycle.md" tests/tools/` that no existing file already owns this; if the
   repo turns out to already have a doc-content-guard file at implementation time, add the test
   there instead).

**Do NOT touch:** Any existing test in the file — no existing test's body, fixture, or assertion
changes. `run_finalize_selfcheck` tests (lines 540-580) are untouched.
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — full file green, old test count
plus 5 new tests, zero modified existing tests (diff the test file to confirm only additions).

### Step 4 — Wire the orchestrator-run checkpoint between Test and Parity
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Insert a new block after the existing Test-phase coverage-gaps log (ends at line 688,
`if (testResult.coverage_gaps.length > 0) { ... }`) and before the `// ─── Phase 7: Parity` comment
(currently line 690). Do not call `phase()` again — this stays attributed to the Test phase's own
`pushEvent` stream rather than becoming a new named phase in `meta.phases`, to avoid touching the
phases list/monitoring schema (out of scope). Insert:

```js
// ─── Post-Test cleanup checkpoint: data/runs/ + reports/release_proof/ ────────────
// Closes the ordering gap where done-checker's data_runs_clean check (Verify, phase 8) ran
// before Finalize (phase 9) — the only phase that actually cleaned these dirs — making the
// check structurally guaranteed to fail whenever Test phase (test-scoper) generated run
// artifacts, which is nearly every standard-tier run touching simulation code. Auto-cleans this
// session's own artifacts (mtime >= startTs only — never a blind rm) immediately after Test,
// before Parity/Verify ever see them stale. This only guarantees no deletion of artifacts from
// sessions that STARTED BEFORE startTs (mtime lower-bound only) — it does NOT protect against a
// second session concurrently/overlapping in progress at this moment, since data/runs/ and
// reports/release_proof/ have no session/PID partitioning (accepted residual risk — see plan.md
// Anti-Drift Notes, "Residual Risk: Concurrent-Session Overlap Window"). Orchestrator-run bash()
// call, not an agent prompt instruction, so it can't be silently skipped
// (TCK-20260708-DATA-RUNS-CLEANUP-TIMING). Finalize step 6's own cleanup and done-checker's
// data_runs_clean check both remain in place as backstops — see docs/ai/ticket-lifecycle.md.
const cleanupOutput = await bash(
  `python3 -c "
import sys
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import clean_data_runs_early
status, evidence = clean_data_runs_early(${JSON.stringify(startTs || null)})
print(status + '|' + evidence)
"`
)
const cleanupSepIdx = cleanupOutput.indexOf('|')
const cleanupStatus = cleanupSepIdx === -1 ? cleanupOutput.trim() : cleanupOutput.slice(0, cleanupSepIdx).trim()
const cleanupEvidence = cleanupSepIdx === -1 ? '' : cleanupOutput.slice(cleanupSepIdx + 1).trim()

if (cleanupStatus === 'FAIL') {
  pushEvent('Test', 'implement-ticket-orchestrator', 'failed', `Post-Test data/runs cleanup failed: ${cleanupEvidence.slice(0, 200)}`, testResult.ts)
  log(`Post-Test data/runs cleanup FAILED: ${cleanupEvidence}`)
  await writeMonitoring('DATA_RUNS_CLEAN_FAILED')
  return {
    status: 'DATA_RUNS_CLEAN_FAILED',
    ticket_id: tid,
    message: 'Auto-clean of data/runs/*, reports/release_proof/* failed — resolve manually (check permissions/locks), then re-run with ticket_id="' + tid + '".',
    evidence: cleanupEvidence,
  }
}

if (cleanupStatus === 'CLEANED') {
  log(`Post-Test cleanup: removed leftover data/runs/ + reports/release_proof/ artifacts — ${cleanupEvidence}`)
} else {
  log('Post-Test cleanup: data/runs/ and reports/release_proof/ already clean.')
}
```

Note: `startTs` is already in JS scope from line 142 onward (`const startTs = ticketInfo.ts ||
null`), confirmed reusable without re-derivation per investigation.md Risk #4. Use
`JSON.stringify(startTs || null)` (not raw string interpolation) to pass it into the Python `-c`
one-liner safely — this correctly renders as a quoted Python string literal or `None`, avoiding the
same quote-corruption class of bug the existing `p0ScanOutput` comment (line 706-711) warns about.
**Do NOT touch:** The Test-phase agent call itself (lines 648-668), the `TESTS_FAILED` gate/return
block (lines 670-681), the Parity phase's own skip-eligibility logic (`parityNoSrcChange`,
`paritySkipEligible`, lines 694-724) — this insertion happens *before* line 690's Parity comment and
must not reorder or interleave with it. Do not touch the Finalize phase (lines ~951-1000) or its step
6 cleanup prose.
**Verify:** No `.js` test harness exists (confirmed in investigation.md) — verified by diffing the
file's phase prompts/blocks before and after this change, matching AC #1's own wording. Manually
trace: the new block reads `testResult.ts` and `startTs`, both already in scope at this point;
`cleanupStatus`/`cleanupEvidence` parsing handles the one `|`-delimited split correctly for both
`CLEANED`/`PASS` (no embedded `|` expected in those evidence strings) and `FAIL` (evidence may
contain `,` and file paths but not `|`).

### Step 5 — Update `docs/ai/ticket-lifecycle.md`
**Files:** `docs/ai/ticket-lifecycle.md`
**Change:**
1. In the **Test** section (currently lines 288-306), after the existing "Gate: Returns
   `TESTS_FAILED`..." line (305), add a new paragraph documenting the post-Test checkpoint:
   > **Post-Test cleanup checkpoint:** Immediately after Test phase completes (before Parity), the
   > orchestrator runs `tools/gate_checks/done_checker_static.py::clean_data_runs_early(start_ts)`
   > directly via `bash()` — not an agent prompt step. This auto-cleans any `data/runs/*` /
   > `reports/release_proof/*` files this session's own Test-phase pytest run produced
   > (`mtime >= start_ts`), closing the gap where Verify's `data_runs_clean` check (below) used to
   > run before Finalize's cleanup ever had a chance to execute. On success (nothing to clean, or
   > cleaned successfully) the workflow proceeds silently to Parity. **Gate:** Returns
   > `DATA_RUNS_CLEAN_FAILED` only if deletion itself errors (e.g. permission/lock) — the user
   > resolves manually and re-runs with `ticket_id`.
2. In the **Verify (Definition of Done)** section, condition 10 row (line 372, "`data/runs/`
   cleaned"), append a clarifying note: change "— script-checked" to "— script-checked; **backstop
   only** as of TCK-20260708-DATA-RUNS-CLEANUP-TIMING — primary cleanup now happens post-Test (see
   Test section above)."
3. In the **Finalize** section, step 5 (line 390, "Clean: `data/runs/*`, `reports/release_proof/*`"),
   append: "(backstop — primary cleanup happens post-Test as of
   TCK-20260708-DATA-RUNS-CLEANUP-TIMING; this step now typically finds nothing to remove)."
4. In the **Failure Recovery Reference** table (lines 475-486), insert a new row immediately after
   the `TESTS_FAILED` row (line 482) and before `SECURITY_BLOCKED` (line 483), matching phase order
   (Test → post-Test cleanup checkpoint → Parity → Security-Review):
   ```
   | `DATA_RUNS_CLEAN_FAILED` | Post-Test auto-clean of `data/runs/*`/`reports/release_proof/*` failed (deletion error, e.g. permission/lock) | Resolve the underlying error manually (check file permissions/locks), then confirm the flagged files are removable | Re-run with `ticket_id` |
   ```
**Do NOT touch:** Any other row in the Failure Recovery table, the 13-condition DoD table's other 12
rows, the Parity/Security-Review/Verify section prose beyond the two noted edits, the Epic Batch
Workflow section, the Manual Execution section.
**Verify:** Manual read-through — no automated doc test exists for this file beyond Step 3's new
`DATA_RUNS_CLEAN_FAILED`-presence test, which covers item 4 above.

## Scope Guards

- Do not modify `check_data_runs_clean`'s mtime/`start_ts` *definition* of clean — only its internal
  implementation is refactored to share `_find_flagged_data_run_files`; its signature, return values,
  and return strings must be byte-identical to before (proven by all 4 existing tests passing
  unmodified).
- Do not add `clean_data_runs_early` to `run_static_precheck`'s aggregation tuple — it is a
  separately-invoked function with its own call site, not a 6th DoD condition.
- Do not modify `run_finalize_selfcheck`, `check_migration_complete`, `check_ticket_finalized`,
  `check_working_log_exactly_one_row`, or the `FINALIZE_INCOMPLETE` status (Part B, lines 230-294) —
  explicitly Out of Scope.
- Do not remove or weaken Finalize step 6's existing cleanup prose (line 994) — it stays as a
  backstop.
- Do not touch the Parity phase's skip-eligibility logic (`parityNoSrcChange`, `paritySkipEligible`,
  `parityForceFullRun`, `find_p0_intersection`) — the new checkpoint is inserted strictly before it,
  with no interaction.
- Do not implement the checkpoint as prose inside the Test-phase or Implement-phase agent prompt —
  must be an orchestrator `bash()` call to a plain Python function.
- Do not touch `scripts/cleanup_tests.py` (process-killing tool, unrelated file-level concern per
  investigation.md).
- Do not address the second retro-flagged failure category (stale `make knowledge-index-update`,
  3/11 failures) — separate ticket, explicitly Out of Scope.
- Do not retroactively clean any currently-uncleaned historical `data/runs/`/`release_proof/`
  artifacts — this ticket fixes the pipeline going forward only.
- Do not add a `phase('Post-Test-Cleanup')` call or a new entry to `meta.phases` — the checkpoint
  stays attributed to the Test phase's event stream to avoid touching the phases list / monitoring
  schema.

## Dependency Map

- Step 1 (refactor) must land before Step 2 (`clean_data_runs_early` calls
  `_find_flagged_data_run_files`, which Step 1 creates).
- Step 2 must land before Step 3 (tests exercise `clean_data_runs_early`).
- Step 3 must land before Step 4 is considered verifiable end-to-end (though Step 4's `.js` edit is
  textually independent and could be written in parallel — sequence it after Step 3 so the Python
  side is proven correct first).
- Step 5 (docs) depends on the final shape/name of the new status (`DATA_RUNS_CLEAN_FAILED`) decided
  in Steps 2 and 4 — must land after both.
- Steps 1-3 are all within one file (`done_checker_static.py` + its test file) and can be done as one
  continuous implementation pass; Step 4 (`.js`) and Step 5 (docs) are independent of each other and
  could be done in either order, but both depend on Steps 1-3 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: `.claude/workflows/implement-ticket.js` contains an explicit cleanup step/precondition earlier than Finalize-only, verifiable by diffing phase prompts | Step 4 | Manual diff review (no `.js` test harness exists) |
| AC2: `check_data_runs_clean` / `run_static_precheck`'s `data_runs_clean` condition still exists and runs at Verify (backstop role preserved) | Step 1 (refactor preserves behavior); Step 5 item 2 (doc clarifies backstop role) | `pytest tests/tools/test_done_checker_static.py -v` — all pre-existing `check_data_runs_clean`/`run_static_precheck` tests pass unmodified |
| AC3: A new test demonstrates leftover artifacts are either auto-cleaned or cause a fail-fast signal before Test/Parity/Verify | Step 2 (`clean_data_runs_early`); Step 3 (new tests 1, 2, 4) | `test_clean_data_runs_early_detects_and_removes_leftover_artifacts`, `test_clean_data_runs_early_returns_fail_on_deletion_error` |
| AC4: `docs/ai/ticket-lifecycle.md` updated to describe new timing; new status appears in Failure Recovery Reference table | Step 5 | `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` (Step 3, test 5) |
| AC5: Running a scoped pytest command against the changed test file(s) passes | Steps 1-3 | `pytest tests/tools/test_done_checker_static.py -v` |
| AC6 (follow-up signal, not a hard gate on closure): next 5 standard-tier runs show zero Verify-phase `data_runs_clean` failures | Steps 1-4 (structural fix); tracked post-closure via `agent-monitoring/events.jsonl`, reported in next weekly retro | Not a pytest-verifiable AC — monitoring/retro follow-up only, per the ticket's own wording |

## Anti-Drift Notes

- The refactor in Step 1 is the single highest-risk step: it touches the body of a function whose
  Out-of-Scope-protected *behavior* must not change. The safety net is the four pre-existing tests —
  if any of them need to change to pass after the refactor, stop immediately; that is the signal the
  refactor accidentally altered the "clean" definition, which is forbidden.
- The earlier-started-session safety test (`test_clean_data_runs_early_preserves_files_older_than_start_ts`,
  Step 3 test 2) is not optional — test_plan.md flags this as the single highest-risk regression
  (a naive implementation collapsing into an unconditional `rm -rf`). Do not skip it under time
  pressure. Note this test proves only the mtime-lower-bound guarantee (sessions that started
  before `start_ts`) — it does not and cannot prove safety against a concurrently-overlapping
  session; see the Residual Risk subsection immediately below.

### Residual Risk: Concurrent-Session Overlap Window

`clean_data_runs_early` and `check_data_runs_clean` both define "this session's own file" as
`mtime >= start_ts` (or unparsable `start_ts`), an mtime **lower bound only**. This correctly
excludes artifacts from a session that started strictly before this session's `start_ts`. It does
**not** exclude artifacts from a second session that is concurrently/overlapping in progress at
the moment this checkpoint fires — e.g. session A starts before session B but is still mid-Test-phase
(actively writing to `data/runs/`) when session B's post-Test checkpoint runs. Any file session A
writes with `mtime >= session B's start_ts` is indistinguishable from session B's own output and
will be unlinked by session B's `clean_data_runs_early`. There is no session/PID-scoping on
`data/runs/` or `reports/release_proof/` (both are flat, shared layouts) that would allow the two
to be told apart.

This ambiguity is a **pre-existing gap already present in `check_data_runs_clean`'s own mtime-only
lower-bound logic** — it is not newly introduced by this ticket. What this ticket changes is the
**consequence** of that gap: today, a false-positive match only produces a `FAIL` that a human
reviews before Finalize's own prose cleanup step (implying judgment, not blind deletion);
`clean_data_runs_early` converts that same false-positive match into an unconditional, automatic
`f.unlink()` with no human-in-the-loop step. Promoting a passive detector into an active deleter
raises the blast radius of the same underlying ambiguity.

This is being accepted as a **documented tradeoff, not mitigated**, for this ticket: the retro
evidence motivating this ticket (139/44/37/19 leftover directories, all cited cases) traces
entirely to a session's own Test-phase output, not cross-session collision — a genuine
concurrent-overlap collision has not been observed in practice. If this residual risk becomes a
real incident, the follow-up mitigation would be a staleness margin (e.g. requiring mtime to also
predate "now" by some buffer) or session/PID-scoped subdirectories under `data/runs/` — neither is
undertaken now; both are explicitly out of scope for this ticket.
- `DATA_RUNS_CLEAN_FAILED` must only fire on a genuine deletion error, never on "found files and
  cleaned them successfully" — that success path returns `CLEANED` and the workflow continues
  silently to Parity. Confusing these two paths would reintroduce exactly the friction this ticket
  removes.
- `data/runs/{session_id}/` (simulation-run output convention referenced by
  `simulation-analyst.md`) is a different concern from the agent-workflow `data/runs/` this ticket
  cleans — do not conflate the two; `clean_data_runs_early` operates on the same `data/runs/` /
  `reports/release_proof/` paths `check_data_runs_clean` already uses, nothing new.
- Use `JSON.stringify(startTs || null)` when interpolating `startTs` into the Python `-c` one-liner
  in Step 4 — raw string interpolation of an unquoted or improperly-quoted value risks the same
  shell-quote-corruption failure class already documented in the existing `p0ScanOutput` code
  (lines 706-711 of `implement-ticket.js`).
- No new `phase()` call / `meta.phases` entry — keep the checkpoint's events attributed to the `Test`
  phase label to minimize blast radius on the monitoring schema, which is out of scope for this
  ticket to touch.

## Unresolved Questions

None. Both open questions flagged in investigation.md (insertion point; auto-clean vs. fail-fast)
have concrete decisions above, adopting the investigation's own recommendations without
modification.

## Deviations

One minor test-fixture correction, no design or production-code deviation: Step 3's test 3
(`test_clean_data_runs_early_reuses_check_data_runs_clean_definition`) as drafted in this plan
implied constructing a fixture file with `mtime` exactly equal to `start_ts`'s clock string. During
implementation this proved timezone-sensitive — `check_data_runs_clean`/`clean_data_runs_early`
parse `start_ts` as UTC (`datetime.fromisoformat(...).timestamp()`) while the test fixture pattern
used elsewhere in this file sets file mtimes via `time.mktime(time.strptime(...))`, which
interprets the same clock string as local time — so an exact-boundary fixture is nondeterministic
across host UTC offsets. Fixed by using timestamps a full day after `start_ts` for the "flagged"
fixture files, matching the margin already used by the pre-existing
`test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path` test. This does not change what
the test proves (shared-definition agreement between `check_data_runs_clean` and
`clean_data_runs_early`) — only removes an unintended timezone dependency from how the fixture
constructs its "at/after start_ts" file.
