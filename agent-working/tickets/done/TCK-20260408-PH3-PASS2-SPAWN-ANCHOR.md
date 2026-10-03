---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260408-PH3-PASS2-SPAWN-ANCHOR
phase: done
date: 2026-04-08
tags: [ph3, pass2, spawn, anchor]
---

# Ticket: TCK-20260408-PH3-PASS2-SPAWN-ANCHOR
# Title: Phase 3 Pass 2: Spawn-time Anchoring

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the logic to anchor entities in the world through routines, roles, and place attachments at spawn time.

## Scope
- [ ] Create `src/systems/social/lived_structure_service.py`.
- [ ] Update `EntityBuilder` to seed routines and attachments.
- [ ] Update `EntityGenerator` to assign `LifeRole`, `clique_id`, and `household_id`.
- [ ] Add unit tests for seeding logic.

## Out of Scope
- AI behavioral integration (Pass 3).
- UI/Schema updates for inspection (Pass 4).

## Acceptance Criteria
- Entities spawned via `EntityGenerator` have appropriate `world_role`.
- `MindAspect.routine_profiles` is populated based on role.
- `MindAspect.place_attachments` includes at least one anchor (HOME or WORKPLACE).
- `IdentityAspect` has valid social identifiers (`clique_id`, `household_id`).
- All new tests pass.

## Related Tickets
- Follows `TCK-20260408-PH3-PASS1-LIVED-MODELS`.

## Status
DONE
