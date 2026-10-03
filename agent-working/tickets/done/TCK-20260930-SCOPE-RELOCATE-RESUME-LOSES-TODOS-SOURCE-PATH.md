---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-SCOPE-RELOCATE-RESUME-LOSES-TODOS-SOURCE-PATH
phase: done
date: 2026-09-30
tags: [ai]
---

# TCK-20260930-SCOPE-RELOCATE-RESUME-LOSES-TODOS-SOURCE-PATH

## Title
A resumed `implement-ticket` run loses `todos_source_path`, so Finalize never deletes the `tickets/todos/` copy

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/agent-monitoring/scope_ticket_relocate.py` returns `{"todos_source_path": "", "action":
"already_in_inprogress"}` when the ticket is already in `tickets/inprogress/` (lines ~53-54).
On a resumed run the Finalize prompt then says "No todos source path recorded — skip" and the
`tickets/todos/` copy is never deleted, and the Verify prompt omits the "expected todos duplicate"
note, so done-checker would flag the leftover. Reported by test-architecture-implementer
(2026-10-01) from a real run of `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP`: the first
Scope returned the real path with `action: copied_from_todos`; the second and third Scope returned
`""`. They passed the original path by hand to both prompts. I confirmed the empty-string returns
by reading the script.

## Scope
1. On `already_in_inprogress`, still report the todos source path when a copy remains in
   `tickets/todos/` (derive it from the filesystem, not from run state), or carry the first Scope's
   value across a resume. Pick the route that needs no new durable state, and say why.
2. Make sure Finalize and Verify prompts receive it on a resumed run.
3. Regression test: ticket in both `inprogress/` and `todos/` returns the todos path with the
   `already_in_inprogress` action; ticket only in `inprogress/` still returns `""`.

## Out of Scope
- Other resume-state loss (`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` is separate).

## Acceptance Criteria
1. A resumed run with a surviving todos copy reaches Finalize with the correct path.
2. The regression test above passes; existing `scope_ticket_relocate` tests pass unchanged.

## Related Tickets
- TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP (run that exposed it)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/scope_ticket_relocate.py`
- `.claude/workflows/implement-ticket.js` (Scope result use, Finalize and Verify prompts)

## Assumptions / Open Questions
- The first `copied_from_todos` result is gone after a resume, so the value has to be recoverable.

## Implementation Notes
**Route chosen: derive from the filesystem.** On `already_in_inprogress`, `resolve_and_relocate_ticket` now searches `tickets/todos/**` for a surviving copy of the ticket and reports it as `todos_source_path`. The alternative (carry the first Scope's value across the resume) needs new durable state or a caller-passed argument; the filesystem already holds the fact, so no new state. An epic-tier move deleted the todos original, so nothing is found and `""` stays correct. Reporting never mutates anything. No JS change was needed: `implement-ticket.js` already passes the Scope result's `todos_source_path` to the Verify prompt ("expected todos duplicate" note, ~L1693) and the Finalize cleanup (`rm`, ~L1761); the defect was the tool returning `""`.

## Test Summary
`tests/tools/test_scope_orphan_fix.py`: 3 new tests (resumed run reports the surviving todos copy and does not mutate; a copy in a todos subfolder is found; a resumed epic-tier run, whose original was moved, reports `""`); the existing `test_already_in_inprogress_is_not_touched` (inprogress only, returns `""`) passes unchanged. 10 pass.

## Files Changed
- `tools/agent-monitoring/scope_ticket_relocate.py`, `tests/tools/test_scope_orphan_fix.py`; this ticket

## Completion Summary
Done. AC1: a resumed run with a surviving todos copy now reaches Verify and Finalize with the correct path (the value comes from the tool, which both prompts already consume). AC2: the regression tests pass and the existing `scope_ticket_relocate` tests pass unchanged.
