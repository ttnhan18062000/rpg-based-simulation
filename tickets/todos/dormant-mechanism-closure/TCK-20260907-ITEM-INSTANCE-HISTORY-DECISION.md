---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION
phase: open
date: 2026-09-07
tags: [content, architecture]
---

# TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION

## Title
Idea 30 (Possessions With Personal History) — activate ENABLE_ITEM_INSTANCE_HISTORY or confirm deliberate deferral

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 4 of 6.
`ENABLE_ITEM_INSTANCE_HISTORY` defaults `OFF` (`src/domains/optimization/feature_flags.py:134`);
`ItemInstanceService.maybe_create_instance()` (`src/core/inventory.py:221`) is real, confirmed
2026-09-07, but has zero real (non-test, non-definition) call sites anywhere in `src/` — the flag has
never been exercised in a live run. Unlike the other tickets in this epic, this is a real product
decision (activate and verify, or leave deliberately dormant), not a wiring bug to fix.

## Scope
- Confirm the real current state of `ItemInstanceService`'s implementation (is it feature-complete
  behind the flag, or a partial scaffold?) during Investigate.
- Present the roadmap owner (the user, via `AskUserQuestion` or equivalent) with a real decision:
  activate the flag and verify the mechanism works end-to-end in at least one real corpus run, or
  record an explicit, evidenced reason to leave it dormant for now.
- If activated: confirm no regression in existing item/inventory tests, and add real test coverage
  proving ownership-history actually accumulates across a real gameplay sequence (LOOT→CRAFTED→
  GIFT→INHERITED, matching M9's own idea-30 corpus-test spec from `CORPUS-TEST-ZERO-NEW-WORLD-
  ASSERTIONS`, if that ticket's own idea-30 work didn't already cover this).
- If deferred: record the reason clearly in this ticket and in the plan doc, not silently left open.

## Out of Scope
- Building any new item-history mechanic beyond what `ItemInstanceService` already implements.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real decision (activate or defer) is made and recorded with an evidenced reason.
- [ ] If activated: real test coverage confirms the mechanism works end-to-end with no regression.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS` (M9's own idea-30 corpus-test work, check for
  overlap during Investigate)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/inventory.py`
- `src/domains/optimization/feature_flags.py`

## Assumptions / Open Questions
- Whether to activate or defer is a real product decision, not resolved here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
