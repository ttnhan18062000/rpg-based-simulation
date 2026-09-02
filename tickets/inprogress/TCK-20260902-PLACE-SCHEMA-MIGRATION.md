---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
phase: open
date: 2026-09-02
tags: [content]
---

# TCK-20260902-PLACE-SCHEMA-MIGRATION

## Title
Add PlaceState/PlaceKind schema and RegionState.places membership

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 1/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`. Adds the `PlaceState`/`PlaceKind` schema
and `RegionState.places: List[str]` membership per the epic's plan doc Target Shape section, using the
now-resolved dual-sided membership decision (`RegionState.places` list + cached `place_id` back-reference
on the owning entity/building, paralleling `GroupRecord.member_ids`/`IdentityComponent.group_id` and
`NavigationComponent.region_id`). No content migration or `WorldCompiler` wiring yet — schema only, so
downstream tickets have a stable target to build against.

## Scope
- Add `PlaceState` dataclass and `PlaceKind` enum (`CITY | CAMP | NEST | LAIR | RUIN | DUNGEON |
  LANDMARK`) per the plan doc's Target Shape (`place_id`, `region_id`, `kind`, `position`, `footprint`,
  `owner_faction_id`, `scale`, `maturity`, `occupant_entity_id`, `hazard_level`, `building_ids`,
  `entity_ids`, `prior_kind`, `transformed_tick`).
- Extend `RegionState` with `places: List[str]`.
- Add the cached `place_id: Optional[str]` back-reference field on the entity/building component(s) that
  need fast Place lookup (mirror `NavigationComponent.region_id`'s placement/rationale).
- Add `to_canonical_dict()`/`from_canonical_dict()` coverage for all new fields from day one — do not
  repeat the Social/Knowledge canonical-hash gap pattern found elsewhere this session.

## Out of Scope
- `WorldCompiler` wiring, content migration, pilot compilation (separate child tickets).
- Implementing ideas 35/45/46/47/48/61 themselves.

## Acceptance Criteria
- [ ] `PlaceState`/`PlaceKind` exist with full field set per the plan doc.
- [ ] `RegionState.places` and the entity/building `place_id` back-reference both exist and stay
      consistent under construction/mutation (a typed update, not ad-hoc dual writes).
- [ ] New fields are covered by `to_canonical_dict()` from the start.
- [ ] Unit tests cover construction, canonical round-trip, and back-reference consistency.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING (depends on this)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (Target Shape, Membership-index
  decision)
- `docs/brainstorm/rpg_expected_schemas.html#schema-66`
- `docs/simulation/domains/party_contract.md` §1 (precedent for the back-reference pattern)

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-SCHEMA-MIGRATION/`)

## Related Code Areas
- `src/worldbuilding/schema.py`
- `src/core/state.py`

## Assumptions / Open Questions
- Exact component placement for the `place_id` back-reference (which component gets it — likely
  alongside `NavigationComponent.region_id` for entities; buildings may need their own equivalent field)
  is an implementation-time decision, not pre-resolved here.
- Coordinate with the concurrent M3 implementation session before editing `src/core/state.py`.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
