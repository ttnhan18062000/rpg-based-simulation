---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E11A-HERO-AUTHORING
phase: open
date: 2026-06-19
tags: [entity-differentiation, hero-entities, world-authoring, class-system, phase-1]
---

# TCK-20260619-E11A-HERO-AUTHORING

## Title
E11-A · Author HERO entities in sandbox_world and urban_political worlds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No HERO role entities exist in any world file. The differentiation epic requires 2–3 HERO entities per world with distinct archetype classes (WARRIOR, MAGE, ROGUE). The WorldCompiler and class assignment system are ready (TCK-20260619-P0-ENTITY-INIT).

## Scope
- Add 2–3 HERO population entries to `data/worlds/sandbox_world/` (or equivalent world spec)
- Add 2–3 HERO population entries to `data/worlds/urban_political/`
- Each entry must specify `role: hero` so the WorldCompiler assigns class_id from the default_class_table (WARRIOR/MAGE/ROGUE distribution)
- Verify that after compilation, the world contains at least one entity with each of: WARRIOR, MAGE, ROGUE class_id (across 6 HERO entities total)
- Extend `data/content/spawn_tables.yaml` default_class_table: add CITIZEN→[WORKER, MERCHANT] and MONSTER→[BEAST, UNDEAD] entries if CLASS_REGISTRY supports them; otherwise add only what's in CLASS_REGISTRY

## Out of Scope
- Implementing WORKER, MERCHANT, BEAST, UNDEAD classes in CLASS_REGISTRY (check first; if not present, only add what exists)
- Personality seeding (already done by TCK-20260619-P0-ENTITY-INIT)

## Acceptance Criteria
- Each world file has ≥2 population entries with `role: hero`
- Post-compilation entity roster includes entities with class_id in {WARRIOR, MAGE, ROGUE}
- `tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue` passes

## Related Tickets
- TCK-20260619-E11-ENTITY-IDENTITY (parent epic)
- TCK-20260619-P0-ENTITY-INIT (prerequisite — done)

## Related Docs
- `docs/core/attributes_and_classes.md`
- `docs/mechanics/01_entity_anatomy.md` § Class Registry
- `src/core/classes.py` (CLASS_REGISTRY — check which IDs are valid before authoring)

## Related Code Areas
- `data/worlds/sandbox_world/`
- `data/worlds/urban_political/`
- `data/content/spawn_tables.yaml`
- `src/worldbuilding/compiler.py`
- `tests/unit/entity/test_entity_archetypes.py` (NEW)

## Assumptions / Open Questions
- What world spec format do sandbox_world and urban_political use? Read world YAML before authoring.
- Does CLASS_REGISTRY contain WORKER, MERCHANT, BEAST, UNDEAD? Check `src/core/classes.py` first.

## Implementation Notes
Read existing world files first. Add HERO population entries following the existing pattern. Run `python3 -c "from src.worldbuilding.compiler import WorldCompiler; ..."` to verify compilation succeeds.

## Test Summary
New `tests/unit/entity/test_entity_archetypes.py`:
- `test_hero_archetypes_cover_combat_mage_rogue()` — compile sandbox_world; assert ≥1 entity with WARRIOR, ≥1 with MAGE, ≥1 with ROGUE across all HERO-role entities

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
