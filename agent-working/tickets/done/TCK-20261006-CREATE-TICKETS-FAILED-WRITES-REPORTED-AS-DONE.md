---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-CREATE-TICKETS-FAILED-WRITES-REPORTED-AS-DONE
phase: done
date: 2026-10-06
tags: [ai, process-improvement]
---

# TCK-20261006-CREATE-TICKETS-FAILED-WRITES-REPORTED-AS-DONE

## Title
create-tickets returns DONE when write agents fail, without naming which tickets were not written

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
This is the second silent-filter shape in `.claude/workflows/create-tickets.js`. The agent-working-implementer
found it while fixing TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED. Line numbers below
are from branch `agent-working-hand-closure-epic` @ `e62a98049`.

At the write phase, `const succeeded = written.filter(Boolean)` (:886) drops every write agent that returned null.
The run logs a WARNING and pushes one aggregate `failed` event, with the count only (:893–896). It then still
returns `status: 'DONE'` (:1031). The return value lists only the successful `ticket_ids`, so the tickets that
were planned but not written appear nowhere.

When zero tickets are written, the status is still `DONE`, with the message "No tickets written — check
comprehend, investigate, and structure output". A caller reading `status` treats a total write failure as
success, which is the same trust failure the investigation-phase hotfix fixed.

## Scope
1. Carry the planned task's identity through the write pipeline: the concern id, or the planned ticket id or
   title. Then a null result can be named.
2. The return value lists `failed_writes` (identities), and the monitoring `failed` event names them.
3. Status:
   - if zero tickets were written and at least one was planned, return a distinct failure status, e.g.
     `WRITE_FAILED`, with monitoring `final_status` to match;
   - if some writes failed, keep `DONE` and populate `failed_writes`. The message states "N of M written; failed:
     …".
4. SEQUENCE.md and epic linking must not reference a failed write. Line :903's comment says this already holds;
   verify it with a test.
5. Update `.claude/skills/create-tickets/SKILL.md` for the new status and field.

## Out of Scope
- Implement-ticket and implement-epic workflows (record any same-shape finding only).
- The pre-flight agentType check (the runtime has no cheap lookup; see the investigation-phase hotfix).

## Acceptance Criteria
1. All writes return null → status `WRITE_FAILED` (not `DONE`), `failed_writes` lists every planned ticket, and
   monitoring `final_status` matches.
2. Partial failure → `DONE`, `failed_writes` names exactly the failed ones, and none of them appears in
   `ticket_ids`, SEQUENCE.md or the epic link.
3. Tested the same way as the investigation-phase hotfix (its harness or stub pattern).

## Related Tickets
- TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED (same class, same file)

## Related Docs
- `.claude/skills/create-tickets/SKILL.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `.claude/workflows/create-tickets.js` (write phase, return block)

## Assumptions / Open Questions
- Depends on the investigation-phase hotfix's changes to the same file, so build it on top of
  `agent-working-hand-closure-epic`.

## Implementation Notes
Re-verified on e62a98049: the filter was at :886, the DONE return at :1031 (now shifted by this change). The draft's claim that :903's comment already keeps failed writes out of SEQUENCE.md was wrong: `batchIdSet` and the dependency map were built from `tasksReadyToWrite` (all planned tasks), so a failed write would have appeared in SEQUENCE.md. They now use `tasksWritten` (tasks whose agent returned); the epic link already used the written ids only.
Failed writes are named by the deterministic planned id (`TCK-<date>-<short_scope>`), the monitoring `failed` event lists them, `WRITE_FAILED` (with matching final_status) is returned before SEQUENCE.md and epic linking when nothing was written, and a partial failure stays `DONE` with `failed_writes` and an "N of M ... Failed to write" message.
Finding only: implement-ticket/implement-epic not examined.

## Test Summary
4 new static tests in `tests/tools/test_create_tickets_failed_investigations.py` (named failures, WRITE_FAILED ordering before SEQUENCE/epic link, partial failure and SEQUENCE/epic exclusion, docs); workflow and create-tickets tests: 162 passed. No JS runner exists, so the runtime path has the manual reproduction of the investigation-phase hotfix.

## Files Changed
`.claude/workflows/create-tickets.js`, `.claude/skills/create-tickets/SKILL.md`, `docs/agent-monitoring/schema.md`, `tests/tools/test_create_tickets_failed_investigations.py`.

## Completion Summary
create-tickets no longer returns DONE for a run that wrote nothing: it returns WRITE_FAILED, names failed writes in `failed_writes`, and keeps them out of SEQUENCE.md and the epic link.
