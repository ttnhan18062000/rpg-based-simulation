---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
phase: open
date: 2026-09-02
tags: [lifecycle]
---

# TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE

## Title
Wire orphaned GeneticsSystem/GeneticProfile into human/humanoid reproduction's inheritance step

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 4 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION). `GeneticsSystem`/`GeneticProfile` (`src/systems/lifecycle_systems/genetics.py`) already exists and is written, but is confirmed to have zero real callers anywhere in `src/` or `tests/` — it is only referenced via a re-export shim at `src/systems/genetics.py`. This ticket wires it up for the first time, as the inheritance step for human/humanoid reproduction: a produced entity's `GeneticProfile` is sampled/combined from both parents' profiles. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first (needs `parent_a_entity_id`/`parent_b_entity_id` to be resolvable to real parent entities to read their profiles from).

## Scope
- Wire `GeneticsSystem`/`GeneticProfile` (`src/systems/lifecycle_systems/genetics.py`) into a real call path for the first time, invoked whenever a human/humanoid birth (from TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE) needs to construct the new entity's genetic profile.
- The produced entity's `GeneticProfile` is sampled/combined from both parents' profiles using the existing 0.8–1.3 per-attribute multiplier range already defined in `genetics.py`.
- The combination's bias direction is determined by parent occupation/role: a combat-relevant lean when both parents are Adventurer-occupation, a flatter/neutral spread when both parents hold civilian occupations (exact weighting formula is a Plan-phase decision — this is new, unprecedented territory with no existing numeric analog to copy).
- The resulting `GeneticProfile` is attached to the new entity via a typed `EntityUpdate`, through the authoritative apply path.

## Out of Scope
- The human/humanoid reproduction trigger/cadence logic itself (cooldown checks, entity pairing) — that is TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE, which calls into this ticket's inheritance step.
- Genetics for the natural-creature or magical/demonic paths — out of scope per those tickets' own boundary notes; confirm at Plan time this ticket is human/humanoid-only.

## Acceptance Criteria
- [ ] `GeneticsSystem`/`GeneticProfile` has a real, live caller for the first time — verifiable via a grep showing a non-test, non-shim call site.
- [ ] A new entity produced by human/humanoid reproduction has a `GeneticProfile` sampled/combined from both parents' profiles using the existing 0.8–1.3 per-attribute multiplier range.
- [ ] The combination's bias direction is measurably different for two-Adventurer-parent vs two-civilian-parent cases (a test asserts the distributional difference, not just that a value exists).
- [ ] The resulting profile is written via a typed `EntityUpdate` through the authoritative apply path.
- [ ] New unit tests added for the inheritance/combination function, following existing `tests/unit/` conventions for `src/systems/lifecycle_systems/`.
- [ ] `docs/mechanics/01_entity_anatomy.md` documents the inheritance mechanism; a `docs/parity_ledger/` entry cites it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE (sibling — the trigger path that will call into this inheritance step; lands after this ticket per the epic's build order)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/genetics.py
- src/systems/genetics.py (re-export shim)
- src/core/updates.py

## Assumptions / Open Questions
- The exact occupation-bias weighting formula has no existing numeric precedent anywhere in the codebase and must be designed fresh at Plan time — do not assume a specific formula here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
