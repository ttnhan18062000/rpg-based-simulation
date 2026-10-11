---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD
phase: open
date: 2026-10-11
tags: [ai, process-improvement, governance]
---

# TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD

## Title
Lead protocol: `status-request` / `status-report` message classes, the cross-domain board skeleton, and lead ownership of `agent-working/lead/**` (Epic E, part E4b)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child of Epic E (`TCK-20261009-EPIC-SESSION-LEAD-PLANNER`), part E4. The lead-planner seat exists (#476), but the
protocol it works by is not written down: no message class lets it ask a seat for status, and there is no durable
board. Epic E's acceptance criterion 5 asks for both, plus the plan §9.0 table update. E1 deferred
`agent-working/lead/**` from the lead's `owns` until its first file is on main; this ticket creates that file.

## Scope
- **Message classes.** Add `status-request` (lead -> any role; information only, no obligation to act) and
  `status-report` (any role -> lead) to `docs/guides/cross_session_messages.md` `## Classes` and to the §9.0 table in
  `docs/plans/agent_infrastructure/session_layer_working_process.md`. Neither is a work assignment: a status-request
  never authorizes work, and a peer message still never approves anything.
- **Board skeleton.** Create `agent-working/lead/board.md` with frontmatter and the agreed columns only: epic or
  batch, owner role, state, depends-on, blocked-by, lead's recommended next step, owner decision needed (y/n).
  One header row plus a short note that the board is advice and the owner sets planner queues. No rows: the lead
  fills them.
- **Ownership.** Add `agent-working/lead/**` to the lead domain's `owns` in `registries/session_roles.yaml`.
  Regenerate the cards; every card stays within the 400-token budget, which is not raised.
- **Plan amendment.** §9.0 adds the lead as an information hub; §12.3 records the owner decisions of 2026-10-09
  and 2026-10-10 (issues as cross-host handoffs). Leave §12.5 to E3 (cross-host status).

## Out of Scope
- The SessionStart issue list (sibling `TCK-20261011-SESSION-START-FOR-ROLE-ISSUES`).
- `fleet.py` (E2), the heartbeat (E3), measurement (E5), the tech-stack registry (E6).
- Any dispatch or queue authority for the lead (owner decision 2026-10-09).
- Filling the board.

## Acceptance Criteria
1. `docs/guides/cross_session_messages.md` and plan §9.0 list `status-request` and `status-report` with sender,
   receiver and obligation, consistent with each other.
2. `agent-working/lead/board.md` exists with the seven columns and valid frontmatter.
3. `route.py agent-working/lead/board.md` names the lead domain; `python3 -m tools.sessions.validate` reports
   0 findings; the generator check shows no drift.
4. The owner confirms the literal `registries/session_roles.yaml` diff (governing file).
5. `pytest tests/tools/test_session_*.py tests/docs` passes.

## Related Tickets
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER (parent, E4)
- TCK-20261011-SESSION-START-FOR-ROLE-ISSUES (sibling, E4a)
- TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION (prior art)
- TCK-20261009-REGISTER-OTHER-HOST-SEATS (#476, E1)

## Related Docs
- docs/guides/cross_session_messages.md
- docs/plans/agent_infrastructure/session_layer_working_process.md (§9.0, §12.3)
- docs/guidelines/session_roles/domains/lead.md

## Related Stored Artifacts
None.

## Related Code Areas
- registries/session_roles.yaml
- .claude/agents/session-lead-planner.md

## Assumptions / Open Questions
- lead-planner (on host ubuntu) may comment on the batch PR about the column set; it does not approve it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
