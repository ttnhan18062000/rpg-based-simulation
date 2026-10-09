---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-GATE-LEDGER-SELFCHECK-FALSE-UNRESOLVED-BLOCKS
phase: done
date: 2026-10-09
tags: [agent-monitoring, data-quality]
---

# TCK-20261009-GATE-LEDGER-SELFCHECK-FALSE-UNRESOLVED-BLOCKS

## Title
The gate ledger shows 31 unresolved finalize self-check blocks on closed tickets; most are post-close precheck false fails and a derivation that only looks one verdict ahead

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by the 2026-W41 retro addendum at 188 runs (`agent-working/agent-monitoring/retro/RETRO-2026-W41.md`, Notes,
`retro-note runs=188 final`). `gate_ledger.py list --unresolved` lists 31 blocking verdicts, all with gate
`Finalize:gate_checks.done_checker_static.run_finalize_selfcheck`. Every ticket concerned is closed and merged. On
2026-10-07 the count was 0. The ledger exists to show a gate someone silently ignored. With this noise in it, an actual
override cannot be seen. Owner approved filing on 2026-10-09.

Measured 2026-10-09 over the W40–W41 `*gate_verdicts.jsonl` shards (origin/main `f446a2bc8`):

| Group | Count | Sub-results |
|---|---|---|
| Precheck ran on a closed ticket | 24 | `finalize.ticket_finalized` = PASS, yet `precheck.*` present and failing (`ticket_location`, `working_log_no_row_yet`, `frontmatter_valid`, `ticket_field_values_valid`) |
| Finalize-only runs with real failing conditions | 7 | `finalize.registry_entry_regenerated` 5, `finalize.working_log_exactly_one_row` 5, `finalize.migration_complete` 3 (overlapping) |

Later verdicts on the same ticket and gate: 21 have none, 8 have only later FAILs, and 2 have a later PASS that did
not resolve them.

Two causes are known or likely:
1. **Precheck on a closed ticket (cause not yet confirmed).** `done_checker_static.py main()` already defaults
   `--part` to `finalize` when `check_ticket_finalized()` PASSes (since #261, 2026-09-30, which is older than verdict
   recording in #369, 2026-10-06). In all 24 rows the same function returned PASS in the same run, so the auto-detect
   should have skipped precheck. Most likely cause: callers pass `--part both` explicitly, maybe copied from a guide or
   ticket text. Unconfirmed, because the tools.jsonl `input_summary` truncates the command. The recorded verdict then
   carries the precheck's expected post-close FAILs as a blocking verdict under the finalize gate_id. `gate_id_for()`
   uses `run_finalize_selfcheck` for any part other than `precheck`.
2. **Derivation looks one verdict ahead (confirmed by reading).** `gate_ledger.py::derive_outcomes()` compares each
   blocking verdict only with the very next verdict on the same (ticket, gate). The sequence FAIL(a) -> FAIL(b, other
   inputs) -> PASS leaves FAIL(a) unresolved, even though the gate was eventually fixed.

## Scope
1. **Confirm cause 1** from tools shards (full rows, not the truncated summary), handover notes and guides. Grep
   `docs/`, `.claude/`, `CLAUDE.md` and the closure tooling for an instruction that yields `--part both` after close.
   Record what you find in Implementation Notes.
2. **Stop the precheck's post-close FAILs from being recorded as finalize blocks.** Record Part A and Part B as two
   verdict rows with their own gate_ids (`run_static_precheck` with phase Verify, `run_finalize_selfcheck` with phase
   Finalize), each with its own verdict and blocking flag. This applies even under `--part both`. When `--part both` is
   passed on a ticket that `check_ticket_finalized()` reports closed, print a warning and record the precheck row as
   non-blocking, marked in `sub_results` or `inputs_ref` as post-close. Fix any guide text found in step 1.
3. **Derivation:** in `derive_outcomes()`, a blocking verdict is `fixed_and_rerun` when **any** later verdict on the
   same (ticket, gate) passes. The follow-up id is the first passing one. `rerun_no_change` keeps its next-verdict
   meaning. Explicit outcomes still win (`resolved_view`).
4. **Existing rows:** do not edit or delete ledger rows (they are append-only). For the 24 precheck-on-closed rows,
   record an adjudication (or an outcome, whichever the ledger's own vocabulary fits; check `gate_ledger.py` and
   `docs/guides/delivery_process.md` "Recording what you did about a gate verdict") that names this ticket as the
   reason. For the 7 real finalize failures, check each ticket's current state on main. If the condition now holds,
   record what happened; if it does not, list it in the Completion Summary. Do not paper over a real one.
5. Tests in `tests/tools/` for: the split recording (both parts, closed and open ticket), derivation over
   FAIL -> FAIL(other inputs) -> PASS, and FAIL -> PASS still deriving as before.

## Out of Scope
- Changing which conditions precheck or finalize check.
- The retro's Gates section layout (it reads the ledger; it should pick the change up unchanged, so verify it does).
- Adjudicating verdicts from other gates.

## Acceptance Criteria
- AC1: The cause of precheck running on closed tickets is stated with evidence, or stated as not found with what was
  searched.
- AC2: A `--part both` run on a closed ticket records no blocking verdict under the finalize gate_id from precheck
  conditions. A test pins this.
- AC3: `derive_outcomes()` resolves FAIL -> FAIL(other inputs) -> PASS as `fixed_and_rerun`. A test pins this, and the
  existing derivation tests still pass.
- AC4: After the change and the step-4 records, `gate_ledger.py list --unresolved` lists only verdicts with a real,
  named open problem. The Test Summary lists the before and after count and each remaining id with its reason.
- AC5: No existing ledger row is edited or removed (git diff on `*gate_verdicts.jsonl` is append-only).
- AC6: Scoped tests pass: `tests/tools/` for gate_ledger and done_checker_static; also grep `tests/` for textual
  readers of the changed gate_id strings.

## Related Tickets
- TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS (#261): added the closed-ticket auto-detect.
- TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES (#369): verdict recording from this CLI.
- TCK-20261009-GATE-LEDGER-OUTCOME-ON-ORPHAN-ATTESTED-ROW (#459): last change to outcome recording.
- TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER (time-gated, after W42): reads this ledger. This fix makes its data usable.

## Related Docs
- `docs/guides/delivery_process.md` ("Recording what you did about a gate verdict")
- `docs/agent-monitoring/schema.md` (gate_verdicts rows)
- `agent-working/agent-monitoring/retro/RETRO-2026-W41.md` (Notes, 2026-10-09 addendum)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/gate_checks/done_checker_static.py` (`main()`, part selection, `record_gate_verdict` call)
- `tools/agent-monitoring/gate_ledger.py` (`derive_outcomes`, `resolved_view`, the outcome and adjudicate commands)
- `tools/agent-monitoring/gate_verdicts.py` (`gate_id_for`, `record_gate_verdict`)

## Assumptions / Open Questions
- Assumes splitting into two rows is acceptable for the retro's Gates table (a new `run_static_precheck` row appears).
  If a reader keys on the old single row, say so in the Test Summary.
- The `search_docs` index is not built and this worktree has no graphify graph. The duplicate scan was a grep over
  `agent-working/tickets/` for precheck, selfcheck and gate-ledger; no duplicate was found.

## Implementation Notes
Cause 1 (AC1): no tracked doc, guide, agent card, workflow or closure tool passes `--part both` (grep of `docs/`, `.claude/`, `CLAUDE.md`, `tools/`: only the CLI's own help text names it). The source was the implementer's private handover note, whose hand-close recipe said `done_checker_static.py --part both`; after a direct-to-done close that runs precheck on a closed ticket. The note is outside the repo and was corrected in this session's handover. The tools shards truncate the command, so the 24 rows are attributed by this one remaining source, not by a captured command.
Code: `done_checker_static.py main()` now records two rows (precheck: `cli:done_checker_static`, phase Verify; finalize: `Finalize:...run_finalize_selfcheck`); precheck on a closed ticket warns, is non-blocking, carries `inputs_ref.post_close`, and is left out of the exit code. `gate_ledger.derive_outcomes()`: next block with the same inputs stays `rerun_no_change`; otherwise any later pass is `fixed_and_rerun` (first passing row is the follow-up). The `delivery_process.md` ledger paragraph says so.

## Test Summary
`pytest tests/tools/test_gate_ledger.py tests/tools/test_gate_verdicts.py tests/tools/test_done_checker_static.py`: 235 passed before the precedence tweak; ledger and verdicts files 61 passed after. New: FAIL -> FAIL(other inputs) -> PASS (both resolve to the pass), same-inputs rerun then pass, `--part both` on a closed ticket (non-blocking post_close precheck row, separate gate_ids, warning) and on an open ticket (blocking precheck row). Existing FAIL -> PASS tests unchanged and green. Textual readers of the gate_id strings in `tests/` checked: test_proof_plan_advisory, test_finalize_knowledge_index_refresh, test_cited_evidence_advisory, test_done_checker_static call the functions, not the recorded id; test_gate_verdicts pins that `run_static_precheck` maps to `cli:done_checker_static`, which still holds.
Unresolved count (`list --unresolved`): 31 before this ticket's code, 29 with the new derivation alone, 2 after the records below. Records (append-only, no row edited): 23 precheck-on-closed rows got outcome `accepted` plus adjudication `false_block` naming this ticket; 4 real finalize failures (SESSION-GUARD-QUOTED-TEXT-FALSE-POSITIVE, TESTING-OWNS-TEST-CI-WORKFLOWS, VISUAL-ASSETS-ICON-V2-DRAFT-SET, VISUAL-ASSETS-ICON-THEME-FIT) now pass on main: I re-ran `--part finalize` for each (recorded), which derives `fixed_and_rerun`.
Remaining, real: `gv-e63a2f3310054cab` and `gv-916c43b075a3444b`, both TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS: closed at tier standard with no `plan.md`, `investigation.md`, `test_plan.md` in `agent-working/stored_artifacts/` (`finalize.migration_complete` FAIL on main today). Left open on purpose. The retro Gates section reads the ledger unchanged; a new `cli:done_checker_static` precheck row will appear there. Not run: the retro report itself.

## Files Changed
`tools/gate_checks/done_checker_static.py`, `tools/agent-monitoring/gate_ledger.py`, `docs/guides/delivery_process.md`, `tests/tools/test_gate_ledger.py`, `tests/tools/test_gate_verdicts.py`, new rows in this branch's `*.gate_verdicts.jsonl` and `gate_outcomes`/adjudication shards.

## Completion Summary
Split precheck and finalize verdict rows, derive `fixed_and_rerun` from any later pass, and cleared the ledger to 2 open ids, both genuine (PERF-LANE ticket closed without its stored artifacts; a follow-up ticket for that is the planner's call). AC1-AC6 met; AC4's remaining ids are listed above.
