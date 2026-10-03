---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING
artifact_type: plan
tags: [workflows, process-improvement]
---

# Plan — TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING

Implements Option A from investigation.md §3: a new "epic ticket close" step in
`.claude/workflows/implement-epic.js`, added immediately after the existing folder-mode cleanup
block, guarded on `epicId` instead of `folder`.

## Scope Guards

- Do not touch `create-tickets.js` or `implement-ticket.js` — investigation.md §1/§3 confirmed
  both are the wrong lifecycle stage or architecturally unable to host this step.
- Do not remove `EPIC_SCOPED` from `tools/ticket_field_values.py::WORKFLOW_STATUS_VALUES` — it
  stays valid for its original mid-flight meaning (investigation.md §4).
- Do not re-normalize the 6 existing EPIC_SCOPED-in-`tickets/done/` epics — out of scope per the
  ticket text.
- Do not modify `tools/validate_frontmatter.py::check_ticket_location_consistency` or its corpus
  test — consumed as-is.

## Step 1 — new "Epic close" step in `implement-epic.js`

Location: immediately after the existing folder-cleanup block (`implement-epic.js:387-411`), before
`phase('Report')`. Guarded `if (batchStatus === 'DONE' && epicId)` — the `epic_id`-mode mirror of
the folder-mode `if (batchStatus === 'DONE' && folder)` guard directly above it.

Uses the existing `writeSidecar` helper (next free negative seq slot: `-5`, since folder-cleanup
already claimed `-3` and the batch-monitoring-write claimed `-2`, tracking-doc-update claimed `-4`
— confirmed by reading every existing `writeSidecar(-N, ...)` call site before picking the next
number, not guessed).

Agent prompt (mirrors the folder-cleanup block's own shape and tone — bookkeeping, never fails the
workflow):

```
Close the epic ticket itself now that all its children are done. This is bookkeeping — do NOT
fail the workflow if anything goes wrong.

The epic "${epicId}" (at "${discovery.epic_ticket_path}") had all ${ticketIds.length} child
ticket(s) implemented successfully. Close the epic ticket file itself:

Step 1 — read the epic ticket at "${discovery.epic_ticket_path}".
  If the file does not exist (already closed in a prior run), print "SKIPPED: epic ticket file
  not found" and return "done".

Step 2 — update the file:
  - In the YAML frontmatter block at the top: set `phase: done` and `status: historical`
  - Set the body `## Status` section to DONE (not EPIC_SCOPED — see
    TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING investigation.md §4: EPIC_SCOPED is this
    ticket's own mid-flight scoped-but-not-yet-resolved meaning, not a terminal state for an
    epic every one of whose children is confirmed done)
  - If a "## Completion Summary" section exists and is empty, fill it with one sentence noting
    all ${ticketIds.length} child ticket(s) completed via this batch run.

Step 3 — move the file:
  If the epic ticket is not already under tickets/done/, move it there:
    Run: mv "${discovery.epic_ticket_path}" "tickets/done/${epicId}.md"
  If it is already under tickets/done/ (already closed in a prior run), skip this step.

Step 4 — print "Closed epic ${epicId} -> tickets/done/${epicId}.md" (or the SKIPPED message from
Step 1/3 if applicable).

Return "done".
```

Followed by `log('Closed epic ${epicId}')` (mirroring the folder-cleanup block's own lack of an
extra log line is fine too — folder-cleanup doesn't log separately either, relying on the agent's
own printed output. Match that: no extra `log()` call needed beyond what the agent itself prints).

## Step 2 — raw-source-text pin tests

New test file `tests/tools/test_implement_epic_close_step.py`, following
`tests/tools/test_finalize_phase_status_instruction_pin.py`'s established pattern for `.js`
workflow files (no JS test runner exists in this repo):

1. `test_epic_close_step_sets_phase_done_and_status_historical` — asserts the frontmatter
   instruction string is present.
2. `test_epic_close_step_sets_body_status_done_not_epic_scoped` — asserts the body-status
   instruction says DONE, and that the string `EPIC_SCOPED` appears in the surrounding block only
   as an explanatory contrast (i.e. the literal instructed value is DONE), not as what gets written.
3. `test_epic_close_step_moves_file_to_tickets_done` — asserts the `mv ... tickets/done/${epicId}.md`
   instruction is present.
4. `test_epic_close_step_is_guarded_on_epic_id_mode` — asserts the new block's guard condition
   references `epicId` (not `folder`), confirming it doesn't accidentally piggyback on the
   folder-mode guard.
5. `test_epic_close_step_runs_after_folder_cleanup_and_before_report_phase` — index-ordering
   check: folder-cleanup block's own guard string precedes the new epic-close block's guard
   string, which itself precedes `phase('Report')`.
6. `test_epic_close_step_is_a_bookkeeping_step_that_never_fails_the_workflow` — asserts the "do
   NOT fail the workflow" bookkeeping framing is present in the new block, matching the existing
   folder-cleanup and batch-monitoring-write blocks' own established convention.

## Step 3 — Document-Update

`implement-epic.js` and `create-tickets.js` are workflow files, not `docs/`, so the doc-staleness
gate does not apply (no `src/`/`config/` path touched). Nothing under `docs/` describes
`implement-epic.js`'s own step-by-step behavior in enough detail to need updating for this internal
change — confirmed via `search_docs` during Investigate (no hit describing implement-epic's
completion-time steps beyond the ticket/investigation corpus itself, which this ticket's own
Completion Summary will update).

## Acceptance Criteria Map

- AC1 (frontmatter phase/status + move to tickets/done/) → Step 1, Step 2's tests 1 and 3.
- AC2 (body ## Status resolved, DONE chosen as canonical) → investigation.md §4, Step 1, Step 2's
  test 2.
- AC3 (test proves the step fires, raw-source-text pin) → Step 2.
- AC4 (`check_ticket_location_consistency` passes without a follow-up bulk-remediation ticket) →
  satisfied by Step 1 writing the exact frontmatter values that rule requires; verified in Test
  phase by hand-running the validator against a synthetic epic ticket file with the new step's
  exact frontmatter values.
