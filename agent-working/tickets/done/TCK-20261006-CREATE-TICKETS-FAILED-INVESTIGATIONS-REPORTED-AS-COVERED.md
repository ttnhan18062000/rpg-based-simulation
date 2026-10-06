---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED
phase: done
date: 2026-10-06
tags: [ai, process-improvement]
---

# TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED

## Title
create-tickets reports NOTHING_TO_CREATE ("all concerns are already covered") when every investigator agent failed

## Status
DONE

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
Verified the quoted lines against the tree (the filter at the old :468, the NOTHING_TO_CREATE exit). Failed concerns are found by id (comprehension ids minus investigated ids), not by position. New status `INVESTIGATION_FAILED` is returned, with `failed_concerns`, `failed_count`, `investigated_count`, `duplicates_skipped` and the likely cause, whenever nothing can be created and at least one concern was not investigated (all failed, or the rest were duplicates); the "already covered" message is now reachable only with no failed concern. With partial failure and tickets created, the final `DONE` return lists `failed_concerns`.
Not done, as the ticket allows: (1) "the first error": the runtime returns null for a failed agent, so no error text exists; the message names the usual cause instead. (2) Scope 2 pre-flight `agentType` check: the runtime offers no cheap lookup, so it is skipped; the failure is caught after the fact and named.
Finding (out of scope): `create-tickets.js` has a second silent-filter shape at the write phase (`written.filter(Boolean)`; "No tickets written" is the only signal). `implement-ticket.js` already has `SCOPE_AGENT_FAILED`; `implement-epic.js` was not examined.
Filed by agent-working-design (interim planner), 2026-10-06, from the run's own task notification.

## Test Summary
`tests/tools/test_create_tickets_failed_investigations.py` (6, static source-text tests like the repo's other workflow tests; no JS runner exists) plus the existing create-tickets and workflow tests (355 passed). Manual reproduction for the runtime path: run /create-tickets from the repo's parent directory; expect INVESTIGATION_FAILED.

## Files Changed
`.claude/workflows/create-tickets.js`, `.claude/skills/create-tickets/SKILL.md`, `docs/agent-monitoring/schema.md`, `tests/tools/test_create_tickets_failed_investigations.py`.

## Completion Summary
create-tickets no longer reports a never-investigated concern as covered: it returns INVESTIGATION_FAILED (monitoring final_status the same) with the failed concerns and the likely cause.
