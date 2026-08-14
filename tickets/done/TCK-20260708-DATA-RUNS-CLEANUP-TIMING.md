---
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-DATA-RUNS-CLEANUP-TIMING
phase: done
status: historical
date: 2026-07-08
tags: [ai, workflows, process-improvement]
---

# TCK-20260708-DATA-RUNS-CLEANUP-TIMING

## Title
Move data/runs/ and reports/release_proof/ cleanup earlier in the implement-ticket pipeline

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The After-Work cleanup rule in `CLAUDE.md` ("Clean up: `rm -rf data/runs/* reports/release_proof/*`",
present both under Workflow Rule > After Work at line 88 and under Definition of Done at line 213) is
currently only ever executed and cross-checked at the very end of the `implement-ticket` pipeline:
execution happens at Finalize step 6 (`.claude/workflows/implement-ticket.js` line 994, inside the
Finalize agent prompt spanning roughly lines 955-1000), and the corresponding DoD condition 10
("data/runs/ cleaned") is checked by `done-checker`'s static pre-check
(`tools/gate_checks/done_checker_static.py::check_data_runs_clean`, lines 92-118, invoked from
`run_static_precheck` at lines 173-188) at the Verify phase — several phases after Implement, Test,
and Parity, where the run artifacts actually accumulate.

Per `agent-monitoring/retro/RETRO-2026-W28.md` (2026-07-08 retro, Notes section lines 110-122), 6 of 11
failed Verify (done-checker) events this week cited uncleaned `data/runs/` as the blocking reason — one
case (`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`) had 139 leftover run directories; others had 44, 37,
and 19. This is the single largest category of first-pass DoD failure this week (6/11), ahead of the
second-largest category (stale knowledge-index, 3/11 — out of scope for this ticket, see Out of Scope).
The retro's own recommendation (lines 119-122) is to move the cleanup earlier in the pipeline rather
than rely on done-checker to catch it at Verify.

## Scope
- Investigate and select an earlier enforcement point for the `data/runs/*` and
  `reports/release_proof/*` cleanup than the current Finalize-phase-only approach. Candidates to
  evaluate (per the request's proposed direction, not prescriptive): an explicit cleanup step added to
  the Implement-phase agent prompt in `.claude/workflows/implement-ticket.js` (currently lines
  514-542), and/or a precondition check before the Test phase (test-scoper invocation) that fails fast
  if run artifacts from a prior session are present.
- Whichever insertion point is chosen, `done_checker_static.py::check_data_runs_clean` /
  `run_static_precheck`'s `data_runs_clean` condition (lines 92-118, 173-188) must remain in place as a
  backstop — it is not being removed, only demoted from primary-enforcement to safety-net.
- Update `.claude/workflows/implement-ticket.js` to add the earlier cleanup step/precondition.
- Update `docs/ai/ticket-lifecycle.md`'s phase-by-phase documentation (the Implement and/or Test
  section, and the Finalize section's existing "data/runs/, reports/ cleaned" line at ~383) to reflect
  the new timing, keeping the Verify-phase `data_runs_clean` backstop condition documented as a
  backstop rather than the primary check.
- If a precondition/failure path is added, define its return status and add it to the Failure Recovery
  Reference table in `docs/ai/ticket-lifecycle.md` (mirroring existing rows like `TESTS_FAILED`,
  `DOD_BLOCKED`).
- Add/update tests covering the new cleanup step or precondition logic (e.g. under
  `tests/tools/` alongside existing `done_checker_static.py` coverage, or workflow-level tests if any
  exist for `implement-ticket.js`).

## Out of Scope
- The second retro-flagged failure category (3/11: stale `make knowledge-index-update` after `docs/`
  edits) — a separate concern with its own fix path; not addressed by this ticket.
- Any change to what counts as "clean" (the `check_data_runs_clean` mtime-based flagging logic itself,
  lines 92-118) — this ticket changes *when* cleanup/checking happens in the pipeline, not the
  definition of cleanliness.
- Changes to `reports/release_proof/*` generation logic or `data/runs/*` artifact generation itself —
  only the cleanup/enforcement timing is in scope.
- Retroactively cleaning up any currently-uncleaned `data/runs/` or `reports/release_proof/` artifacts
  from past runs — this ticket fixes the pipeline going forward, not historical debt.
- Changes to the Finalize-phase self-check (`run_finalize_selfcheck`, lines 283+) or its
  `FINALIZE_INCOMPLETE` status — that check covers post-Finalize migration verification, a distinct
  concern from data/runs cleanup timing.

## Acceptance Criteria
- `.claude/workflows/implement-ticket.js` contains an explicit cleanup step or precondition for
  `data/runs/*` and `reports/release_proof/*` at a pipeline point earlier than the current
  Finalize-only step (line 994), verifiable by diffing the file's phase prompts before/after.
- `tools/gate_checks/done_checker_static.py::check_data_runs_clean` /
  `run_static_precheck`'s `data_runs_clean` condition still exists and still runs at Verify (backstop
  role preserved) — verified by running the existing test suite for `done_checker_static.py` with no
  regressions.
- A new test (or updated existing test) demonstrates that run artifacts left over from a prior session,
  when present before the new earlier checkpoint, are either cleaned automatically or cause a
  fail-fast, human-actionable signal before Test/Parity/Verify are reached.
- `docs/ai/ticket-lifecycle.md` is updated to describe the new cleanup timing, and if a new failure/return
  status was introduced, it appears in the Failure Recovery Reference table.
- Running a scoped pytest command against the changed test file(s) passes.
- The next 5 completed `implement-ticket` runs (standard tier, tracked via
  `agent-monitoring/events.jsonl`) show zero Verify-phase failures citing uncleaned `data/runs/` as the
  reason — noted as a follow-up verification signal in the next weekly retro, not a hard gate on this
  ticket's own closure (the ticket cannot itself wait 5 future runs to close).

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER (done) — built `done_checker_static.py`, including
  `check_data_runs_clean` and `run_static_precheck`, as the deterministic backstop this ticket must not
  remove or weaken.
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK (referenced in `docs/ai/ticket-lifecycle.md` lines 137-143) —
  precedent for the same class of fix: moving a check from a late Verify-phase DoD condition
  (`frontmatter_valid`) to an earlier Scope-phase gate (`TAGS_NOT_REGISTERED`), 6+ phases sooner. This
  ticket applies the same pattern to `data_runs_clean`.
- TCK-20260705-WORKFLOW-PARITY-SKIP (referenced in `docs/ai/ticket-lifecycle.md` lines 328-331) — same
  general precedent class of tightening pipeline timing/skip logic in `implement-ticket.js`.
- TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS (done) — the concrete 139-leftover-run-directory case
  cited in the retro as motivating evidence.

## Related Docs
- `CLAUDE.md` — Workflow Rule > After Work (line 88: "Clean up: `rm -rf data/runs/* reports/release_proof/*`")
  and Definition of Done (line 213: "Temporary run data cleaned: `data/runs/`, `reports/release_proof/`").
- `docs/ai/ticket-lifecycle.md` — Implement section (~lines 225-247), Finalize section (~lines 379-397,
  cleanup at step 5/line 390), Verify/DoD table (condition 10, ~line 372), Failure Recovery Reference
  table (~lines 473-486).
- `agent-monitoring/retro/RETRO-2026-W28.md` — Notes section (~lines 110-122), source of the 6/11
  failure-rate evidence and the recommendation this ticket implements.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/` (investigation.md, plan.md, test_plan.md) —
  prior investigation covering `done_checker_static.py`'s design, including `check_data_runs_clean`'s
  mtime-based flagging rationale.
- No prior stored artifact found specifically addressing cleanup *timing* (as opposed to cleanup
  *detection*) — this appears to be the first ticket targeting the timing problem directly.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` — Implement phase agent prompt (lines 497-542), Test phase
  (immediately following, not yet read in detail — to be covered by Investigate), Finalize phase agent
  prompt (lines 951-1000, cleanup step at line 994).
- `tools/gate_checks/done_checker_static.py` — `check_data_runs_clean` (lines 92-118),
  `run_static_precheck` (lines 173-188), `run_finalize_selfcheck` (line 283+, not to be modified).
- `docs/ai/ticket-lifecycle.md` — pipeline documentation requiring updates to match the new timing.
- `tests/tools/` — likely home for new/updated tests of the relocated check (exact existing test file
  for `done_checker_static.py` to be confirmed during Investigate).

## Assumptions / Open Questions
- Assumes the correct insertion point is somewhere in Implement or Test phase, per the request's
  proposed direction — the actual best point (single earlier step vs. precondition vs. both) is left to
  Investigate/Plan to determine and is not prescribed here. If Investigate finds a materially different
  and better insertion point (e.g. a dedicated new micro-phase), that is in scope as long as the
  Finalize-phase backstop and `done_checker_static.py`'s `data_runs_clean` condition are preserved.
- Assumes `layer: ai` is correct since this is Claude agent workflow tooling (`docs/ai/` domain), not
  gameplay simulation code — consistent with the tag registry's explicit note that this repo's
  `layer:ai` means the Claude agent system, not gameplay AI/cognition.
- Assumes this is process/workflow tooling with no Mechanics Bible or Engine Contract overlap, and no
  parity ledger entry applies — confirmed: no `docs/parity_ledger/*.yaml` file references `data/runs`
  or `release_proof`. Not applicable.
- Open question for Investigate: whether the Implement-phase agent (which does not always run
  simulations) is the right actor to own this cleanup, versus test-scoper (which does run simulations
  and is more likely to be the actual source of new `data/runs/` artifacts) — the request suggests both
  as candidates and defers the choice.
- If wrong that 6/11 failures this week are representative rather than a one-off spike, the acceptance
  criterion's "next 5 runs" follow-up signal may need a longer observation window — flagged as a
  post-closure monitoring concern, not a blocker to implementation.

## Implementation Notes

Implemented all 5 plan steps exactly as specified in `staging_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/plan.md`:

1. **Extracted `_find_flagged_data_run_files`** in `tools/gate_checks/done_checker_static.py`, and
   refactored `check_data_runs_clean` to call it. Ran the 4 pre-existing `check_data_runs_clean`
   tests (plus the 2 `run_static_precheck` tests) before adding any new code — all 36
   pre-existing tests in `tests/tools/test_done_checker_static.py` passed unmodified, confirming
   the refactor is behavior-preserving. `check_data_runs_clean`'s signature and return strings are
   byte-identical to before.
2. **Added `clean_data_runs_early(start_ts, runs_dir, proof_dir)`** immediately after
   `check_data_runs_clean`, using the plan's exact docstring wording (the "started before this
   session's start_ts" framing and the full Residual Risk cross-reference). It reuses
   `_find_flagged_data_run_files`, returns `("PASS", ...)` when nothing is flagged,
   `("CLEANED", "<n> file(s) removed: ...")` on successful auto-clean, and `("FAIL", ...)` only if
   `Path.unlink()` itself raises `OSError`. Not added to `run_static_precheck`'s aggregation tuple
   (still exactly 5 checks).
3. **Added 5 new tests** to `tests/tools/test_done_checker_static.py`:
   `test_clean_data_runs_early_detects_and_removes_leftover_artifacts`,
   `test_clean_data_runs_early_preserves_files_older_than_start_ts`,
   `test_clean_data_runs_early_reuses_check_data_runs_clean_definition`,
   `test_clean_data_runs_early_returns_fail_on_deletion_error` (via `monkeypatch.setattr(Path, "unlink", ...)`),
   and `test_data_runs_clean_status_appears_in_failure_recovery_reference_table`. Confirmed via
   `grep -rl "ticket-lifecycle.md" tests/tools/` that no existing doc-guard test file already
   owned this check, so it was added to `test_done_checker_static.py` per the plan's fallback.
   Full file: 41/41 passing (36 pre-existing + 5 new).
4. **Wired the post-Test cleanup checkpoint** into `.claude/workflows/implement-ticket.js`,
   inserted between the Test phase's coverage-gaps log (previously ending at line 688) and the
   `// ─── Phase 7: Parity` comment, using the plan's exact inline comment wording verbatim. Reused
   the already-in-scope `startTs` variable (from line 142) via `JSON.stringify(startTs || null)` —
   no new timestamp derivation. Returns `DATA_RUNS_CLEAN_FAILED` (new blocking status, pushes a
   `failed` event, calls `writeMonitoring`) only when `clean_data_runs_early` itself returns
   `"FAIL"` (a genuine deletion error); the `"CLEANED"` and `"PASS"` paths log and fall through
   silently to Parity. `node --check` confirms the file still parses as valid JS syntax.
5. **Updated `docs/ai/ticket-lifecycle.md`**: added the "Post-Test cleanup checkpoint" paragraph
   to the Test section (after the `TESTS_FAILED` gate line); appended the backstop-only note to
   DoD condition 10's row; appended the backstop note to Finalize step 5's cleanup line; and added
   the `DATA_RUNS_CLEAN_FAILED` row to the Failure Recovery Reference table (inserted after
   `TESTS_FAILED`, before `SECURITY_BLOCKED`, mirroring the `TAGS_NOT_REGISTERED` row's 4-column
   shape).

No deviations from the plan. One implementation-level note not called out as a deviation: Step 3
test 3 (`test_clean_data_runs_early_reuses_check_data_runs_clean_definition`) originally used a
file with `mtime` set to the exact same clock-string as `start_ts` (both "2026-07-05T00:00:00",
one parsed as UTC via `datetime.fromisoformat`, the other as local time via `time.mktime`), which
is timezone-sensitive and failed non-deterministically depending on the host's UTC offset. Adjusted
the fixture to use timestamps a full day after `start_ts` (mirroring the existing
`test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path` pattern) — this is a test-fixture
correctness fix within the scope of writing the test the plan specified, not a change to the plan's
design or to production code.

## Test Summary

`pytest tests/tools/test_done_checker_static.py -v` — 41 passed, 0 failed (36 pre-existing tests
unmodified and green, proving the Step 1 refactor is behavior-preserving; 5 new tests covering
`clean_data_runs_early`'s auto-clean, mtime-lower-bound preservation, shared-definition agreement
with `check_data_runs_clean`, deletion-error fail-fast path, and the new status's presence in the
Failure Recovery Reference table).

No `.js` test harness exists for `implement-ticket.js` (confirmed in investigation.md) — verified
by `node --check` (valid syntax) and manual read-through tracing `testResult.ts`/`startTs` scope
and the `|`-delimited output parsing.

## Files Changed

- `tools/gate_checks/done_checker_static.py` — added `_find_flagged_data_run_files` and
  `clean_data_runs_early`; refactored `check_data_runs_clean` to call the shared helper
  (behavior-preserving).
- `tests/tools/test_done_checker_static.py` — added 5 new tests for `clean_data_runs_early` and
  the new Failure Recovery Reference table row.
- `.claude/workflows/implement-ticket.js` — added the post-Test cleanup checkpoint `bash()` block
  between the Test and Parity phases; introduced the `DATA_RUNS_CLEAN_FAILED` return status.
- `docs/ai/ticket-lifecycle.md` — documented the new post-Test checkpoint, marked DoD condition 10
  and Finalize step 5 as backstop-only, and added the `DATA_RUNS_CLEAN_FAILED` row to the Failure
  Recovery Reference table.

## Completion Summary

Moved the primary `data/runs/*` / `reports/release_proof/*` cleanup enforcement point from
Finalize-phase-only (after Verify's check already ran) to a new deterministic, orchestrator-run
`bash()` checkpoint immediately after Test phase and before Parity — closing the ordering gap that
caused 6/11 first-pass Verify failures in the 2026-W28 retro. `check_data_runs_clean` and
`run_static_precheck` remain in place unmodified as the Verify-phase backstop; Finalize step 6's
cleanup prose remains in place unmodified as the final backstop. A new `DATA_RUNS_CLEAN_FAILED`
status fires only on a genuine deletion error, never on the common "found and cleaned" case.

**Residual risk, accepted and unresolved:** `clean_data_runs_early` shares `check_data_runs_clean`'s
pre-existing mtime-lower-bound-only definition of "this session's own file" (`mtime >= start_ts`) — an
ambiguity that already existed in `check_data_runs_clean` and is not newly introduced by this ticket.
What this ticket changes is the consequence of that ambiguity: a false-positive match now triggers an
automatic, irreversible `f.unlink()` immediately after Test phase, rather than the pre-existing passive
`FAIL` that a human reviews before Finalize's own cleanup step — raising the blast radius of the same
underlying gap. This is accepted as a documented tradeoff, not mitigated, because the retro evidence
motivating this ticket (139/44/37/19 leftover directories) all traced to a session's own Test-phase
output, not cross-session collision — no genuine concurrent-overlap collision has been observed in
practice. No follow-up ticket is being filed now; if this residual risk ever manifests as a real
incident, the fix would be a staleness margin or session/PID-scoped subdirectories under `data/runs/`,
noted here as a future mitigation path rather than committed work. See
`staging_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/plan.md`'s "Residual Risk: Concurrent-Session
Overlap Window" section (moving to `stored_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/plan.md` at
Finalize) for full detail.
