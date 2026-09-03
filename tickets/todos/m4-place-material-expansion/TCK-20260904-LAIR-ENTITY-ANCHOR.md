---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-LAIR-ENTITY-ANCHOR
phase: open
date: 2026-09-04
tags: [content, determinism]
---

# TCK-20260904-LAIR-ENTITY-ANCHOR

## Title
Generalize Boss's entity-anchor idempotency pattern to Place-scoped Lair spawning

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 47 (Lair). Generalizes `BossService.check_for_boss_spawn`'s per-region entity-anchor idempotency pattern (`identity.properties["boss_region_id"]`, `src/world/boss.py`) to per-Place scoping using `PlaceState.occupant_entity_id` (kind=LAIR, already schema-frozen by idea 66 and documented as "reused from boss_region_id pattern"), since a Region can hold multiple LAIR Places where the old per-Region keying would collide.

## Scope
- Extend the `boss_region_id` idempotency pattern in `src/world/boss.py` to key off `PlaceState.occupant_entity_id` per LAIR-kind Place (`place_id`) instead of per-Region, so multiple LAIR Places within one Region each get independent, idempotent spawn tracking.
- Extend `tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` to a Place-scoped variant proving idempotency holds across multiple LAIR Places in one Region.
- Add real LAIR-kind content to at least one world corpus profile, or a synthetic fixture, since no LAIR-kind Place exists in the current 21-world corpus (Stage B rollout explicitly declined to add one).

## Out of Scope
- Lair dissolution or transformation on occupant death — idea 47's own card wants this, but the mechanism belongs to idea 48 (place-type transitions), which has no ticket yet. This ticket must not silently assume or half-build that behavior.
- Writing the first-ever dedicated boss-spawn test suite from scratch — an idempotency test already exists (`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`); this ticket extends/generalizes it to Place-scoping, it does not establish boss-spawn testing for the first time. Boss-spawn logic overall still has minimal dedicated test coverage beyond this — budget test-writing accordingly per the epic doc's depth-audit note.
- Any change to CampService/Camp-Nest classification (C1) or CampState/PlaceState bridging (C2).

## Acceptance Criteria
- Lair spawn idempotency is keyed per-Place (via `PlaceState.occupant_entity_id` / `place_id`), not per-Region, and is proven not to double-spawn when multiple LAIR Places exist in the same Region.
- `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`-style coverage is extended (not replaced) to cover the Place-scoped case.
- At least one real LAIR-kind Place exists in a chosen corpus world OR a synthetic fixture is added and clearly labeled as such, sufficient to exercise the new logic in tests.
- Dissolution/transformation on occupant death is explicitly listed in Out of Scope in the ticket, with idea 48 named as the deferred owner — not silently omitted.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 47)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/world/boss.py (check_for_boss_spawn, boss_region_id pattern)
- src/core/state.py (PlaceState.occupant_entity_id, PlaceKind.LAIR)
- tests/unit/world/test_world_dynamics.py

## Assumptions / Open Questions
- Idea 48 (place-type transitions) does not yet have a ticket — Lair dissolution-on-death depends on it and is explicitly deferred, not silently dropped.
- No real LAIR-kind Place exists in the current 21-world corpus; Stage B rollout explicitly declined to add one, so this ticket must add real content or a clearly-labeled synthetic fixture.
- Boss-spawn logic generally has minimal dedicated test coverage beyond the one idempotency test being extended — budget accordingly rather than assuming a mature test base.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
