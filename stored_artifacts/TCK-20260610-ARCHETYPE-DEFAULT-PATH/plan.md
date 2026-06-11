---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-ARCHETYPE-DEFAULT-PATH
artifact_type: plan
tags: [archetype, default, path]
---

# Plan — TCK-20260610-ARCHETYPE-DEFAULT-PATH

## Ordered Steps

### Step 1 — Create `src/worldassembly/entity_spawner.py`
New file with `WorldEntitySpawner` class:
- Method: `spawn_from_context(ctx, catalog_repo, base_entity_id=1) -> Dict[int, EntityState]`
- Archetype-native path (when profile.archetype_id is set): EntityArchetypeResolver → resolved_archetype_to_contract → ArchetypeEntityFactory.build_entity()
- Legacy guard (when profile.archetype_id is None): V2EntityBuilder with explicit "legacy path" comment

### Step 2 — Add integration test
File: `tests/integration/worldassembly/test_world_entity_spawner.py`
- Assemble a world via WorldAssemblyResolver (using real catalog + modules)
- Call WorldEntitySpawner.spawn_from_context() on the result
- Assert: entities produced, archetype-native entities have archetype_id in identity.properties
- Assert: V2EntityBuilder is NOT imported inside WorldEntitySpawner except in the legacy guard

### Step 3 — Add architecture guard test
In the same test file or separate:
- Assert WorldEntitySpawner exists and imports ArchetypeEntityFactory (not a CatalogRepository import inside archetype_factory.py — it must stay catalog-free)

### Step 4 — Run tests to confirm

## Scope Guards

- Do NOT modify `ProfileResolver`, `WorldAssemblyResolver`, or existing call sites
- Do NOT add `WorldEntitySpawner` to the world assembly pipeline itself (additive only — existing code keeps working)
- Do NOT modify `perf/scenarios.py` or `certification/scenarios.py`
- The legacy V2EntityBuilder path in `WorldEntitySpawner` must be explicitly commented as a guard

## Dependency Map

Step 1 → Step 2 → Step 3 → Step 4 (sequential)

## Acceptance Criteria Mapped

- AC1 (WorldEntitySpawner uses ArchetypeEntityFactory): Step 1
- AC2 (no V2EntityBuilder without guard): Step 1 (guard is explicit in the legacy branch)
- AC3 (integration test via archetype-native path): Step 2
- AC4 (arena/combat tests continue passing): Step 4 (these don't touch the spawner)
- AC5 (architecture guard): Step 3

## Deviations
<!-- Fill if any step changes -->
