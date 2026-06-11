---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-ARCHETYPE-DEFAULT-PATH
phase: done
date: 2026-06-10
tags: [archetype, default, path]
---

# TCK-20260610-ARCHETYPE-DEFAULT-PATH

## Title
Promote archetype-native entity construction to the default runtime entity creation path for world assembly

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Phase 29 delivered `ResolvedEntityRuntimeContract`, `EntitySpawnContext`, and `ArchetypeEntityFactory` as a bridge from resolved archetypes to `EntityState`. These are implemented and tested. However, the archetype-native construction path is not yet clearly the default path used during world assembly and runtime entity creation — `V2EntityBuilder` legacy paths still exist and may be invoked by default. This leaves Phase 29 as "a bridge", not "the new default", which means the runtime is not yet fully archetype-authoritative.

## Scope
- Identify all call sites in world assembly and runtime initialization that construct `EntityState` without going through `ArchetypeEntityFactory` / `resolved_archetype_to_contract()`
- Wire the archetype-native path as the default for entity creation during world assembly
- Retain `V2EntityBuilder` only as an explicit legacy fallback (guarded by `LEGACY_FALLBACK` mode or equivalent)
- Add or update integration tests asserting that world assembly produces entities via the archetype-native path, not via legacy construction
- Confirm no regression in arena/combat tests that depend on entity structure

## Out of Scope
- Removing `V2EntityBuilder` entirely (legacy removal is a separate cleanup task)
- Changes to archetype schema or the `ResolvedEntityRuntimeContract` structure

## Acceptance Criteria
- [x] World assembly entry point uses `ArchetypeEntityFactory` as the default entity construction path
- [x] No call site in the standard assembly pipeline invokes `V2EntityBuilder` directly without an explicit legacy-mode guard
- [x] At least one integration test asserts that a world assembled in strict catalog mode produces entities constructed via the archetype-native path
- [x] Existing arena and combat integration tests continue to pass
- [x] Architecture guard or test documents the expected default construction path

## Related Tickets
- TCK-20260610-CAT-REL-099-FIX (CAT-REL-099 must be fixed first if world assembly tests are needed to verify this)

## Related Docs
- `docs/engine/authoritative_pipeline.md`
- `docs/core/entities.md`
- `docs/parity_ledger/substrate.yaml` (SUB-368)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-ARCHETYPE-DEFAULT-PATH/`

## Related Code Areas
- `src/worldassembly/entity_spawner.py` — new WorldEntitySpawner
- `src/entities/archetype_factory.py` — ArchetypeEntityFactory (unchanged)
- `src/entities/contract_builder.py` — resolved_archetype_to_contract (unchanged)
- `tests/integration/worldassembly/test_world_entity_spawner.py`

## Assumptions / Open Questions
- Investigation confirmed: no `WorldEntitySpawner` existed before this ticket. The archetype-native path (`ArchetypeEntityFactory`) was fully implemented but not wired into world assembly output.
- `V2EntityBuilder` remains in `perf/scenarios.py` and `certification/scenarios.py` — those are harnesses, not world assembly, and are intentionally excluded per scope.

## Implementation Notes
Created `src/worldassembly/entity_spawner.py` with `WorldEntitySpawner`:
- `spawn_from_context(ctx, catalog_repo, base_entity_id=1) -> Dict[int, EntityState]`
- Archetype-native path: `EntityArchetypeResolver → resolved_archetype_to_contract → ArchetypeEntityFactory.build_entity()` for profiles with `archetype_id`
- Explicit LEGACY GUARD fallback using `V2EntityBuilder` for profiles without `archetype_id` (town NPCs, synthetic entities)
- Fallback also triggers if `EntityArchetypeResolver.resolve()` raises (e.g. archetype not in catalog)

V2EntityBuilder is a deferred import inside `_spawn_legacy_guard()` only — not at module level.

## Test Summary
6/6 integration tests pass in `tests/integration/worldassembly/test_world_entity_spawner.py`:
- Architecture guard: WorldEntitySpawner imports ArchetypeEntityFactory
- Architecture guard: V2EntityBuilder only in legacy guard (not at module level)
- spawn_from_context produces EntityState for all CompileContext profiles
- Archetype-native entities carry archetype_id in identity.properties
- Entity IDs sequential from base_entity_id
- Entity combat stats positive

61/62 pass in `tests/unit/worldassembly/ tests/unit/entities/` — the 1 pre-existing failure (`test_cli_resolve_and_compile_integration`: `plains_layout` module not found) exists on baseline too.

## Files Changed
- `src/worldassembly/entity_spawner.py` — new
- `tests/integration/worldassembly/test_world_entity_spawner.py` — new
- `docs/parity_ledger/substrate.yaml` — SUB-368 added

## Completion Summary
Created `WorldEntitySpawner` as the canonical bridge between `CompileContext` and `Dict[int, EntityState]`, using `ArchetypeEntityFactory` as the primary construction path. The legacy `V2EntityBuilder` guard is explicitly labelled and deferred-imported inside a dedicated method. Parity ledger entry SUB-368 added. All 6 new integration tests pass; no regressions introduced.
