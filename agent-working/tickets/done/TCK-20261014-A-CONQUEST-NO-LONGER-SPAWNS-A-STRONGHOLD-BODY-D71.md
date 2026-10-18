---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71

## Title
A conquest no longer spawns a stronghold body from nothing. The region still changes hands at -50 influence, and is freed when its influence recovers (owner ruling D71, 2026-10-14).

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`FactionInfluenceService.process_conquest_lifecycle` (src/world/influence.py, from lifecycle.py:~299) is ON. When a region is conquered by MONSTER_HORDE, it spawns a stronghold entity with MONSTER role and hp 10000 x (1 + 0.5 x maturity), with no parent and no cost. It is removed on liberation. D71 rules: no body; keep the ownership flip.

## Scope
- Remove spawn_stronghold from the conquest lifecycle. The ownership flip at -50 is unchanged.
- Liberation:
  - If an influence-recovery path already exists, use the existing -50 line.
  - If none does, add the minimum one: the region goes back to unowned once influence climbs above that same line.
  - Report any flapping to the designer, and invent no new number.
- BEFORE building, report whether any region in the baseline arms was liberated by stronghold kills (frontier_living_world and urban_political, seeds 42-46, 5000 ticks). That changes how the step is read.
- Measure alone with the paired protocol:
  - deaths and alive per kind;
  - region ownership over time;
  - tax into the MONSTER_HORDE treasury (2.108 knock-on);
  - sales and hiring in towns inside held regions (the faction check on sale and shift).
- Disclose as interim: the influence-from-deaths trigger and MONSTER_HORDE as a taker are label-driven. They are re-anchored with caused war and peace (§12.4, not before M3).
- Docs: a divergence, a parity entry, a Bible 05 note.
- Tests:
  - a conquest adds no entity;
  - ownership flips at -50 and recovers;
  - determinism.

## Out of Scope
- The id-0 generator bug (its own ticket, first).
- Caused war and peace.

## Acceptance Criteria
- No stronghold body is created.
- Ownership and liberation work by influence.
- The knock-ons are measured and disclosed.

## Related Tickets
TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1; TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70; TCK-20261014-REGIONS-STOP-TOPPING-UP-MONSTERS-TO-A-DENSITY-TARGET-D67-D70.

## Related Docs
designer memo row 71; ECOL-03; docs/mechanics/05_world_evolution.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/world/influence.py; src/systems/lifecycle_systems/lifecycle.py; src/systems/world_systems/generator.py (spawn_stronghold).

## Assumptions / Open Questions
None.

## Implementation Notes
- Removed `FactionInfluenceService.process_conquest_lifecycle` and `EntityGenerator.spawn_stronghold`, and the lifecycle call site that merged their adds and removals. `process_influence_shift` is untouched, so conquest at -50 and liberation at +50 are as before; no number is added.
- The designer's "-50" assumed no recovery path existed. The code already has one at +50 (`LIBERATION_THRESHOLD`, an invader-owned region), and rpg-planner ruled to keep it. Influence moves only on deaths, so recovery needs invader deaths in the region.
- Pre-build probe (rpg-planner asked whether any baseline region is ever liberated, and by what): in 10 baseline runs (frontier_living_world and urban_political, seeds 42-46, 5000 ticks) there was no conquest, no liberation and no stronghold. Lowest influence anywhere was -15; owned regions stayed at +80 to +130. The step is dormant in the baseline, so there is no paired difference to measure (planner ruling: the 0-event evidence is the measurement, proved by tests that force it).
- Disclosed: the influence-from-deaths trigger and MONSTER_HORDE as a taker are label-driven, re-anchored with caused war and peace (not before M3). A second ownership writer in `engine/world_dynamics.py` flips on the same lines and is untouched. The Aura of Despair read still looks for stronghold-kind entities.
- Docs: divergence 2.123, parity PROG-136, Bible 05 Section 3 note.

## Test Summary
New `tests/unit/world/test_conquest_adds_no_entity.py` (6 tests: flip at -50 adds no entity; liberation at +50; round trip; entry points gone; tax in a conquered town goes to the horde treasury; determinism). `test_stronghold.py` is removed with the behaviour; the id-fix test now uses a monster spawn as its add. Pre-existing failures: `tests/arena/test_arena_regional_control.py` (2) fail the same on main.

## Files Changed
src/world/influence.py; src/systems/lifecycle_systems/lifecycle.py; src/systems/world_systems/generator.py; tests/unit/world/test_conquest_adds_no_entity.py; tests/unit/world/test_stronghold.py (removed); tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py; docs/mechanics/05_world_evolution.md; docs/guidelines/intentional_divergences.md; docs/parity_ledger/progression.yaml.

## Completion Summary
A monster conquest flips ownership and adds no body. Liberation at +50 is kept. Dormant in the baseline; behaviour proved by forced-conquest tests.
