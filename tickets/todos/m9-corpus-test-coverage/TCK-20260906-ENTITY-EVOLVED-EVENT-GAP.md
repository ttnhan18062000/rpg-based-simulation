---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP
phase: open
date: 2026-09-06
tags: [simulation-quality]
---

# TCK-20260906-ENTITY-EVOLVED-EVENT-GAP

## Title
Add a real entity_evolved observability event for the already-shipped XP-only evolution path

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 2 of 8. `docs/brainstorm/
rpg_expected_schemas.html`'s "Expected Events" section found this gap independent of any of M9's own
32 tracked ideas: no `entity_evolved` event exists today, even for the already-shipped XP-only
evolution path. Confirmed still real, 2026-09-06 — zero real code hits for `entity_evolved` anywhere
in `src/`.

## Scope
- Confirm the real XP-only evolution code path (likely in `src/domains/progression/` or
  `src/systems/lifecycle_systems/`, confirm exact location during Investigate).
- Add a real `entity_evolved` observability event, emitted on the actual evolution transition, mirroring
  the shape/conventions of this codebase's other 90 real event types in `src/observability/
  event_extractor.py`.
- Register the new event with SimQ per the standard M7-established pattern (a real signal rule, or an
  explicit written reason it's excluded) — cross-reference
  `docs/simulation_quality/event_type_coverage.md` rather than duplicating that audit.

## Out of Scope
- Building any new evolution mechanic — the XP-only path already exists and ships; this ticket only
  adds observability for it.
- Any other item from M9's scope.

## Acceptance Criteria
- [ ] A real `entity_evolved` event fires on the actual XP-only evolution transition, confirmed via a
      test.
- [ ] The event is registered with SimQ (a real signal rule, or an explicit written exclusion reason
      recorded in `event_type_coverage.md`).

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/brainstorm/rpg_expected_schemas.html` — "Expected Events" section
- `docs/simulation_quality/event_type_coverage.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/domains/progression/`

## Assumptions / Open Questions
- The exact real code location of the XP-only evolution transition is not confirmed here — real work
  for this ticket's own Investigate phase.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
