# Test Plan — TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE

## Updated tests (encoded the old bug as expected behavior)
- `test_spawn_from_context_produces_entity_states` — now asserts `len(entities) ==
  sum(profile.count for profile in ctx.entities.values())`, and requires the real corpus fixture
  to have at least one population with `count > 1` (so the assertion actually exercises expansion,
  not a vacuously-true 1:1 case).
- `test_archetype_native_entities_carry_archetype_id` — now groups spawned entities by their
  `population_id` tag (the correct way to map entities back to their source profile once one
  profile can expand into many), asserting both the right count per population and the right
  `archetype_id` on every individual, not just one.
- `test_entity_ids_start_from_base` — now asserts the ID range spans `sum(profile.count)`
  individuals, not `len(ctx.entities)` profiles.

## Regression suites
- `pytest tests/integration/worldassembly/ tests/unit/worldassembly/test_resolver.py -q` — full
  targeted suite for the two modified modules' own direct test coverage.
- `pytest tests/integration/worldassembly/ tests/unit/entities/ tests/integration/entities/
  tests/unit/worldassembly/test_corpus_diversity.py -q` — broader sweep to catch any consumer
  depending on the old 1-entity-per-population behavior; the corpus_diversity failures found here
  were triaged via `git stash` against clean `main` (see Implementation Notes) and confirmed
  pre-existing, not caused by this change.

## Real-corpus verification (not required as an automated test, but confirms the fix has real
effect)
- `frontier_living_world`'s own compile via `WorldAssemblyResolver`/`WorldEntitySpawner` (the
  catalog pipeline this ticket fixes) now spawns `sum(PopulationSpec.count)` entities instead of
  one per population group — the exact gap
  `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s own blocking dependency names.

## Acceptance criteria mapping
- Intentional-vs-accidental determination → Implementation Notes' evidence chain (field docstring,
  Mechanics Bible, classic-pipeline comparison).
- Real fix + test coverage showing declared/spawned counts reconcile → the 3 updated
  `test_world_entity_spawner.py` tests above, asserting `sum(profile.count)` directly.
- No regression in the named suites → Test Summary; all pre-existing failures individually
  confirmed unrelated via `git stash`, not silently assumed unrelated.
