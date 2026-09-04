---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY
artifact_type: plan
tags: [content, schema]
---

# Plan — TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY

Scope-only epic. No implementation happens here (explicit user instruction). The plan is to split the
confirmed real scope (see investigation.md) into 4 sequenced child tickets along natural subsystem
boundaries, so a future implementation session can pick each one up independently and verifiably:

1. **`TCK-20260904-SPECIES-CORE-SCHEMA-RENAME`** — the base schema/entity plumbing:
   `RaceDefinition` -> a species-named class, `race_id` -> `species_id`, across
   `src/content/{schema,resolver,repository,matrix,reference_graph,validator}.py`,
   `src/entities/{archetype_factory,contract_builder,identity_resolver}.py`,
   `src/worldbuilding/compiler.py`, and `data/content/living/races.yaml` -> `species.yaml`. No
   dependents (this is the foundation every other child ticket's rename builds on).
2. **`TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME`** — idea 37's own subsystem:
   `race_relations.yaml` -> `species_relations.yaml`, `src/content_semantics/{faction,relation}.py`,
   `src/engine/tactical.py`, `src/world/{perception/gate,motivation/pressure_resolver}.py`,
   `src/strategy/role_model_imitation.py`, plus the 6 dedicated race-relations test files. Depends on
   child 1 (reads `race_id`/the base catalog).
3. **`TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME`** — remaining code consumers not covered by
   1/2: `src/engine/{kernel,cognition,replay_manager}.py`, `src/observability/*`,
   `src/quests/generator.py`, `src/api/ws/stream.py`, `src/world/environment.py`,
   `src/content_semantics/personality.py`, remaining content data
   (`entity_archetypes.yaml`, `factions.yaml`, `personality_bias.yaml`), remaining test files. Depends
   on child 1.
4. **`TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP`** — `docs/mechanics/*.md` (5 files),
   `docs/parity_ledger/*.yaml` (7 shards, prose only — entry IDs checked, not assumed renameable),
   remaining real terminology hits across `docs/`. Depends on children 1-3 landing first, so doc
   updates cite the real final names rather than guessing ahead of the code.

Each child ticket is standard-tier (touches real code/content/tests) and gets its own full staging
artifacts (investigation/plan/test_plan) when picked up for implementation — not created now, since
this epic only scopes and does not implement.
