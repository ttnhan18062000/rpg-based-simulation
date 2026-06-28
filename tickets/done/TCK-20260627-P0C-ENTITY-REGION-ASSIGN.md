---
status: historical
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260627-P0C-ENTITY-REGION-ASSIGN
phase: done
date: 2026-06-27
tags: [p0, region-id, entity-factory, world-compiler, blocker]
---

# TCK-20260627-P0C-ENTITY-REGION-ASSIGN

## Title
Fix `WorldCompiler`/`EntityFactory` to assign `navigation.region_id` at world assembly

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
All 30 entities in urban_political have `navigation.region_id = None` after `WorldCompiler.compile()`. `ResourceOpportunityProvider` uses `region_id` for node matching — even with P0-B's resource nodes added, region-based filtering fails for every entity. The assignment of `region_id` from spawn location to entity navigation state is missing from the world assembly pipeline.

## Scope
- Identify where in `WorldCompiler` (or the `ArchetypeEntityFactory` / `WorldEntitySpawner` path) entity spawn location is resolved.
- Fix that path to write `navigation.region_id` based on the entity's spawn region at compile/assembly time.
- Add post-compile assertion: `all(e.navigation.region_id is not None for e in state.entities.values())`.

## Out of Scope
- Runtime region migration (entities moving between regions during ticks) — that is handled separately.
- Changes to resource node definitions (P0-B).
- Adventure routing flag policy (P0-A).

## Acceptance Criteria
- [ ] After `WorldCompiler.compile()` for urban_political, every entity has `navigation.region_id is not None`.
- [ ] `make world-compile WORLD=urban_political` succeeds.
- [ ] Unit or integration test asserts: `all(e.navigation.region_id is not None for e in state.entities.values())` on a compiled world.
- [ ] Existing world assembly tests pass.

## Related Tickets
- TCK-20260627-P0A-ADVENTURE-FLAG (same blocker group)
- TCK-20260627-P0B-URBAN-RESOURCE-NODES (same blocker group)

## Related Docs
- `docs/audits/D04_balance_tuning.md` §6.3
- `docs/world/compiler_contract.md`
- `docs/world/assembly_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12A-BALANCE-MEASURE/` — documented `region_id = None` for all entities
- `stored_artifacts/TCK-20260609-ARCHETYPE-ENTITY-FACTORY/` — ArchetypeEntityFactory implementation

## Related Code Areas
- `src/engine/worldcompiler.py` (or wherever `WorldCompiler.compile()` lives)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner` — likely spawn context is resolved here)
- `src/core/models/navigation.py` (or wherever `NavigationComponent.region_id` is defined)
- `src/content/resolver.py` (archetype + population resolution)

## Assumptions / Open Questions
- The spawn location → region mapping should be available at assembly time through the world's region topology (hometown/bandit_road/trading_hometown).
- Preferred spawn regions may be defined in the archetype or population spec — check `WorldEntitySpawner` and `PopulationRecipeResolver`.

## Implementation Notes
- Root cause found in `src/worldbuilding/compiler.py` L315-337: `V2EntityBuilder` chain had `region_id = pop_spec.spawn_region` in scope (L254) but never called `.navigation(region_id=region_id)`. Fixed by adding that call after `.location(float(x), float(y))`.
- `WorldEntitySpawner` (entity_spawner.py) is a SEPARATE pipeline not used by `make world-compile`. It has a latent related bug but is out of scope.
- Fix is one additive line; deterministic, no RNG, no schema changes required.

## Test Summary
- New test: compile urban_political, assert all entities have non-None `navigation.region_id`.
- Regression: `pytest tests/ -k "world" -m "not slow"`.

## Files Changed
- `src/worldbuilding/compiler.py` — added `.navigation(region_id=region_id)` to V2EntityBuilder chain at L319
- `tests/integration/worldassembly/test_e2e_smoke.py` — new test `test_urban_political_all_entities_have_region_id`
- `docs/parity_ledger/substrate.yaml` — updated SUB-087 with test_path and v2_evidence

## Completion Summary
Added `.navigation(region_id=region_id)` to the `V2EntityBuilder` chain in `WorldCompiler.compile()` (compiler.py L319). Root cause was that `region_id = pop_spec.spawn_region` was in scope but never assigned to `NavigationComponent`. All 30 urban_political entities now have non-None `navigation.region_id` after compile. New integration test `test_urban_political_all_entities_have_region_id` asserts the postcondition. 8/8 targeted tests GREEN; 641 world-scoped regression tests passed. Parity ledger SUB-087 updated with proper test_path.
