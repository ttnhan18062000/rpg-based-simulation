---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMPSTATE-PLACE-BRIDGE
phase: open
date: 2026-09-04
tags: [content, architecture]
---

# TCK-20260904-CAMPSTATE-PLACE-BRIDGE

## Title
Reconcile CampState and PlaceState(kind=CAMP/NEST) for world-gen bridging

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Corrects a stale framing in the M4 epic doc ("new WorldModuleSpec field plus new WorldCompiler step") — idea 66's Place hierarchy already lets `WorldCompiler.compile()` construct `kind=CAMP`/`kind=NEST` `PlaceState` instances generically (both Direct and Composition paths), and `PlaceState.maturity`'s own docstring says "reused from CampState.maturity." The real remaining gap is that `CampState`'s fields (`kind: str` creature-flavor string, faction, active, last_raid_tick) do not losslessly map onto `PlaceState`'s fields (`kind: PlaceKind` enum, owner_faction_id, occupant_entity_id). This ticket makes and implements an explicit architecture decision to close that gap.

## Scope
- In `plan.md`, make and document an explicit architecture decision between: (a) construct a companion `CampState` alongside each `PlaceState(kind=CAMP/NEST)` instance at compile time, keeping `CampService` operating on `CampState` as today, or (b) migrate `CampService` to operate on `PlaceState` directly (owner_faction_id/occupant_entity_id/maturity), retiring the separate `AuthoritativeState.camps` dict — note (b) has a larger blast radius, touching raid/spawn logic and all existing camp tests.
- Implement the chosen option: wire `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) to recognize Camp/Nest-shaped content and construct the corresponding `PlaceState` (and, if option (a), companion `CampState`), for both the Direct and Composition content paths, mirroring `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`'s precedent for CITY-kind Places.
- Add a regression test proving non-Camp-shaped content (e.g. a City/Ruin/Dungeon-only world module) compiles unchanged after this change.
- If option (a) is chosen, define and test the `CampState`<->`PlaceState` linkage (e.g. via `place_id`, matching `RegionState.places`' dual-sided membership pattern from the schema migration ticket).

## Out of Scope
- The City/Camp/Nest race classification decision itself — that is `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s scope; this ticket consumes that decision's output (which races/content are Camp vs Nest) but does not make the classification call itself.
- Any change to the Nest spread-outcome mechanism or new typed Camp/Nest feature fields (totem/stockpile/palisade) — those are `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s scope.
- `CreatureTerritoryService` changes.

## Acceptance Criteria
- `plan.md` states and justifies the chosen architecture (companion CampState vs CampService-on-PlaceState migration) before implementation begins.
- `WorldCompiler.compile()` constructs `PlaceState(kind=CAMP)` and `PlaceState(kind=NEST)` instances from content, for both the Direct and Composition paths, mirroring the CITY-kind precedent in `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`.
- A new test proves non-Camp-shaped world content compiles unchanged (regression) after this change — mirrors `tests/unit/worldbuilding/test_place_wiring.py` and `tests/unit/worldassembly/test_resolver.py`'s existing structure.
- If option (a): `CampState` instances constructed alongside their `PlaceState` counterpart round-trip correctly and existing `CampService` tests (`test_camp_lifecycle.py`) continue to pass unmodified in their assertions about `CampService` behavior.
- If option (b): all existing `CampService`/`CampState` call sites (`src/world/camp.py`, `src/world/creature_territory.py`, `src/engine/apply.py`, `src/engine/apply_plan.py`) are updated consistently and their existing test suites pass.

## Related Tickets
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING
- TCK-20260902-PLACE-SCHEMA-MIGRATION
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md
- docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md (stale WorldModuleSpec/WorldCompiler framing to correct)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/core/state.py (PlaceState, PlaceKind, CampState, AuthoritativeState.camps/.places)
- src/world/camp.py
- src/world/creature_territory.py
- src/engine/apply.py
- src/engine/apply_plan.py
- tests/unit/worldbuilding/test_place_wiring.py
- tests/unit/worldassembly/test_resolver.py

## Assumptions / Open Questions
- Recommended sequencing: this ticket needs C1's classification rule (which races/content are Camp vs Nest) to exist before compiling real content, though the bridging mechanism itself is separately implementable — recommend implementing TCK-20260904-CAMP-NEST-CLASSIFICATION first.
- docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md's "CampState is never constructed anywhere, needs new WorldModuleSpec field + WorldCompiler step" framing is now stale given idea 66's landed Place hierarchy — this ticket's plan.md should note the correction rather than re-implementing the stale plan.
- Option (a) vs (b) is a real, consequential architecture decision with different blast radii; the Plan phase should not silently default to the smaller option without stating the tradeoff.
- No production code currently constructs `CampState()` at all (confirmed via grep) — `state.camps` is populated only in tests today; this ticket is the first to give it a real construction path.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
