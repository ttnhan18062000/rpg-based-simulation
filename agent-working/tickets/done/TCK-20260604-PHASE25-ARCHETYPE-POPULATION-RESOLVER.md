---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260604-PHASE25-ARCHETYPE-POPULATION-RESOLVER
phase: done
date: 2026-06-04
tags: [phase25, archetype, population, resolver]
---

# TCK-20260604-PHASE25-ARCHETYPE-POPULATION-RESOLVER

## Title
Phase 25 — Entity archetype and population resolution

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement `ResolvedEntityArchetype` (the fully-merged compile-ready archetype template) and `PopulationRecipeResolver` (which expands population recipes into world assembly contributions). This makes `entity_archetypes.yaml` and `populations.yaml` the preferred spawn authoring path.

## Scope
- Add `ResolvedEntityArchetype` to `src/content/resolver.py` — resolved from race + role + faction defaults layered with explicit archetype profiles and traits/themes.
- Add `EntityArchetypeResolver` to `src/content/resolver.py` — resolves a single `EntityArchetypeDefinition` into `ResolvedEntityArchetype`.
- Add `PopulationRecipeResolver` to `src/content/resolver.py` — expands a `PopulationRecipeDefinition` into a list of `(ResolvedEntityArchetype, count)` pairs.
- Write unit tests in `tests/unit/content/test_resolvers.py` covering archetype resolution and population expansion.
- Extend `tests/unit/worldassembly/test_assembly.py` to verify CompileContext receives archetype-driven profile data.

## Out of Scope
- Phase 26 registry adapters.
- Modifying legacy world module population_recipes (compatibility preserved).
- Adding boss/enemy logic — archetypes with strong stats represent boss-like entities.

## Acceptance Criteria
- Every catalogued archetype resolves without error.
- Race defaults affect archetype output.
- Role defaults affect archetype output.
- Faction defaults affect archetype output.
- Explicit archetype fields override defaults.
- Traits/themes merge deterministically (race natural traits + archetype traits, deduplicated in stable order).
- No archetype stores enemy/ally labels.
- Population recipe expands all archetype refs deterministically.
- Output remains compatible with `WorldSpec` via CompileContext.
- Old module population style remains supported as compatibility.
- Existing tests pass without regression.

## Related Tickets
- TCK-20260604-PHASE24-RESOLVER-LAYER

## Related Docs
- `world_phase_20_28.md` (Phase 25)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260604-PHASE24-RESOLVER-LAYER/`

## Related Code Areas
- `src/content/resolver.py`
- `tests/unit/content/test_resolvers.py`
- `tests/unit/worldassembly/test_assembly.py`

## Assumptions / Open Questions
- Trait merge: race natural_traits + archetype traits, deduplicated preserving archetype order then appending missing race traits. (Archetype traits take precedence in ordering; race natural traits added at end if not already present.)
- For the `projection` field: carry `legacy_role` and `legacy_faction` (int enum values) derived from `FactionDefinition.legacy_engine_bucket` and `RoleDefinition.legacy_engine_role`, consistent with `WorldAssemblyResolver`.
- `PopulationRecipeResolver` outputs `List[Tuple[ResolvedEntityArchetype, int]]` — one entry per `members` entry, preserving dict insertion order.

## Implementation Notes
- `ResolvedEntityArchetype` is a frozen Pydantic model carrying all 8 resolved profiles plus merged traits/themes and legacy projection strings.
- `EntityArchetypeResolver._resolve_from_definition` performs the 4-layer resolution: race defaults → role defaults → faction defaults → explicit archetype fields.
- Trait merge: archetype traits first (in declaration order), then any race natural_traits not already present. Deduplication is stable (set + list).
- `legacy_engine_role` / `legacy_engine_bucket` are pure catalog strings from `RoleDefinition.legacy_engine_role` and `FactionDefinition.legacy_engine_bucket`. No runtime enum imports in `resolver.py`.
- `EntityArchetypeResolver.resolve_all()` iterates `repo.entity_archetypes.items()` for deterministic ordering.
- `PopulationRecipeResolver.resolve()` returns `(expanded, preferred_regions)` where expansion order matches `members` dict insertion order.

## Test Summary
- 38 new tests added to `tests/unit/content/test_resolvers.py` (Phase 25 classes), total now 93.
- 5 new tests added to `tests/unit/worldassembly/test_assembly.py` (Task 25.2), total now 13.
- All 2051 unit tests pass.

## Files Changed
- [MODIFY] `src/content/resolver.py` — Added `ResolvedEntityArchetype`, `EntityArchetypeResolver`, `PopulationRecipeResolver`
- [MODIFY] `tests/unit/content/test_resolvers.py` — Added 38 Phase 25 tests
- [MODIFY] `tests/unit/worldassembly/test_assembly.py` — Added 5 Task 25.2 tests

## Completion Summary
- Phase 25 fully implemented: `EntityArchetypeResolver` resolves archetypes from race+role+faction defaults with explicit overrides; `PopulationRecipeResolver` expands population recipes into typed archetype+count pairs.
- All 9 acceptance criteria met:
  - Every catalogued archetype resolves without error.
  - Race / role / faction defaults each propagate to archetype output.
  - Explicit archetype fields override defaults.
  - Traits merge deterministically (archetype first, then race naturals, no duplicates).
  - No archetype stores enemy/ally labels (`is_boss` or `enemy_label` absent).
  - Population recipe expands all archetype refs deterministically.
  - Output remains compatible with `WorldSpec` via legacy projection strings.
  - Old module population style remains supported (unchanged).
  - 2051 unit tests pass without regression.
