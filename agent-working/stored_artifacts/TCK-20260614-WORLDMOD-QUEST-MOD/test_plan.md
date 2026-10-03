---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-MOD
artifact_type: test_plan
tags: [worldmodules, quest, assembly, merge]
---

# Test Plan — TCK-20260614-WORLDMOD-QUEST-MOD

## Unit Tests (tests/unit/worldassembly/test_quest_merge.py)

1. **test_single_module_quest_definitions** — A module with one QuestDefinition compiles into WorldSpec.quest_definitions with source_module set to the module's module_id.

2. **test_collision_raises_assembly_error** — Two modules contributing a quest with the same `id` raise `AssemblyCollisionError` naming both contributing module IDs.

3. **test_empty_quest_definitions_no_error** — A module with no quest_definitions (empty list default) assembles without error and output has empty quest_definitions.

4. **test_source_module_matches_contributing_module** — source_module on the returned QuestDefinition exactly matches the contributing module's module_id.

## Scope
- All tests use minimal stubs (no YAML fixture loading).
- Tests mock CatalogRepository, WorldModuleRepository, and resolvers to isolate assembly logic.
