---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY

## Context search (mandatory step)
`search_docs` for "ArchetypeEntityFactory WorldEntitySpawner CatalogScenarioStateBuilder
personality seed" surfaced `docs/world/assembly_contract.md` (real, authoritative, P0,
`last_verified: 2026-06-16`) — the real, current contract for this exact subsystem. It states:
**"Determinism: Given the same `CompileContext` and `base_entity_id`, `spawn_from_context`
produces bit-identical `EntityState` objects. No randomness is introduced during spawning."**
This is a real, documented architectural property this ticket's own fix will change — flagged and
corrected in Document-Update, not silently invalidated.

Also surfaced `docs/audits/D05_entity_differentiation.md`'s own "Recommended Follow-Up" section
(the same audit that originally caught `WorldCompiler.compile()`'s all-zero-personality bug, fixed
by `TCK-20260619-P0-ENTITY-INIT`) — confirms this is the same class of finding, just for a
different, newer construction path that audit never covered.

## A seed already exists at the right layer — not from scratch
`CatalogScenarioStateBuilder.build()` (`src/scenarios/catalog_state_builder.py`) already accepts
`seed: int = 42` — but currently only passes it to the final `AuthoritativeState(tick=0,
seed=seed, entities=entities)` construction, **never to `spawn_from_context()` itself**. The real
fix is threading this already-existing seed down through 3 layers, not inventing a new one:
`CatalogScenarioStateBuilder.build()` → `WorldEntitySpawner.spawn_from_context()` →
`ArchetypeEntityFactory.build_entity()` (archetype-native path) and the legacy-guard path
(`_spawn_legacy_guard()`, same file).

## Architecture check: avoid a backward dependency
Reusing `get_bravery_bias()`/`get_action_style_for_bravery()`/`_load_personality_bias_config()`
(added to `src/worldbuilding/compiler.py` this session, `TCK-20260809-COMBAT-PERSONALITY-RACE-
CORRELATION`/`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`) directly from `src/entities/
archetype_factory.py` would create a new dependency edge from `src/entities/` (used by both
`worldbuilding` and `worldassembly` paths) onto a specific `worldbuilding` compiler module —
architecturally backward. Confirmed via grep that `src/content_semantics/` is this repo's own
real, established precedent for exactly this kind of cross-cutting semantic helper, already
imported by both `worldbuilding` (`compiler.py`) and `worldassembly` (`resolver.py`) and `engine`
(`legality.py`, `tactical.py`, `combat_rewards.py`, etc.). **Real fix**: extract the 3 personality-
bias helper functions out of `compiler.py` into a new `src/content_semantics/personality.py`
module (pure move, no behavior change to `compiler.py`'s own existing, already-verified
callers), and have both `compiler.py` and `archetype_factory.py` import from there.

## Real constraint: `ArchetypeEntityFactory` must not import `CatalogRepository`
`tests/unit/entities/test_archetype_entity_factory.py::test_factory_does_not_import_catalog_repository`
is a real, existing architecture guard test (AST-walks `archetype_factory.py`'s own source,
fails if `CatalogRepository` appears anywhere). Confirmed safe: `get_faction_semantics_service()`
(the function `get_bravery_bias()` calls) does its own `CatalogRepository` import lazily, inside
its own function body (`src/content_semantics/faction.py`) — not at `archetype_factory.py`'s
import level. Importing `from src.content_semantics.personality import get_bravery_bias, ...` at
module level in `archetype_factory.py` does not itself reference `CatalogRepository` anywhere in
that file's own source text, so the guard test's AST walk still passes.

## Real backward-compatibility constraint on `build_entity()`'s own signature
12 existing tests in `tests/unit/entities/test_archetype_entity_factory.py` call
`FACTORY.build_entity(entity_id, contract, spawn)` positionally, with no seed argument. A new
`seed` parameter must default (chosen: `42`, matching `CatalogScenarioStateBuilder.build()`'s own
existing default exactly) to avoid breaking any of them. Confirmed via grep: no test anywhere in
the affected surface (`test_entity_identity_resolver.py`, `test_entity_construction_bridge.py`,
`test_catalog_scenario_state_builder.py`, `test_catalog_vs_legacy_scenario_semantics.py`,
`test_catalog_arena_smoke.py`) references `personality`/`bravery` at all — nothing asserts the
previous all-zero state, so adding real values breaks nothing.

## Docs Requiring Update
- `docs/world/assembly_contract.md`: its own "Determinism" claim under "Entity Spawner Contract"
  ("No randomness is introduced during spawning") becomes false once `spawn_from_context()` gains
  a real, seed-driven personality-generation step — corrected to describe the new real, still-
  fully-deterministic-given-seed behavior, not silently left stale.
