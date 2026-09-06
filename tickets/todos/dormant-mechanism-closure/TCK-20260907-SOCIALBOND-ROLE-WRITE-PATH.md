---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH
phase: open
date: 2026-09-07
tags: [social, architecture]
---

# TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH

## Title
Wire a real writer for SocialBond.role, or confirm and remove it as dead scaffolding

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 2 of 6.
`RelationshipRole` (`src/core/models/social.py:7`, real enum, `SocialBond.role` defaults to
`NEUTRAL`) has a real read/merge path (`src/systems/social_systems/relationships.py:61`:
`role=b_upd.role_set if b_upd.role_set is not None else bond.role`), confirmed 2026-09-07, but zero
real (non-test) construction anywhere in `src/` of a bond-update object with `role_set` set to
anything — every `SocialBond.role` in the live system is permanently `NEUTRAL`. This is a
foundational relationship field, not a narrow content gap — potentially every relationship in the
game is affected.

## Scope
- Determine the real, live-precedented trigger for setting `role_set`. The nemesis-promotion pattern
  (`grudge_history >= 3.0` → `nemesis_ids`, `src/systems/social_systems/memory.py`) is the most
  obvious real precedent already proven live — check whether `RelationshipRole` should mirror that
  same threshold-driven promotion pattern for its own values (confirm the real enum values first, not
  assumed here).
- If a real trigger is designed and wired: add it through the authoritative apply-path only
  (`role_set` on the typed bond-update object, following `bond.role`'s existing read/merge
  convention).
- If, after investigation, no real gameplay consumer would ever read `SocialBond.role` meaningfully
  (confirm this by checking all real read sites of `.role`, not just the merge logic): remove the
  field and its dead read/merge path instead of leaving it as silent scaffolding. This is a real
  decision this ticket must make explicitly, not defer further.

## Out of Scope
- Any other item from the Dormant Mechanism Closure epic's scope.
- Building a generic relationship-classification framework beyond what `RelationshipRole`'s existing
  enum already defines.

## Acceptance Criteria
- [ ] Either: (a) a real, tested trigger sets `SocialBond.role` through the authoritative apply-path
      for at least one real enum value, confirmed via a test showing a bond transition; or (b) the
      field is confirmed dead and removed, with the removal itself tested (no regression).
- [ ] Whichever disposition is chosen, it's recorded with a real, evidenced reason — not a coin flip.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/simulation/social_systems_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/models/social.py`
- `src/systems/social_systems/{relationships,memory}.py`

## Assumptions / Open Questions
- Whether wiring a real trigger or removing the field is the right call is not decided here — real
  investigation work for this ticket's own Investigate/Plan phases.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
