---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION
phase: open
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

## Title
Unify status_frozen/stunned and interaction_kind into a typed StatusEffectState

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This was misclassified in the epic as small 'orphan wiring' work under Design Idea 4, but investigation found it is real architecture work: status_frozen/status_stunned and interaction_kind are stored in untyped identity.properties/property_updates dicts and read by a wider blast radius than the atlas's own count (5 real consumers for status flags, 7 for interaction_kind). The fix is a new typed StatusEffectState record following the already-proven WoundState/ScarState precedent.

## Scope
- Add a new typed StatusEffectState frozen dataclass (source, magnitude, expires_tick) to src/core/state.py, following the WoundState/ScarState precedent (already proven to generalize per TCK-20260824-TACTICAL-WOUND-SCAR-WIRING).
- Migrate status_frozen and status_stunned off identity.properties.get() in all 5 real consumer files (src/engine/combat.py, src/engine/legality.py, src/engine/pipeline_phases/actor_validity.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/work_queue.py), with behavior provably unchanged for entities with no active status.
- Migrate interaction_kind off property_updates in all 7 real consumer files (src/actions/harvest.py, src/actions/loot.py, src/systems/world_systems/harvesting.py, src/systems/economy_systems/chests.py, src/systems/economy_systems/town_service.py, src/systems/economy_systems/loot.py, src/systems/social_systems/guilds.py).
- Explicitly decide whether closing the docs/architecture/cognition_domain_ownership.md EmotionalModel ownership-row gap is in scope for this ticket.

## Out of Scope
- Re-wiring EmotionUpdateService.update_on_event() for event_kinds beyond 'near_death' — already wired for that kind by TCK-20260824-WIRE-ORPHANED-MECHANISMS; do not duplicate work that's already done.
- PerceptionModel, EmotionalModel, and TemporalModel fields in cognition.py that are genuinely written by real pipeline phases — not part of this migration.

## Acceptance Criteria
- [ ] A new StatusEffectState typed record exists following the WoundState/ScarState precedent.
- [ ] status_frozen (and status_stunned, same call sites) migrated off identity.properties.get() in all 5 real consumer files with behavior provably unchanged for entities with no active status.
- [ ] interaction_kind migrated off property_updates in all 7 real consumer files.
- [ ] docs/architecture/cognition_domain_ownership.md gains an EmotionalModel row ONLY IF this ticket's scope touches EmotionUpdateService migration (optional, state explicitly).

## Related Tickets
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
- TCK-20260824-WIRE-ORPHANED-MECHANISMS
- TCK-20260429-E3-MISSING-LOGIC

## Related Docs
- docs/architecture/cognition_domain_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/engine/combat.py
- src/engine/legality.py
- src/engine/pipeline_phases/actor_validity.py
- src/systems/strategic_systems/intelligence.py
- src/systems/strategic_systems/work_queue.py
- src/actions/harvest.py
- src/actions/loot.py
- src/systems/world_systems/harvesting.py
- src/systems/economy_systems/chests.py
- src/systems/economy_systems/town_service.py
- src/systems/social_systems/guilds.py
- src/systems/economy_systems/loot.py

## Assumptions / Open Questions
- Blast radius is wider than the atlas's own '6 more' count — 5 consumer files for status flags plus 7 for interaction_kind.
- The atlas's 'EmotionUpdateService never called from production' finding is now partially stale — it is already wired for one event_kind ('near_death'); do not re-wire what's already wired.
- The cognition_domain_ownership.md EmotionalModel ownership-row gap remains real and unaddressed — this ticket must decide whether closing it is in scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
