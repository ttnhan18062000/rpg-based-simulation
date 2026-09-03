---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: investigation
tags: [content]
---

# Investigation — TCK-20260902-PLACE-SCHEMA-MIGRATION

Re-verified directly against current code on pickup (2026-09-03):

- Confirmed `PlaceState`/`PlaceKind` don't already exist anywhere in `src/`.
- `RegionState` lives in `src/core/state.py`; `RegionSpec` (content-authoring, Pydantic) lives separately
  in `src/worldbuilding/schema.py` — `RegionSpec.tags` already exists and is what the plan doc's "tags
  extends" note refers to, not a new `RegionState` field.
- `BuildingState` had zero prior region/place containment field — no `region_id` precedent to mirror for
  buildings, unlike entities (`NavigationComponent.region_id`).
- `AuthoritativeState.town_entity_ids: set[int]` is the real precedent for `PlaceState.entity_ids`/
  `building_ids` typing (`Set[int]`, not `List[str]` as originally drafted in this ticket's Scope text).
- `boss_region_id` (precedent cited for `occupant_entity_id`) is currently stored in
  `identity.properties["boss_region_id"]` (`src/world/boss.py`) — a loose properties-dict field, itself a
  Durable State Rule violation this ticket does not fix, but `PlaceState.occupant_entity_id` is
  implemented as a proper first-class typed field from the start.
- All top-level world-object state classes (`RegionState`, `BuildingState`, `CampState`, `GroupRecord`)
  live directly in `src/core/state.py` — `PlaceState`/`PlaceKind` follow the same placement, added
  directly after `RegionState`.

Two findings surfaced during implementation, not anticipated at scoping time:
1. A real bug: `ApplyPath._fast_replace_navigation` (`src/engine/apply.py`) is a hand-rolled fast
   constructor with a hardcoded field list, missing the new `place_id` field — caused a runtime
   `AttributeError` under the real tick-apply pipeline until fixed.
2. A separate, pre-existing canonical-hash gap in `NavigationComponent` itself (10 of 13 fields
   uncovered) — out of scope here, filed as `TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP`.
