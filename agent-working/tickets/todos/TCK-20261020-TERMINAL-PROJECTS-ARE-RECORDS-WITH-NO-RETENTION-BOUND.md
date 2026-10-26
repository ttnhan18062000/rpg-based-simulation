---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND

## Title
COMPLETED and ABANDONED strategic projects are kept on the entity for its lifetime with no retention bound: decide their lifecycle

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
`strategic.py:336-361` keeps a terminal project as "a record" that doesn't count against `max_active_projects`, and nothing removes it. So `strategic.projects` grows by one entry per finished quest for the entity's life, along with any per-project payload. This is durable state with no defined lifecycle end, which conflicts with the Durable State Rule (typed model, stable location, defined lifecycle). It feeds the /entities payload growth (TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL), and probably state size and fingerprint cost too.
`strategic.blockers` and `strategic.contracts` also have no capacity rule. Check them the same way.

## Scope
- Decide the lifecycle with rpg-designer: keep the last N terminal projects per entity, fold older ones into typed aggregate counts, or move them to a world-level history store. Whatever is chosen must keep what any reader (memory, reputation, SimQ, quests UI) needs.
- Implement it through the authoritative apply path. Measure it as a behaviour step (it moves the hash): paired 3 × 42-46, crowded first.
- Apply the same review to blockers and contracts.

## Out of Scope
- The API projection fix (its own ticket).

## Acceptance Criteria
- Every unbounded per-entity collection has a written lifecycle and a bound, with tests.
- The paired measurement passes the stop rule, or the result goes to the owner.
- Mechanics Bible 04 and the parity ledger are updated if the knowledge or project law text changes.

## Related Tickets
- TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/core/state.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/entities_payload.md

## Related Code Areas
- src/ai strategic.py (~336-361), the project capacity trim

## Assumptions / Open Questions
- Do any readers depend on the full terminal history?

## Implementation Notes
After v1 (it moves the state hash).
- Lead's review note on #686: read_model_service_contract.md should say that the detail's live quests and blockers are only bounded because cognition caps live projects. Add that sentence when this ticket defines the lifecycle, or as a one-line doc fix sooner.

## Test Summary

## Files Changed

## Completion Summary
