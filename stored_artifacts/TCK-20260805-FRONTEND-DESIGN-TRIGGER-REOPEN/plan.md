---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN
artifact_type: plan
tags: [skills, workflows]
---

# Plan — TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN

## Decision: no code change
Per investigation.md, all 4 real tickets confirmed maintenance-shaped, not matching
`frontend-design`'s actual "build a new distinctive interface" trigger. The exclusion stands as
correctly decided by `TCK-20260704-SKILL-TRIGGER-COVERAGE`. No CLAUDE.md row is added — adding one
now would create a false-positive trigger (auto-invoking a design-direction skill for routine
bugfix/maintenance tickets), which would be actively counterproductive, not neutral.

## No coordination conflict with `SKILL-GATE-CONVERSION-DECISION`
That ticket (already DONE) never touched CLAUDE.md's Proactive Tool Use table at all — confirmed
by reading its own Files Changed section. No conflict exists to coordinate.

## Tests
None applicable — this ticket concludes with a documented decision and no code/doc change, matching
this repo's own precedent for decision tickets whose outcome is "confirm existing state," not
"implement something." The decision itself, with full reasoning, is the deliverable — recorded in
investigation.md.

## Parity
No `src/` files touched. No files touched at all. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (explicit decision with reasoning) → investigation.md's Decision section.
- AC2 (if reopened, coordinate) → N/A, not reopened.
