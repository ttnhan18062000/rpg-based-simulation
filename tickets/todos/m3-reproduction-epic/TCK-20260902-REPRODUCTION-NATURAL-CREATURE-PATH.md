---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
phase: open
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH

## Title
Natural-creature reproduction path — reuse Camp maturity/spawn pattern for parentless offspring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 2 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering the natural-creature branch of idea 32 (Reproduction). Natural creatures (non-sapient wildlife) reproduce without a tracked parent pair — the design reuses `CampService.process_camps()`'s existing maturity-accrual/spawn/raid-trigger pattern (`src/world/camp.py`) rather than inventing a new mechanism. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first (needs the birth-record fields to exist, even though this path leaves parent_a/parent_b as None).

## Scope
- A camp/territory at or above its existing maturity threshold produces a new same-kind entity with a short CHILD→ADULT maturation clock, following `CampService`'s existing maturity/spawn constants (`MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD`-style thresholds in `src/world/camp.py`).
- The new entity has no tracked parent pair — `parent_a_entity_id`/`parent_b_entity_id` from the birth-record schema (TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are left None for this path.
- The spawn is committed via a typed `EntityUpdate`/`StateUpdate` through the authoritative apply path, reusing `CampService`'s existing mutation pattern.
- Eligibility is gated by the population-pressure signal: suppress spawn when `compute_regional_scarcity()` (`src/domains/demographics/cohort.py`) for the camp's region exceeds the region's cohort `migration_threshold` (0.7 default) — reuse this existing computation, do not add a new one.

## Out of Scope
- The magical/demonic and human/humanoid reproduction paths (separate child tickets).
- Genetics inheritance — natural creatures do not use `GeneticsSystem`/`GeneticProfile` per this ticket's scope (genetics wiring is scoped to the human/humanoid path only in TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE; confirm this boundary at Plan time rather than assuming).
- The population-pressure feedback-loop closure itself (nudging `population_cohorts` on a successful birth) — that is TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, a separate later child ticket.

## Acceptance Criteria
- [ ] A camp/territory at or above its maturity threshold produces a new same-kind entity with a short CHILD→ADULT maturation clock, verifiable against `CampService`'s existing maturity/spawn constants.
- [ ] The new entity's birth-record fields (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are populated with `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, and correct `birth_city_id`/region.
- [ ] Spawn eligibility is suppressed when `compute_regional_scarcity()` exceeds the region's `migration_threshold` for the camp's region — a test proves both the allowed and suppressed cases.
- [ ] The spawn is committed through the authoritative apply path (`EntityUpdate`/`StateUpdate`), not a direct mutation.
- [ ] New unit test(s) added following the pattern of `tests/unit/world/test_camp_lifecycle.py::test_camp_maturity_and_spawn` / `::test_camp_raid_trigger`.
- [ ] `docs/mechanics/05_world_evolution.md` documents this reproduction path; a `docs/parity_ledger/world_dynamics.yaml` entry cites it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260831-CREATURE-TERRITORY-LIFECYCLE (sibling precedent — reused CampService's trauma-multiplier maturity shape for a different settlement-population tier)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/camp.py
- src/domains/demographics/cohort.py
- src/core/updates.py

## Assumptions / Open Questions
- Whether this path needs any genetics involvement at all is an open boundary question for Plan — flagged as likely "no" (natural creatures don't inherit the human/humanoid GeneticProfile system) but not yet confirmed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
