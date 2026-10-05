---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS
phase: done
date: 2026-10-05
tags: []
---

# TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS

## Title
Closing a ticket filed directly into `todos/` leaves a stale copy there, and only a PR-time corpus test catches it

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Routed by `rpg-feature-planning` (2026-10-05). PR #347's `Tools · f–z` job failed on
`tests.tools.test_validate_frontmatter.TestClosedTicketResurrectionCorpus::test_real_tickets_tree_has_no_closed_ticket_resurrected_into_active_dirs`
("1 ticket basename(s) resurrected"): `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK.md`
existed in both `agent-working/tickets/done/` and `agent-working/tickets/todos/`. It was fixed by hand (`git rm` of the
`todos/` copy plus a registry regenerate).

Three things line up badly (verified against `origin/main`):

1. CLAUDE.md "After Work" deletes the source copy only when the ticket came from a `todos/{folder}/` subfolder. A ticket
   filed directly into `todos/` (the normal planner hand-off) has no delete instruction, so following the documented flow
   exactly produces the inconsistency.
2. `tools/gate_checks/done_checker_static.py` validates the ticket being closed. It has no check that a same-basename copy
   does not survive in an active directory (no `todos` or resurrection logic in the file).
3. The only detector is `find_closed_ticket_resurrections` in `tools/validate_frontmatter.py`, reached through a corpus
   test at PR time, after the commits, close, monitoring records and registry regenerate are already done.

This will recur: planners file tickets directly into `todos/` for lanes to pick up, so every one is a future instance.
Related earlier guard: `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`.

## Scope
Move detection from PR time to close time, and make the omission impossible or loud. Candidate shapes, in the order the
planner recommends (the choice is the implementer's within the existing gates):

- Add a sibling-copy condition to `done_checker_static` (reuse `find_closed_ticket_resurrections`) so it fails locally at
  close, including through the hand-orchestrated CLI.
- Have `record_hand_orchestrated_closure.py` and the Finalize phase remove the `todos/` copy of the closing ticket (and
  report that it did), so the step cannot be forgotten.
- Extend the CLAUDE.md "After Work" wording to any `todos/` ticket. This is a governing-file edit and needs the owner's
  literal-diff confirmation; do not land it without that.

## Out of Scope
- Changing the corpus test itself (it stays as the backstop).
- Restructuring the `todos/` layout.

## Acceptance Criteria
- Closing a ticket whose basename also exists in `todos/` (directly or in a subfolder) fails `done_checker_static` locally
  with a message naming the stale path, or the closure tool removes it and says so.
- A test pins both the failing and the passing case.
- The CLAUDE.md wording either covers directly-filed tickets (with owner-confirmed diff) or the ticket records why the
  tooling fix makes it unnecessary.

## Related Tickets
- `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`

## Related Docs
- `CLAUDE.md` (After Work)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS/`

## Related Code Areas
- `tools/gate_checks/done_checker_static.py`
- `tools/validate_frontmatter.py` (`find_closed_ticket_resurrections`)
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tests/tools/test_validate_frontmatter.py`

## Assumptions / Open Questions
- Which of the three shapes fits the existing gates is the implementer's call; the first two need no governing-file edit.

## Implementation Notes
Shapes 1 and 2 implemented; shape 3 deliberately not (see Completion Summary). Shares a PR with `TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE`.

## Test Summary
`tests/tools/test_close_sequence_repairs.py` (stale-copy cases: 5 tests) plus `tests/tools/test_done_checker_static.py`; full `tests/tools tests/docs`: 4206 passed, 55 skipped, 2 xfailed.

## Files Changed
`tools/gate_checks/done_checker_static.py`, `tools/agent-monitoring/record_hand_orchestrated_closure.py`, `tests/tools/test_close_sequence_repairs.py`, `docs/guides/delivery_process.md`, `docs/REGISTRY.yaml` (regenerated). CLAUDE.md is unchanged.

## Completion Summary
Closing a ticket whose basename survives under `todos/` (flat or subfolder) now fails `check_ticket_finalized` naming the path, and the hand-orchestrated closure tool deletes the `todos/` and `inprogress/` copies of the ticket it closes and prints them. Decision: the CLAUDE.md "After Work" wording is not edited; the tooling makes the omission loud and automatic (no governing-file edit, so no owner diff needed). The PR-time corpus test stays as backstop.
