---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMP-NEST-CLASSIFICATION
phase: open
date: 2026-09-04
tags: [content, feature-flags]
---

# TCK-20260904-CAMP-NEST-CLASSIFICATION

## Title
Camp/Nest race classification rule and flag-gated Nest branch on CampService

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Consolidates M4 design ideas 44+45+46. Establishes a documented, race-data-verified City/Camp/Nest classification rule keyed off `natural_traits` in `data/content/living/races.yaml`, explicitly resolving the goblin `social_humanoid` contradiction and the 5 currently-unclassified races (wolf, undead, troll, dragonkin, spirit). Adds a flag-gated Nest branch to `CampService` (`src/world/camp.py`) that reuses `RAID_MATURITY_THRESHOLD`/`MATURITY_PER_TICK` timing but substitutes a spread outcome for the raid outcome, plus new typed Camp/Nest feature fields (totem, stockpile, palisade) on `CampState`/`CampUpdate`.

## Scope
- Document the City/Camp/Nest classification rule against real `natural_traits` data for all 13 races in `data/content/living/races.yaml` (human, wolf, goblin, spider, orc, elf, dwarf, undead, troll, lizardfolk, dragonkin, slime, spirit); the decision must be recorded in `plan.md`/`investigation.md`, not deferred.
- Explicitly resolve the goblin contradiction: goblin carries `social_humanoid` (shared with City-eligible human/elf/dwarf) alongside `opportunistic`/`small_body`, which is the trait set idea 44's card claims justifies Camp classification — state which trait(s) decide Camp-over-City for goblin specifically.
- Give an explicit disposition (Camp, Nest, or neither/out-of-scope-for-now) for each of: wolf (`quadruped, pack_hunter, territorial, carnivore`), undead (`undead` only), troll (`large_body, regenerating`), dragonkin (`flying, large_body, fire_aligned, magic_sensitive` — note dragonkin's trait profile is the closest match to idea 47's Lair concept, not Camp/Nest; state whether dragonkin is excluded from Camp/Nest classification entirely for that reason), spirit (`spiritual, magic_sensitive`).
- Add a new feature flag (registered in `src/domains/optimization/feature_flags.py`'s flag map, default OFF, following the `ENABLE_CREATURE_TERRITORY_LIFECYCLE`/`ENABLE_REPRODUCTION_*` naming and default-OFF precedent) gating a new Nest branch in `CampService`.
- Nest branch reuses `CampService.MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD` for timing but at threshold triggers a spread/population-growth outcome instead of the existing raid-spawn outcome in `CampService.process` (`src/world/camp.py`).
- Add typed fields for Camp/Nest features — totem, stockpile, palisade — to `CampState` (`src/core/state.py`) and `CampUpdate` (`src/core/updates.py`), not free-form dict/metadata storage; magnitudes may be provisional but must be explicitly documented as such.
- Extend `tests/unit/world/test_camp_lifecycle.py` and `tests/unit/world/test_natural_creature_reproduction.py` to cover the Nest branch (flag ON and flag OFF/no-op) and the new typed fields.

## Out of Scope
- CampState world-generation/WorldCompiler wiring, `WorldModuleSpec` changes, or seeding a live Camp/Nest at world-compile time — no AC in this ticket may assume a live seeded Camp exists at compile time; that is `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`.
- Any change to `src/world/creature_territory.py`'s `CreatureTerritoryService` — it is an intentionally separate, parallel per-entity territory mechanism per its own docstring; do not merge or extend it as part of Nest work.
- Dissolution/transformation of Camp/Nest content on any trigger — that mechanism family belongs to idea 48 (place-type transitions), which has no ticket yet.

## Acceptance Criteria
- `plan.md`/`investigation.md` records an explicit classification decision for all 13 races in `races.yaml`, with the goblin `social_humanoid` contradiction named and resolved, and all 5 previously-unclassified races (wolf, undead, troll, dragonkin, spirit) given an explicit disposition (not left ambiguous or silently deferred).
- A new flag (default OFF) gates a Nest branch in `CampService`; with the flag OFF, existing raid-branch behavior and all current tests in `test_camp_lifecycle.py` pass unchanged (regression).
- With the flag ON, a Camp instance flagged as Nest-kind reaches `RAID_MATURITY_THRESHOLD` and produces a spread outcome (documented, tested) instead of a raid outcome, using the same `MATURITY_PER_TICK` accrual.
- `CampState`/`CampUpdate` carry new typed fields for totem, stockpile, and palisade (not dict/metadata storage), each round-tripping through `to_canonical_dict()`/merge correctly and covered by a serialization test.
- No `WorldModuleSpec`, `WorldCompiler`, or world-generation code is touched by this ticket.

## Related Tickets
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-109's camp_constructed divergence_note)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/world/camp.py
- src/core/state.py (CampState)
- src/core/updates.py (CampUpdate)
- data/content/living/races.yaml
- src/world/creature_territory.py (related-but-explicitly-separate, do not merge)
- src/domains/optimization/feature_flags.py
- tests/unit/world/test_camp_lifecycle.py
- tests/unit/world/test_natural_creature_reproduction.py

## Assumptions / Open Questions
- The classification decision (goblin resolution + 5-race dispositions) is a genuine judgment call this ticket must make explicitly, not defer — flagged directly by the epic doc's own Content note.
- Feature-flag name is not yet chosen; must be registered following existing naming/default-OFF conventions.
- Totem/stockpile/palisade magnitudes have no existing anchor in the codebase and must be documented as provisional/flagged, per the epic doc's Content & Balance Requirements note.
- docs/parity_ledger/world_dynamics.yaml's WORLD-109 divergence_note ("camp_constructed has no viable engine path... camps are pre-placed at world generation") pre-dates this work and should be revisited only if this ticket changes that fact — it currently does not, since CampState construction remains out of scope here.
- dragonkin's trait profile overlaps more with idea 47's Lair concept than Camp/Nest — this ticket must state explicitly whether dragonkin is excluded from Camp/Nest classification for that reason, to avoid conflicting with TCK-20260904-LAIR-ENTITY-ANCHOR.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
