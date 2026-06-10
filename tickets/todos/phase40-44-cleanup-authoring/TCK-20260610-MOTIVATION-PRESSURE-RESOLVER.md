# TCK-20260610-MOTIVATION-PRESSURE-RESOLVER

## Title
Add MotivationPressureResolver consuming need_profile and drive_profile from catalog

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 42.1. Entity archetypes already carry `need_profile_id` and `drive_profile_id` in `identity.properties` (set by `worldassembly/archetype_factory.py`). Currently no behavior consumer reads these IDs. This ticket adds `MotivationPressureResolver.resolve_pressures(entity, context) -> MotivationPressureSet` that converts need/drive profiles into normalised pressure values (hunger, safety, territory, duty, wealth, curiosity, aggression). Pressures are inputs to goal/target scoring — they do not directly force actions.

## Scope
- Add `src/world/motivation/pressure_resolver.py` with `MotivationPressureResolver` class
- Add `MotivationPressureSet(BaseModel)` with fields for each pressure type (normalized 0.0–1.0)
- Resolve `need_profile` and `drive_profile` from `CatalogRepository` using IDs from `entity.identity.properties`
- Include `context` inputs: region context (hunger, safety signals), relationship context
- Explicit fallback when profile missing: `MotivationPressureSet.empty()` with `source="no_profile"` (not silent failure)
- Do not import or depend on cognitive subsystem (`MotivationBiasService`, `DoctrineResolver`) — this is a data-consumer layer
- Tests: territorial predator → territory/hunger pressure; cautious commoner → safety/duty; merchant → wealth/trade; undead purpose-bound → purpose pressure

## Out of Scope
- Connecting pressures to decision points (that is TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS)
- Emotional simulation or complex AI subsystem
- Race-specific scripts inside resolver

## Acceptance Criteria
- [ ] `MotivationPressureResolver.resolve_pressures()` exists and returns `MotivationPressureSet`
- [ ] Need profiles are consumed from catalog
- [ ] Drive profiles are consumed from catalog
- [ ] Outputs are normalized (0.0–1.0) and deterministic
- [ ] Missing profile returns `MotivationPressureSet.empty()` with `source="no_profile"` — not exception
- [ ] Pressures do not directly force actions (read-only computation)
- [ ] No race-specific scripts inside resolver
- [ ] 4 archetype test cases pass

## Related Tickets
- TCK-20260610-SENSE-PERCEPTION-GATE (companion — perception gating)
- TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS (downstream — connects to decisions)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md`

## Related Code Areas
- `src/world/motivation/pressure_resolver.py` — new
- `src/content/repository.py` — catalog source for profiles
- `worldassembly/archetype_factory.py` — where IDs are set on entity

## Assumptions / Open Questions
- Do `need_profile` and `drive_profile` YAML files exist in `data/content/`? If not, minimal fixture files are needed.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
