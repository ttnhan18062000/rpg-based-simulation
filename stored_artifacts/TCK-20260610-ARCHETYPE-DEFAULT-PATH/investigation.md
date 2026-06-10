# Investigation — TCK-20260610-ARCHETYPE-DEFAULT-PATH

## Current Behavior

World assembly produces a `WorldBundle` with `world_spec` (WorldSpec) and `compile_context` (CompileContext).
`CompileContext.entities` is a `Dict[str, ResolvedEntityProfile]` — entity templates with archetype metadata.

`ResolvedEntityProfile` already carries `archetype_id`, `role_id`, `faction_id`, `race_id`, traits, themes, and
all profile IDs (Phase 25 work). The `ProfileResolver.resolve()` in `resolver.py:896-960` already resolves the
archetype via `EntityArchetypeResolver` and populates this data.

However, there is **no `WorldEntitySpawner` or equivalent** — no component converts
`ResolvedEntityProfile` → `EntityState` via `ArchetypeEntityFactory`. The downstream path for
entity instantiation (`perf/scenarios.py`, `certification/scenarios.py`) goes directly to `V2EntityBuilder`
without routing through `ArchetypeEntityFactory`.

## Documented Construction Paths (from contract_builder.py)

1. **archetype-native** [preferred]: catalog → resolved archetype → contract → EntityState
2. **worldspec role/faction/count**: existing world assembly population expansion (ProfileResolver)
3. **legacy builder**: V2EntityBuilder for arena/test/migration use cases

Path 2 populates `CompileContext` with archetype data but doesn't create `EntityState`.
Path 1 exists as an isolated bridge (`ArchetypeEntityFactory` tested in `test_archetype_entity_factory.py`)
but is not wired into world assembly output.

## Gap

No `WorldEntitySpawner` (or equivalent) converts `CompileContext.entities → Dict[int, EntityState]`
using `ArchetypeEntityFactory` as the primary path.

## Fix Design

Create `src/worldassembly/entity_spawner.py` with `WorldEntitySpawner`:
- `spawn_from_context(ctx: CompileContext, catalog_repo: CatalogRepository) -> Dict[int, EntityState]`
- For each entity profile with `archetype_id`:
  `EntityArchetypeResolver → resolved_archetype_to_contract → ArchetypeEntityFactory.build_entity()`
- For profiles without `archetype_id`: explicit `V2EntityBuilder` legacy guard path
- Entity IDs assigned sequentially (1-based) from profile keys

## V2EntityBuilder Locations (scope)

`V2EntityBuilder` is used in:
- `src/perf/scenarios.py` — perf harnesses, NOT world assembly (leave unchanged)
- `src/certification/scenarios.py` — certification harnesses (leave unchanged)
- `src/entities/archetype_factory.py` — internal, inside `ArchetypeEntityFactory.build_entity()` (correct, leave unchanged)
- `src/core/builder.py` — the class definition (leave unchanged)

None of these are the world assembly pipeline. No existing call site needs to be changed — this is additive.

## Parity Ledger

No parity entries directly cover `WorldEntitySpawner` — new behavior, add entry to `substrate.yaml` if created.

## Risks

- Minimal: additive code, no existing call sites changed
- `EntityArchetypeResolver.resolve()` may throw if archetype not found → guard with try/except + legacy fallback
- `resolved_archetype_to_contract` requires `stat_profile` and `inventory_profile` to be non-None → ensure archetype is fully resolved before calling
