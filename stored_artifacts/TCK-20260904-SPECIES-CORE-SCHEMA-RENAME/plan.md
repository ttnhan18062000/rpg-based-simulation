---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME
artifact_type: plan
tags: [content, schema]
---

# Plan — TCK-20260904-SPECIES-CORE-SCHEMA-RENAME

1. `src/content/schema.py`: `RaceDefinition` → `SpeciesDefinition`; `EntityArchetypeDefinition.race`
   → `species`; leave `RaceRelationRecord`/`source_race`/`target_race` untouched (child 2), only
   correct its docstring's dangling `RaceDefinition` reference.
2. `data/content/entities/entity_archetypes.yaml`: rename all 29 `race:` keys to `species:` (schema/
   content coupling — the renamed Pydantic field requires it).
3. `src/content/{repository,matrix,reference_graph,validator,resolver}.py`: rename every
   `race`/`race_id`/`races`/`get_race`/`_validate_race_relations` (misleadingly named, actually
   validates `SpeciesDefinition`) symbol to its `species` equivalent; leave `race_relations`/
   `RaceRelationRecord` consumers untouched.
4. `data/content/living/races.yaml` → `species.yaml` (`git mv`), update every path reference
   (`matrix.py`, `tools/generate_content_inventory.py`).
5. `src/entities/{identity_resolver,contract_builder,archetype_factory,runtime_contract}.py` and
   `src/worldbuilding/compiler.py`: rename `race_id` fields/params (the last two are hard-coupling
   discoveries beyond the ticket's original file list — the field flows through them).
6. `src/worldassembly/{models,resolver,entity_spawner}.py`: same `race_id` → `species_id` rename
   (hard-coupling discovery — `ResolvedEntityProfile.race_id` is downstream of the same chain).
7. Minimal surgical stored-key fix (not a full rename) in the 3 files owned by child 2/3 that read
   `entity.identity.properties["race_id"]`: `content_semantics/faction.py`'s `get_race_id_str()`,
   `strategy/role_model_imitation.py`, `observability/event_shapers.py` (its OUTPUT key stays
   `"race_id"` — deferred to child 3).
8. Fix every test file touching the renamed schema/fields (full list in test_plan.md).
9. Regenerate `data/worlds/*/resolved/*` for all 21 worlds (`resolve` + `compile --seed
   <original_seed>` per world), verifying isolation via `state_hash`/`canonical_state_hash`/
   entity-count diff.
10. Explicitly verify the ticket's own flagged replay/determinism open question rather than assuming
    it's safe (see investigation.md).
11. Parity ledger entry recording the schema rename.
