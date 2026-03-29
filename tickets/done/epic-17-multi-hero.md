# Epic 17 Phase 1: Multi-Hero & Permanent Death

## Title
Implement Multiple Heroes, Name Generation, and Escalating Death Penalties

## Description
The simulation previously hardcoded the existence of a single Hero entity. This epic transitions the world into a multi-hero simulation where 3-5 heroes spawn simultaneously, operate independently, build familiar bonds, and face permanent death if they exhaust 4 death strikes. When a hero falls permanently, a generic Generation tracker is bumped, and a completely fresh recruit replaces them.

## Scope
- Modify `EngineManager._build()` and configuration loaders to spawn `N` heroes based on `config.hero_count`.
- Add `display_name`, `death_count`, `generation`, and `hero_familiarity` dynamically to `models.Entity`.
- Create a `HeroLifecycleSystem` inserted strictly at the end of `WorldLoop` to independently handle:
  - Naming heroes on birth (`FirstName the Title`).
  - Checking `EntityRole.HERO` instances who died, scaling their drop penalties depending on `death_count`.
  - Managing the permadeath threshold (4 deaths) and firing a replacement event.
  - Parsing the spatial index to detect adjacent heroes and incrementing their familiarity score (+0.002) or dropping it (-0.0005).

## Acceptance Criteria
- Starting the simulation with `config.hero_count = 4` spawns exactly 4 independent heroes with different names and starting classes.
- A hero dying 3 times drops items. The 4th time, they are permanently removed from the `entities` dictionary and a new Class/Name hero spawns.
- `HeroLifecycleSystem` is strictly segregated from `action_system.py` and `progression_system.py`.

## Related Tickets
Subsumes features from `epic-04` (Multi-Hero) and partially addresses `epic-18` tracking concepts.
