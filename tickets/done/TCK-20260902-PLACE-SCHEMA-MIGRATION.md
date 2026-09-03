---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
phase: done
date: 2026-09-02
tags: [content]
---

# TCK-20260902-PLACE-SCHEMA-MIGRATION

## Title
Add PlaceState/PlaceKind schema and RegionState.places membership

## Status
DONE

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
- [x] `PlaceState`/`PlaceKind` exist with full field set per the plan doc.
- [x] `RegionState.places` and the entity/building `place_id` back-reference both exist. (Construction
      consistency — e.g. a typed update keeping both sides in sync — is deferred to
      `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`, the first ticket that actually constructs populated
      instances; this ticket is schema-only, no mutation path exists yet to keep consistent.)
- [x] New fields are covered by `to_canonical_dict()` from the start. Confirmed via `AuthoritativeState.places`
      in `CanonicalStateHasher.to_canonical_data()` and explicit `place_id` coverage on both
      `NavigationComponent` and `BuildingState`.
- [x] Unit tests cover construction, canonical round-trip, and back-reference consistency. 9 tests in
      `tests/unit/core/test_place_state.py`.

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
- Confirmed directly: `RegionSpec.tags` (content-authoring schema, `src/worldbuilding/schema.py`)
  already exists and is where the plan doc's "tags extends to describe the territory as a whole" applies
  — that's an authoring-time field, not a `RegionState` runtime field, and out of this ticket's scope
  (no `WorldCompiler`/content changes here).
- `place_id` back-reference placement: `NavigationComponent` (entities, mirrors `region_id` exactly) and
  `BuildingState` (buildings — new, since `BuildingState` had zero prior region/place containment field
  at all, unlike entities).
- `building_ids`/`entity_ids` typed as `Set[int]`, matching `AuthoritativeState.town_entity_ids: set[int]`'s
  real precedent (not `List[str]` as originally drafted in this ticket's own Scope text).
- **Real bug found and fixed during implementation**: `ApplyPath._fast_replace_navigation`
  (`src/engine/apply.py`) is a hand-rolled, performance-optimized constructor for `NavigationComponent`
  with an explicit, hardcoded field list that predated `place_id` — adding the new field without updating
  this function caused a runtime `AttributeError` under the real tick-apply pipeline (caught by
  `tests/unit/worldbuilding/test_worldbuilding_strategy.py::test_smoke_simulation_run`). Fixed by adding
  the missing `object.__setattr__(res, "place_id", nav.place_id)` line. This confirms hot-path dataclasses
  in this codebase can have multiple hand-rolled fast-constructors that must all be updated in lockstep
  with the class definition — not caught by type checking, only by running the real integration tests.
- Found a separate, pre-existing canonical-hash gap while working in this area:
  `NavigationComponent`'s own `"navigation"` canonical sub-dict covers only 3 of 13 real fields
  (`target`, `path`, `moved_recently`) — `region_id`, `position`, and 10 others are excluded. Out of
  scope for this ticket (predates it, not introduced by it); filed as
  `TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP` for future pickup. `place_id` itself was given explicit
  coverage specifically so it would not silently inherit this same gap.
- A `FakeState` test double in `tests/certification/test_evidence_levels.py` needed a `places: dict = {}`
  attribute added, since `CanonicalStateHasher.to_canonical_data()` now reads `state.places`
  unconditionally.

## Test Summary
- 9 new tests in `tests/unit/core/test_place_state.py`: minimal construction, all-7-kind construction,
  transformation trail (`prior_kind`/`transformed_tick`), `RegionState.places` membership list,
  `place_id` back-reference on `NavigationComponent`/`BuildingState`, `PlaceState`/`RegionState.places`/
  `NavigationComponent.place_id` canonical-hash participation (including a per-field divergence loop
  covering all 12 `PlaceState` fields).
- Full scoped run: `pytest tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/
  tests/unit/worldbuilding/ -m "not slow"` → 699 passed, 2 skipped (pre-existing, unrelated), 0 failed.
- Also ran `tests/certification/test_recorder_refactor.py`, `tests/unit/worldbuilding/test_world_compiler.py`,
  `tests/arena/` → 76 passed.
- One test (`tests/integration/world/test_long_run_stability.py`) hit a sandbox resource-time-limit
  timeout on a mis-scoped run — it's marked `@pytest.mark.extra_slow` and explicitly `skipif(CI==true,
  reason="wall-clock-dependent")`; not a real regression, just excluded from the real scoped command
  above.

## Files Changed
- `src/core/state.py` — `PlaceKind`, `PlaceState`, `RegionState.places` (+ canonical dict entry),
  `NavigationComponent.place_id` (+ explicit canonical dict entry), `BuildingState.place_id` (+ canonical
  dict entry), `AuthoritativeState.places`.
- `src/engine/checkpoint.py` — `CanonicalStateHasher.to_canonical_data()`: added `"places"` key.
- `src/engine/apply.py` — `ApplyPath._fast_replace_navigation`: added the missing `place_id` copy (real
  bug fix, not just a new-field addition).
- `tests/unit/core/test_place_state.py` — new file, 9 tests.
- `tests/certification/test_evidence_levels.py` — `FakeState` test double: added `places: dict = {}`.
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-389`, written via `tools/parity_ledger_writer.py`.
- `tickets/todos/TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP.md` — new follow-up ticket (not implemented).
- `tickets/inprogress/TCK-20260902-PLACE-SCHEMA-MIGRATION.md` → moved to `tickets/done/`.

## Completion Summary
Landed idea 66's first child ticket: `PlaceState`/`PlaceKind` schema, `RegionState.places` membership,
and the resolved dual-sided `place_id` back-reference on `NavigationComponent`/`BuildingState`, all with
full canonical-hash coverage from day one. Found and fixed a real bug along the way (a hand-rolled
fast-constructor with a stale hardcoded field list) and surfaced a separate pre-existing canonical-hash
gap in `NavigationComponent` itself, filed as a follow-up rather than scope-creeping into fixing it here.
Schema only — no `WorldCompiler` wiring or content migration; `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`
is next in the epic's child-ticket sequence.
