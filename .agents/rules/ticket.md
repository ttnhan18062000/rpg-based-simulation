---
trigger: always_on
---

# Ticket Rule

## File Name

Use:

`TCK-YYYYMMDD-SHORT-SCOPE.md`

Example:

`TCK-20260330-CORE-STABILIZATION.md`

Rules:

- uppercase
- hyphen-separated
- short and meaningful
- stable after creation

---

## File Location

Active work:

`tickets/inprogress/{ticket_id}.md`

Completed work:

`tickets/done/{ticket_id}.md`

---

## Required Content

Use this exact section order:

# TCK-20260330-CORE-STABILIZATION

## Title

Short outcome-focused title

## Status

OPEN | INPROGRESS | BLOCKED | DONE

## Request Summary

What was requested

## Scope

- what this ticket will do

## Out of Scope

- what this ticket will not do

## Acceptance Criteria

- concrete, checkable outcomes

## Related Tickets

- related ticket IDs or None

## Related Docs

- relevant repo doc paths or None

## Related Stored Artifacts

- relevant artifact paths or None

## Related Code Areas

- expected files/modules

## Assumptions / Open Questions

- only material assumptions/questions

## Implementation Notes

- important design notes or changes during work

## Test Summary

- tests run
- tests added/updated
- known gaps if any

## Files Changed

- actual changed files

## Completion Summary

- final implementation summary
- limitations/follow-ups if any
