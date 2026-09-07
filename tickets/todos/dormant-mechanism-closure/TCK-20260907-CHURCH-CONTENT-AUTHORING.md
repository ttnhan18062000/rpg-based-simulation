---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260907-CHURCH-CONTENT-AUTHORING
phase: open
date: 2026-09-07
tags: [content, world]
---

# TCK-20260907-CHURCH-CONTENT-AUTHORING

## Title
Place the CHURCH building's Blessing/Resurrection services into at least one real world module

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 6 of 6,
lowest priority. `CHURCH`'s Blessing/Resurrection services (`src/town/buildings.py:15,23`) are fully
coded and real, but placed in zero of the 20 world modules and 21 compiled worlds — confirmed by
direct grep during the 2026-09-02 hardening pass, not re-verified stale since. This is a pure
content-authoring gap, not a code bug.

## Scope
- Confirm the finding is still accurate during Investigate (re-grep the 20 world modules for
  `CHURCH`/`Church` building placements).
- Add `CHURCH` to at least one real world module's building composition (a low-risk, additive content
  change — no schema or code change expected).
- Confirm the building's Blessing/Resurrection services function correctly once placed, via a real
  test or calibration run.

## Out of Scope
- Building any new CHURCH mechanic — the services already exist and are correct; this ticket only
  places the building where it can actually be used.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] `CHURCH` is placed in at least one real world module.
- [ ] Blessing/Resurrection services confirmed functional in that world via a real test or run.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (Hardening backlog item 5)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/town/buildings.py`
- `data/content/world_modules/`

## Assumptions / Open Questions
- Which world module is the best fit for CHURCH content is not decided here — real content-design
  work for this ticket's own Investigate/Plan phases.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
