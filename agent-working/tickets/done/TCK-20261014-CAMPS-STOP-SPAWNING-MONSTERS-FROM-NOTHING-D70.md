---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70

## Title
Camps stop spawning monsters from nothing (V1). They shrink as members die, until real births (M1) or recruits (later) refill them. Owner ruling D70, 2026-10-14.

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`CampService.process_camps` (src/world/camp.py, the CAMP_SPAWN_INTERVAL block) works like this: every 30 ticks, a camp with fewer than max(2, maturity/10) monsters within 10 tiles spawns one through `generator.spawn_monster`, with no parent, no cost and no food. It runs in the headless simulation and the gate. Found by Lane C while tracing the live map's unexplained entity. Owner ruling D70: this is a V1 violation, removed before v1.

## Scope
- Covers EVERY camp kind (Lane C, 2026-10-14):
  - `CampService.spawn_kind` falls back to the camp's own kind when a species declares no `camp_spawn_kind`, so a wolf nest (wolf_den_nest) spawns wolves.
  - The body is a generic `spawn_monster` monster (hp 50 x tier, faction MONSTER_HORDE), not the authored archetype.
  - It fires at tick 0 on sandbox_world, because the den holds 1 monster against a cap of 2.
  - The natural-creature offspring path is separate, and gated OFF.
- Remove the camp-based spawning block.
- The nest-spread branch (ENABLE_CAMP_NEST_SPREAD, default OFF, spawn_natural_creature_offspring) has the same no-parent shape. It stays OFF, marked to be retired when the M1 births land. Do not delete it in this ticket unless it is dead code.
- The removed count used EntityRole.MONSTER, a role label (against D46). Make sure no remaining code reads that label for camp logic, or list where it does.
- Measure alone with the paired protocol against the #536 main:
  - deaths and alive per kind;
  - camp members over time;
  - V1 and validity rows.
- Docs:
  - a divergence (Bug Fix / Intentional Gameplay Change, D70);
  - the parity entry;
  - a Bible 05 camps paragraph: camps refill only by births (M1) or recruits (later).
- Tests:
  - no camp adds an entity without a source over N ticks;
  - camps shrink as members die;
  - determinism.

- ALSO REMOVE the camp raid spawn (designer application of D70, 2026-10-14): `RaidService.spawn_raid`, called from camp.py's raid trigger, conjures 3 + maturity NEW raiders at the camp for a 20-maturity cost, with no off-map origin and no existing members. Camps don't raid until a later rule lets existing members set out together; that is the designer's to bring to the owner.
- These stay OFF and are retired with the M1 births: creature_territory (ENABLE_CREATURE_TERRITORY_LIFECYCLE), boss/lair (D14), and calamity entities (ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH). reproduction_humanoid is a tracked two-parent BIRTH, a candidate base for M1, so keep it.

- Mechanism binding: Lane C re-bound EntityGenerator to `camp` when the density top-up was removed (2.122). Re-check that binding once the camp spawn is gone.
- Known red: rpg_gate_known.yaml's V8 entry names this ticket as primary. Re-point it to the D71 ticket when this lands.

## Out of Scope
- M1 births for every living kind (D67, extended by D70 to camp kinds).
- Recruits.
- The gate's "every mid-run entity has a declared source" V1 check. That belongs to testing-planner.

## Acceptance Criteria
- Expected after removal (designer): the wolf den keeps only its alpha until M1 births. This is reported, not graded (D67/D70).
- No parentless camp spawn remains active.
- The measurement is disclosed.
- Camp shrinkage is reported, not graded.

## Related Tickets
D67 wild-births child (M1 epic); TCK-20261014-THE-LIVE-SERVER-RUNS-THE-AUTHORED-WORLD-NOT-A-DEMO-SPAWN-D69.

## Related Docs
docs/mechanics/05_world_evolution.md; designer memo row 70; ECOL-03.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70/ (plan, investigation, test_plan).

## Related Code Areas
src/world/camp.py; src/world/world_dynamics (the caller); the generator's spawn_monster.

## Assumptions / Open Questions
None.

## Implementation Notes
- `src/world/camp.py`: the CAMP_SPAWN_INTERVAL spawn block and the raid trigger are gone. The flag-gated nest-spread branch (OFF) and the natural-creature step are unchanged. No remaining camp logic reads `EntityRole.MONSTER`.
- `src/world/raid.py`: `spawn_raid` deleted; the class keeps its constants and comments for the raid that returns with caused war.
- Docs: divergence 2.125, WORLD-030/031/032 now `divergent`, Bible 05 subsection, mechanism comment on `camp` (the `EntityGenerator` binding stays: `process_camps` still calls it for the flag-OFF nest-spread offspring).
- Known red: the V8 entry is removed from `tools/test_architecture/rpg_gate_known.yaml` because V8 is green (0 violations) in all 10 camp-world gate runs (frontier_living_world and crowded_frontier, seeds 42-46, 5000 ticks).
- Measured (paired, seeds 42-46, 5000 ticks): frontier_living_world mid-run adds 50 to 0, final alive 168 to 121, deaths 151 to 148; urban_political identical (no camps). Details in divergence 2.125.

## Test Summary
- New `tests/unit/world/test_camps_spawn_nothing.py` (5 tests; 3 fail on the old code).
- Conversions of tests of the removed behaviour: `test_camp_lifecycle.py`, `test_calamity_raid.py` (spawn_raid tests replaced by a retired-spawner test), `test_global_raid_retired.py`, `tests/unit/ai/test_guild_need_scorer.py` (goblin_raider built through `spawn_monster`), `tests/integration/world/test_camp_raid_targeting.py` (now a matured camp raids nothing).
- Gate harness V8: 0 violations in 10 of 10 runs.

## Files Changed
src/world/camp.py; src/world/raid.py; the five test files above plus the new test; docs/guidelines/intentional_divergences.md; docs/parity_ledger/world_dynamics.yaml; docs/mechanics/05_world_evolution.md; registries/mechanisms.yaml; tools/test_architecture/rpg_gate_known.yaml; this ticket and its stored artifacts.

## Completion Summary
Camps add no entity and raid nothing. Measured against rpg-next 56cefc2f4: frontier mid-run adds 50 to 0; urban unchanged. V8 is green, so its known-red entry is removed. Disclosed in 2.125: camp maturity only rises, camps are empty places until M1, shrinkage is reported not graded.
