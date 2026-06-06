# TCK-20260530-WORLD-PHASE2

## Title

World Data Refactor Phase 2: Content Semantics Layer

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the Content Semantics Layer under `src/content_semantics`. This includes building services that interpret faction, role, and default properties from catalog definitions (without exposing raw YAML specs to runtime components), and building compatibility adapters to allow existing compiler enum mappers to fall back seamlessly onto semantic definitions.

## Scope

- Create faction semantics service (`src/content_semantics/faction.py`) mapping alignments and checking hostilities.
- Create role semantics service (`src/content_semantics/role.py`) translating families and legacy role associations.
- Create default semantics service (`src/content_semantics/defaults.py`) providing defaults for units, resources, starting gold, and regions.
- Modify existing compiler mappers (`src/worldbuilding/compiler.py`) to serve as backward-compatible adapters backed by these new services.
- Ensure all legacy simulation behavior and tests continue to work flawlessly.

## Out of Scope

- Introducing new compilation pipelines or resolving complex dynamic recipe profiles.
- Changing runtime engine ticks or modifying core state models.

## Acceptance Criteria

- [x] `src/content_semantics/` folder and modules created.
- [x] Faction semantics service (`FactionSemanticsService`) supports `is_hostile`, alignments, and bucket lookup.
- [x] Role semantics service (`RoleSemanticsService`) supports role families and default stat profile ids.
- [x] Defaults semantics service (`DefaultSemanticsService`) supplies core compiler fallbacks.
- [x] Compiler adapters wrapper in `src/worldbuilding/compiler.py` handles catalog-backed resolution without breaking old string matching.
- [x] Tests verify that mappers and semantic services execute perfectly under both mock and base catalog files.
- [x] Runtime execution remains completely unchanged.

## Related Tickets

- `TCK-20260530-WORLD-PHASE1`

## Related Docs

- `docs/architecture/world_assembly_architecture.md`
- `world_phases_0_10_updated.md`

## Related Code Areas

- `src/content_semantics/faction.py`
- `src/content_semantics/role.py`
- `src/content_semantics/defaults.py`
- `src/worldbuilding/compiler.py`

## Assumptions / Open Questions

- We will import and reference the `CatalogRepository` inside our semantic layer safely.

## Test Summary

- We will write modular, focused unit tests under `tests/unit/content_semantics/`.

## Files Changed

- `src/content_semantics/faction.py` (NEW)
- `src/content_semantics/role.py` (NEW)
- `src/content_semantics/defaults.py` (NEW)
- `src/worldbuilding/compiler.py` (MODIFY)
