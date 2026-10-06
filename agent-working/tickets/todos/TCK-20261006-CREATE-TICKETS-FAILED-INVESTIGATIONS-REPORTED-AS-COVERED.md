---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED
phase: open
date: 2026-10-06
tags: [ai, process-improvement]
---

# TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED

## Title
create-tickets reports NOTHING_TO_CREATE ("all concerns are already covered") when every investigator agent failed

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
On 2026-10-06, Workflow run `wf_4a572e02-40e` (`/create-tickets` on
`TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST`, from `7570beb90`) returned
`{"status":"NOTHING_TO_CREATE","duplicates_skipped":[],"message":"All concerns are already covered by existing tickets."}`.
All 4 `concern-investigator` agents had failed with "agent type 'concern-investigator' not found". The session
was launched from the repo's parent directory, so the project agents in `.claude/agents/` were not loaded.

In `.claude/workflows/create-tickets.js`, failed investigations are filtered out at :468. A `failed` event is
pushed at :474-475, but `activeInvestigations` (:483) is then empty, and the run exits at :486 with
`NOTHING_TO_CREATE` and the "already covered" message. A run in which nothing was investigated reports the
same status as a run that found only duplicates. A reader trusts that status and files nothing.

## Scope
1. When any investigation fails, the run must not report `NOTHING_TO_CREATE`. If all of them fail, return a
   distinct failure status, e.g. `INVESTIGATION_FAILED`, carrying the count and the first error. If some fail,
   continue with the survivors and list the failed concerns in the return value. Never report a failed concern
   as covered.
2. Check before the Investigate phase: if a required `agentType` (`concern-investigator`, `ticket-scoper`) cannot
   be resolved, stop at once with a message that names the likely cause, a session launched outside the repo
   root. The check is optional if the runtime offers no cheap way to perform it; say so if it is skipped.
3. Update the skill text (`.claude/skills/create-tickets/SKILL.md`) for the new status.

## Out of Scope
- Other workflows. If `implement-ticket.js`/`implement-epic.js` have the same shape, note it here as a finding;
  do not fix it in this ticket.

## Acceptance Criteria
1. If every investigator returns null, the run returns a non-`NOTHING_TO_CREATE` failure status and the
   monitoring `final_status` matches. Tested with a stubbed agent or the workflow's test harness, if one exists.
   Otherwise document a manual reproduction: launch from the parent directory.
2. With partial failure, the return value lists the failed concerns, and none of them appears as a duplicate.
3. The "already covered" message appears only when every concern was investigated and judged a duplicate.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (where it was found)
- `TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT` (made the native Workflow path primary)

## Related Docs
- `.claude/skills/create-tickets/SKILL.md`

## Related Stored Artifacts
None.

## Related Code Areas
`.claude/workflows/create-tickets.js` (:337-339, :463-486)

## Assumptions / Open Questions
- Route check: `.claude/**` routes to agent-working per the rpg domain's `routes`, so this is agent-working's.

## Implementation Notes
Filed by agent-working-design (interim planner), 2026-10-06, from the run's own task notification.

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
