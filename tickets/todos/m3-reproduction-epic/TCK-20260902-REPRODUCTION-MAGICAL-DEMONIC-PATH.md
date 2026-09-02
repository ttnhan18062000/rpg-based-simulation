---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH
phase: open
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH

## Title
Magical/demonic-being reproduction path — reuse Calamity substrate, full-adult spawn (no childhood)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 3 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering the magical/demonic branch of idea 32 (Reproduction). Magical/demonic beings spawn off the existing `CalamityService`/`CalamityPressurePropagator` substrate (`src/world/calamity.py`) rather than a parent-pair mechanism, and per the design's own resolved decision, spawn at full adult capability with no childhood/maturation clock — this is settled, not an open question. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first.

## Scope
- A calamity/pressure event at or above its existing trigger threshold produces a new magical/demonic entity via `CalamityService`, following its existing intensity/trigger pattern (`src/world/calamity.py`).
- The new entity spawns directly as an ADULT life stage with no CHILD→ADULT maturation clock (explicit resolved design decision — magical beings do not have a childhood).
- No tracked parent pair — `parent_a_entity_id`/`parent_b_entity_id` (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are left None for this path, same as the natural-creature path.
- The spawn is committed via a typed `EntityUpdate`/`StateUpdate` through the authoritative apply path, reusing `CalamityService`'s existing mutation pattern.

## Out of Scope
- The natural-creature and human/humanoid reproduction paths (separate child tickets).
- Genetics inheritance — magical/demonic beings do not use `GeneticsSystem`/`GeneticProfile`; confirm this boundary at Plan time.
- The population-pressure feedback-loop closure — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, a separate later child ticket. Note: whether magical/demonic spawns even participate in the population-pressure gate at all (vs. being purely calamity-intensity-driven) is an open question for Plan — the atlas's population-pressure gate language is written primarily with natural/human reproduction in mind.

## Acceptance Criteria
- [ ] A calamity/pressure event at or above its trigger threshold produces a new magical/demonic entity, verifiable against `CalamityService`'s existing intensity/trigger constants.
- [ ] The new entity is spawned directly at ADULT life stage — no CHILD→ADULT transition or maturation clock is applied to this path.
- [ ] The new entity's birth-record fields are populated with `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, and correct `birth_city_id`/region (or the calamity's origin location if no city applies).
- [ ] The spawn is committed through the authoritative apply path, not a direct mutation.
- [ ] New unit test(s) added following the pattern of `tests/unit/world/test_calamity_raid.py::test_calamity_raid_maturity_advancement` / `::test_calamity_intensity_shift`.
- [ ] `docs/mechanics/05_world_evolution.md` documents this reproduction path (including the explicit "no childhood" rule); a `docs/parity_ledger/world_dynamics.yaml` entry cites it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card — cross-race pairing / magical maturation explicitly resolved by design, treat as settled)
- docs/mechanics/05_world_evolution.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/calamity.py
- src/core/updates.py

## Assumptions / Open Questions
- Whether magical/demonic spawns are gated by the same regional population-pressure signal as natural/human paths, or purely by calamity intensity, is unresolved — a Plan-phase decision, not assumed here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
