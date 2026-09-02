---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
phase: open
date: 2026-09-02
tags: [lifecycle, core]
---

# TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA

## Title
Foundational birth-record durable schema — new Lifecycle/EntityState fields and builder wiring for individual reproduction

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is child ticket 1 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering idea 32 (Reproduction) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Today idea 32 has zero real code — it is design-only in `docs/brainstorm/rpg_feature_atlas.html`. `LifecycleUpdate` (`src/core/updates.py:435-462`) has a `heir_entity_id_set` field but no fields at all for parent identity, birth tick, birth location, or per-parent reproduction cooldown — every other reproduction-path ticket in this epic (natural-creature, magical/demonic, human/humanoid, genetics) depends on this durable schema existing first, so it must land before any of them. Marriage is explicitly NOT a precondition for reproduction — the M3 build-order note (2026-08-29 plan-owner decision) decoupled Marriage (idea 33) from Reproduction (idea 32); do not gate any part of this schema or its write path on an active marriage contract.

## Scope
- Add new typed durable fields to the Lifecycle component/update (parallel to the existing `heir_entity_id`/`heir_entity_id_set` pattern in `src/core/state.py` and `src/core/updates.py:435-462`): `parent_a_entity_id`, `parent_b_entity_id` (Optional[int], None for parentless spawns e.g. natural-creature/magical paths), `birth_tick` (int), `birth_city_id` (Optional[int]), and a per-parent reproduction cooldown field (follow the `CampUpdate.last_raid_tick_set` precedent at `src/core/updates.py:861-868` for the cooldown-field shape).
- Wire these fields through the authoritative apply path (`src/engine/patches.py` / `src/engine/apply_plan.py`) so a birth event can be committed as a typed `EntityUpdate`/`StateUpdate`, never a direct state mutation.
- Extend `src/core/builder.py` (which already has a `heir_entity_id` param at lines 584, 597) with an equivalent birth-record construction path so a newly spawned entity can be built with these fields populated at creation time.
- Seed a `SocialBond` between each parent and the new child entity at high familiarity/sentiment, following the seeding precedent in `src/systems/social_systems/relationships.py:55`.
- This ticket does not implement any of the three reproduction trigger paths (natural-creature, magical/demonic, human/humanoid) — it only builds the schema and the builder-level wiring those paths will call into.

## Out of Scope
- The actual reproduction trigger/decision logic for any of the three species-branching paths (natural-creature, magical/demonic, human/humanoid) — those are separate child tickets (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH, TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH, TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE).
- Genetics inheritance (`GeneticsSystem`/`GeneticProfile` wiring) — separate child ticket TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE.
- The population-pressure feedback-loop closure (idea 38) — separate child ticket TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE.
- Any marriage-gating logic — explicitly decoupled per the 2026-08-29 build-order decision; do not add a marriage precondition anywhere in this schema.

## Acceptance Criteria
- [ ] `parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, and a per-parent reproduction-cooldown field exist as new typed fields on the Lifecycle component/update, following the existing `heir_entity_id`/`heir_entity_id_set` naming and write-path pattern.
- [ ] These fields are written only through a typed `EntityUpdate`/`StateUpdate` applied via the authoritative apply path — no direct mutation of frozen state.
- [ ] `src/core/builder.py` gains a birth-record construction path that can populate all new fields at entity creation time, alongside the existing `heir_entity_id` param.
- [ ] A `SocialBond` is seeded between each parent and the new child at high familiarity/sentiment when a birth record is constructed via the new builder path.
- [ ] New unit tests cover: field serialization/deserialization (canonical-dict round-trip, matching the pattern the POPULATION-COHORT-SEEDING ticket fixed for `PopulationCohort.to_canonical_dict()` — see `docs/parity_ledger/world_dynamics.yaml:1671-1691`), and that the builder path produces correctly-populated fields for a two-parent case and a parentless (natural-creature/magical) case.
- [ ] `docs/core/entities.md` and/or `docs/mechanics/01_entity_anatomy.md` documents the new fields; a new `docs/parity_ledger/` entry (likely `world_dynamics.yaml` or a new social_narrative.yaml entry) cites this schema.
- [ ] No marriage-contract precondition exists anywhere in the new schema or its write path.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260831-SPECIES-INTELLIGENCE-TIER (idea 14, DONE — hard dependency satisfied)
- TCK-20260831-POPULATION-COHORT-SEEDING (idea 43, DONE — hard dependency satisfied)
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (precedent for a Lifecycle-field write path)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-DEMO-005, WORLD-DEMO-006)
- CLAUDE.md (Durable State Rule, Authoritative Mutation Pipeline Contract)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/engine/patches.py
- src/engine/apply_plan.py
- src/systems/social_systems/relationships.py

## Assumptions / Open Questions
- Whether the per-parent cooldown lives on the Lifecycle component itself or a separate sidecar structure is an implementation decision for the Plan phase — `CampUpdate.last_raid_tick_set` is the closest existing precedent but is on a different component type (Camp, not entity Lifecycle).
- This ticket must land first — every other Reproduction-epic child ticket depends on it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
