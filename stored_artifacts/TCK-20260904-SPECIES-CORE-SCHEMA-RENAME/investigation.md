---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME
artifact_type: investigation
tags: [content, schema]
---

# Investigation — TCK-20260904-SPECIES-CORE-SCHEMA-RENAME

## Class rename target

`RaceDefinition` (`src/content/schema.py:134`) renamed to `SpeciesDefinition` — the epic's own
Assumptions/Open Questions flagged this as not finally locked. `species` reads as the natural,
unambiguous target given the rest of the epic's naming (`species_id`, `living/species.yaml`), and
matches every sibling schema's plain-noun convention (`FactionDefinition`, `RoleDefinition`). No
plan-owner sanity check was available mid-session; proceeded with this name as the only reasonable
candidate and recorded the decision here for visibility.

## Real scope vs. the ticket's original file list

The ticket's listed file scope
(`src/content/{schema,resolver,repository,matrix,reference_graph,validator}.py`,
`src/entities/{archetype_factory,contract_builder,identity_resolver}.py`,
`src/worldbuilding/compiler.py`, `data/content/living/races.yaml`) undercounted the real
hard-coupling surface. Confirmed via direct grep, not assumed, that the following consumers also
read the renamed `race_id`/`race` fields and would break at runtime (`AttributeError`/`KeyError`)
if left unfixed:

- `src/entities/runtime_contract.py` — `ResolvedEntityRuntimeContract.race_id`.
- `src/worldassembly/{models,resolver,entity_spawner}.py` — `ResolvedEntityProfile.race_id` and its
  three read/write sites.
- `data/content/entities/entity_archetypes.yaml` — 29 `race:` keys satisfying
  `EntityArchetypeDefinition.race` (now `species`); the YAML itself is content data, not code, but
  the schema/content coupling is unavoidable.

All were fixed in this ticket rather than left for a later child to discover broken.

## Deliberate child-2/3 boundary (verified per-file, not assumed)

`RaceRelationRecord`, `source_race`/`target_race`, `FactionDefinition.common_races`,
`CatalogRepository.race_relations`/`get_race_relationship`, and `data/content/social/
race_relations.yaml` are untouched — confirmed by reading `CatalogValidator._validate_race_relations`
(renamed to `_validate_species_relations` — its body actually validates `SpeciesDefinition`
cross-references, not `RaceRelationRecord`; a misleading pre-existing name, not this ticket's
subsystem) and `src/content_semantics/relation.py`'s race-hostility escalation step, both of which
belong to `TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME`.

Three files conceptually owned by later children (`src/content_semantics/faction.py`'s
`get_race_id_str()`, `src/strategy/role_model_imitation.py`, `src/observability/event_shapers.py`)
read the exact `entity.identity.properties` stored key renamed here. Each got the minimal surgical
fix (only the stored-key string literal), with the surrounding function/variable names and the
observability event's OUTPUT key (`"race_id"`, deliberately kept for now) left untouched and
commented — avoiding both a silent break and scope creep into child 2/3's own naming pass.

## Replay/determinism impact (ticket's own flagged open question — explicitly checked)

`src/engine/checkpoint.py`'s `CanonicalStateHasher`/`ReplayManager` and `src/engine/
scenario_checkpoint.py` were grepped for `race`/`race_id` — zero hits. Checkpointing hashes
`entity.to_canonical_dict()` generically; no field name is hardcoded into the hash logic. Renaming a
key inside `identity.properties` does not break the hashing mechanism itself.

Confirmed empirically after regenerating all 21 `data/worlds/*/resolved/*` artifacts (see below):
per-world `state_hash` (the LIGHT hash — tick/seed/entity_count/region_count only) is byte-identical
before and after the rename in every world; `canonical_state_hash` (the FULL hash, which includes
`identity.properties`) changed in every world, exactly as expected for a real content-field rename.
`entity_count`/`quest_count`/`distinct_populated_factions`/`place_count`/warnings are identical across
all 21 worlds — confirming the regeneration is isolated to the renamed field, no other content
drifted. `data/runs/*` recorded run logs (ephemeral, cleaned per this ticket's own close per the
standard workflow) and `tests/tools/fixtures/kgmcp_phase5_*` (KGMCP tooling snapshots, unrelated
subsystem) also matched on `race_id` in the initial grep but are not durable replay fixtures this
rename could break.

## World regeneration

`data/worlds/*/resolved/{compile_context,assembly_report,provenance_manifest,validation_report}.json`
and `data/worlds/*/world_compile_report.json` (21 worlds) regenerated via `python3 -m
src.worldbuilding.cli resolve <world_id>` + `compile <world_id> --seed <original_seed>` (per-world
original seed preserved from each world's prior `world_compile_report.json`, not the CLI's `--seed 42`
default, to avoid an unintended spawn-layout change). No dedicated batch/`--all` tool exists in this
repo; same ad-hoc per-world loop pattern as `TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT` used for
its own prior schema-rename batch regen (idea 66 precedent, confirmed via search).
