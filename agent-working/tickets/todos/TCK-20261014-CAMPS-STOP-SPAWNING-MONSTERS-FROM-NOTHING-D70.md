---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70

## Title
Camps stop spawning monsters from nothing (V1). They shrink as members die, until real births (M1) or recruits (later) refill them. Owner ruling D70, 2026-10-14.

## Status
OPEN (before M0 baseline v1, measured as its own step)

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
None.

## Related Code Areas
src/world/camp.py; src/world/world_dynamics (the caller); the generator's spawn_monster.

## Assumptions / Open Questions
None.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
