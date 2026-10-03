---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP

New file: `tests/unit/observability/test_event_extractor_identity.py`

1. `test_recipe_learned_fires_through_real_kernel_tick_once` — real, non-mocked
   `Kernel.tick_once()` loop (blacksmith visit is unconditional); assert `recipe_learned` fires
   for at least one entity/recipe if the world naturally produces a visit within budget. If not
   reachable within budget, document and fall back to hand-built state for this event too
   (decided during Implement, not assumed here).
2. `test_entity_role_changed_fires_on_real_delta` — hand-built `IdentityComponent.role` delta.
3. `test_entity_faction_changed_fires_on_real_delta` — hand-built `IdentityComponent.faction`
   delta.
4. `test_recipe_learned_fires_on_new_entry` — hand-built `known_recipes` set gains an entry.
5. `test_recipe_learned_does_not_fire_on_removal_or_no_change` — set unchanged, and (separately)
   an entry removed; assert no event either way (recipes are never un-learned in the real
   mechanic, but the diff logic itself must not misfire on a shrink).
6. `test_skill_cooldown_started_fires_on_new_or_changed_entry` — hand-built `cooldowns` dict gains
   an entry / an existing entry's `tick_ready` changes.
7. `test_no_event_on_zero_delta` — identical `IdentityComponent` (role/faction/recipes/cooldowns
   subset) before/after; assert no events.
8. `test_identity_events_suppressed_in_light_and_long_run_modes` — same suppression pattern as
   sibling tickets.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real role/faction reassignment trigger | Done — zero exist |
| A clear verdict on TaskUpdate | Done — deliberately not worth an event, documented |
| New event(s) wired and confirmed via a real Kernel.tick_once() loop (where reachable) | Test 1 for `recipe_learned`; hand-built pattern for the other 3 (no live trigger of any kind) |
| event_type_coverage.md and entity.yaml updated | Document-Update phase |
| Scoped pytest passes | Tests 1-8 |
